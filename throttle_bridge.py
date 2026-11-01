#!/usr/bin/env python3

import argparse
import math
import time

import rospy
from gazebo_msgs.msg import ModelStates
from std_msgs.msg import Bool

from pymavlink import mavutil

from gazebo_msgs.srv import (
    ApplyBodyWrench,
    ApplyBodyWrenchRequest
)


parser = argparse.ArgumentParser()

parser.add_argument(
    "--model",
    required=True
)

parser.add_argument(
    "--port",
    type=int,
    required=True
)

parser.add_argument(
    "--max-thrust",
    type=float,
    default=3.0
)

parser.add_argument(
    "--pace-model",
    default=None,
    help="Fixed-gas target aircraft used as distance reference for own UAV."
)
parser.add_argument("--desired-gap", type=float, default=25.0)
parser.add_argument("--lateral-limit", type=float, default=30.0)
parser.add_argument("--min-own-speed", type=float, default=15.0)
parser.add_argument("--max-own-speed", type=float, default=24.0)
parser.add_argument("--max-thrust-increase", type=float, default=0.50)
parser.add_argument("--max-thrust-reduction", type=float, default=0.25)

args = parser.parse_args()


PWM_MIN = 1000
PWM_MAX = 2000


def pwm_to_thrust(
    pwm
):

    pwm = max(
        PWM_MIN,
        min(
            PWM_MAX,
            pwm
        )
    )

    throttle = (
        pwm - PWM_MIN
    ) / float(
        PWM_MAX - PWM_MIN
    )

    return (
        throttle
        * args.max_thrust
    )



def clamp(value, low, high):
    return max(low, min(high, value))


class OwnshipGapController:


    def __init__(self, own_model, lead_model, desired_gap, lateral_limit,
                 min_speed, max_speed, max_increase, max_reduction, max_thrust):
        if own_model == lead_model:
            raise ValueError("Ownship and lead model names must differ")
        if not (desired_gap > 0 and lateral_limit > 0):
            raise ValueError("Gap and lateral limit must be positive")
        if not (0 < min_speed < max_speed):
            raise ValueError("Require 0 < min-own-speed < max-own-speed")
        if not (0 <= max_increase <= max_thrust and 0 <= max_reduction <= max_thrust):
            raise ValueError("Invalid force bounds")
        self.own_model = own_model
        self.lead_model = lead_model
        self.desired_gap = desired_gap
        self.lateral_limit = lateral_limit
        self.min_speed = min_speed
        self.max_speed = max_speed
        self.max_increase = max_increase
        self.max_reduction = max_reduction
        self.max_thrust = max_thrust
        self.enabled = False
        self.state = None
        self.adjustment = 0.0
        self.last_step = time.monotonic()
        self.last_gap = None
        self.last_lateral = None
        self.last_rel_speed = None
        self.status = "STANDBY"
        rospy.Subscriber("/tracking/enabled", Bool, self.on_enabled, queue_size=1)
        rospy.Subscriber("/gazebo/model_states", ModelStates, self.on_states, queue_size=1)

    def on_enabled(self, msg):
        self.enabled = bool(msg.data)
        if not self.enabled:
            self.adjustment = 0.0

    def on_states(self, msg):
        try:
            a = msg.name.index(self.own_model)
            b = msg.name.index(self.lead_model)
            ap, av = msg.pose[a].position, msg.twist[a].linear
            bp, bv = msg.pose[b].position, msg.twist[b].linear
            values = (
                float(ap.x), float(ap.y), float(ap.z),
                float(av.x), float(av.y),
                float(bp.x), float(bp.y), float(bp.z),
                float(bv.x), float(bv.y)
            )
            self.state = ((time.monotonic(),) + values) if all(
                math.isfinite(value) for value in values
            ) else None
        except (AttributeError, IndexError, TypeError, ValueError):
            self.state = None

    def apply(self, base_thrust):
        now = time.monotonic()
        dt = clamp(now - self.last_step, 0.0, 0.20)
        self.last_step = now
        self.last_gap = None
        self.last_lateral = None
        self.last_rel_speed = None
        self.status = "STANDBY"

        state = self.state
        if not self.enabled or state is None or now - state[0] > 0.75:
            self.adjustment = 0.0
            return base_thrust

        (_, ax, ay, az, avx, avy, bx, by, bz, bvx, bvy) = state
        speed = math.hypot(avx, avy)
        if az < 3.0 or bz < 3.0 or speed < 5.0:
            self.adjustment = 0.0
            self.status = "ALTITUDE / SPEED GUARD"
            return base_thrust


        ux, uy = avx / speed, avy / speed
        dx, dy = bx - ax, by - ay
        ahead = dx * ux + dy * uy
        lateral = abs(dx * uy - dy * ux)
        rel_speed = bvx * ux + bvy * uy - speed
        self.last_gap, self.last_lateral = ahead, lateral
        self.last_rel_speed = rel_speed


        if ahead <= 0.0 or lateral > self.lateral_limit:
            self.adjustment = 0.0
            self.status = "OUT OF CORRIDOR"
            return base_thrust

        error = ahead - self.desired_gap
        if abs(error) < 3.0 and abs(rel_speed) < 0.6:
            requested = 0.0
        else:
            requested = 0.018 * error + 0.060 * rel_speed
        requested = clamp(requested, -self.max_reduction, self.max_increase)

        if speed < self.min_speed:
            requested = max(0.0, requested)

        if speed > self.max_speed:
            requested = min(0.0, requested)

        requested = clamp(requested, -base_thrust,
                          self.max_thrust - base_thrust)

        max_change = 0.22 * dt
        self.adjustment += clamp(
            requested - self.adjustment, -max_change, max_change
        )
        self.adjustment = clamp(
            self.adjustment, -base_thrust, self.max_thrust - base_thrust
        )
        self.status = "FOLLOWING"
        return clamp(base_thrust + self.adjustment, 0.0, self.max_thrust)


def main():

    rospy.init_node(
        f"{args.model}_throttle_bridge",
        anonymous=True
    )

    rospy.wait_for_service(
        "/gazebo/apply_body_wrench"
    )

    apply_wrench = (
        rospy.ServiceProxy(
            "/gazebo/apply_body_wrench",
            ApplyBodyWrench
        )
    )

    mav = (
        mavutil.mavlink_connection(
            f"udpin:0.0.0.0:{args.port}"
        )
    )

    armed = False
    servo3 = 1000

    body = (
        f"{args.model}::base_link"
    )

    follower = None
    if args.pace_model:
        follower = OwnshipGapController(
            own_model=args.model,
            lead_model=args.pace_model,
            desired_gap=args.desired_gap,
            lateral_limit=args.lateral_limit,
            min_speed=args.min_own_speed,
            max_speed=args.max_own_speed,
            max_increase=args.max_thrust_increase,
            max_reduction=args.max_thrust_reduction,
            max_thrust=args.max_thrust
        )

    last_print = 0

    print(
        f"{args.model} throttle bridge hazir "
        f"(UDP {args.port})"
    )

    while not rospy.is_shutdown():

        while True:

            msg = mav.recv_match(
                blocking=False
            )

            if msg is None:
                break

            msg_type = (
                msg.get_type()
            )

            if (
                msg_type
                == "HEARTBEAT"
            ):

                armed = bool(
                    msg.base_mode
                    &
                    mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED
                )

            elif (
                msg_type
                == "SERVO_OUTPUT_RAW"
            ):

                value = int(
                    getattr(
                        msg,
                        "servo3_raw",
                        1000
                    )
                )

                if value > 0:
                    servo3 = value

        if armed:

            thrust = (
                pwm_to_thrust(
                    servo3
                )
            )

        else:

            thrust = 0.0

        if follower is not None and armed:
            thrust = follower.apply(thrust)

        if thrust > 0.001:

            request = (
                ApplyBodyWrenchRequest()
            )

            request.body_name = (
                body
            )

            request.reference_frame = (
                body
            )

            request.wrench.force.x = (
                thrust
            )

            request.wrench.force.y = 0
            request.wrench.force.z = 0

            request.start_time = (
                rospy.Time(0)
            )

            request.duration = (
                rospy.Duration.from_sec(
                    0.035
                )
            )

            try:

                apply_wrench(
                    request
                )

            except rospy.ServiceException:

                pass

        now = time.time()

        if (
            now - last_print
            >= 1
        ):

            print(
                f"{args.model} | "
                f"{'ARMED' if armed else 'DISARMED'} | "
                f"SERVO3={servo3} | "
                f"THRUST={thrust:.2f} N"
            )

            if follower is not None:
                if follower.last_gap is None:
                    print(f"  GAP CONTROL: {follower.status}")
                else:
                    print(
                        f"  GAP CONTROL: ahead={follower.last_gap:.1f}m | "
                        f"lateral={follower.last_lateral:.1f}m | "
                        f"relative={follower.last_rel_speed:+.1f}m/s | "
                        f"adjust={follower.adjustment:+.2f}N | "
                        f"{follower.status}"
                    )

            last_print = now

        time.sleep(
            1 / 30.0
        )


if __name__ == "__main__":
    main()