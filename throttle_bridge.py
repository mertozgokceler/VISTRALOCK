#!/usr/bin/env python3

import argparse
import time

import rospy

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

            last_print = now

        time.sleep(
            1 / 30.0
        )


if __name__ == "__main__":
    main()