#!/usr/bin/env python3
import argparse
import math
import subprocess
import time
import rospy
from gazebo_msgs.msg import ModelState
from gazebo_msgs.srv import (
    GetModelState,
    SetModelState
)
from tf.transformations import (
    euler_from_quaternion
)
parser = argparse.ArgumentParser()
parser.add_argument(
    "--model",
    required=True
)
parser.add_argument(
    "--window",
    required=True
)
parser.add_argument(
    "--y",
    type=float,
    required=True
)
parser.add_argument(
    "--x",
    type=float,
    default=-130.0
)
args = parser.parse_args()
RUNWAY_Z = 0.26
TAKEOFF_THROTTLE = 1900
FLIGHT_THROTTLE = 1800
AIRBORNE = False
def mavproxy(
    command,
    wait=0.15
):
    print(
        f"[{args.model}] "
        f"MAVProxy -> {command}"
    )
    subprocess.run(
        [
            "tmux",
            "send-keys",
            "-t",
            f"talon:{args.window}",
            command,
            "C-m"
        ],
        check=True
    )
    time.sleep(
        wait
    )


def set_plane(
    service,
    x,
    y,
    z,
    vx=0.0,
    vy=0.0,
    vz=0.0
):
    state = ModelState()
    state.model_name = (
        args.model
    )
    state.pose.position.x = x
    state.pose.position.y = y
    state.pose.position.z = z
    state.pose.orientation.x = 0.0
    state.pose.orientation.y = 0.0
    state.pose.orientation.z = 0.0
    state.pose.orientation.w = 1.0
    state.twist.linear.x = vx
    state.twist.linear.y = vy
    state.twist.linear.z = vz
    state.twist.angular.x = 0.0
    state.twist.angular.y = 0.0
    state.twist.angular.z = 0.0
    state.reference_frame = (
        "world"
    )
    result = service(
        state
    )
    if not result.success:
        raise RuntimeError(
            result.status_message
        )


def read_state(
    service
):
    result = service(
        args.model,
        "world"
    )
    if not result.success:
        raise RuntimeError(
            result.status_message
        )
    vx = (
        result.twist.linear.x
    )
    vy = (
        result.twist.linear.y
    )
    vz = (
        result.twist.linear.z
    )
    speed = math.sqrt(
        vx * vx
        + vy * vy
        + vz * vz
    )
    quaternion = (
        result.pose.orientation
    )
    roll, pitch, yaw = (
        euler_from_quaternion(
            [
                quaternion.x,
                quaternion.y,
                quaternion.z,
                quaternion.w
            ]
        )
    )
    return {
        "x": result.pose.position.x,
        "y": result.pose.position.y,
        "z": result.pose.position.z,
        "speed": speed,
        "vz": vz,
        "roll": math.degrees(roll),
        "pitch": math.degrees(pitch),
        "yaw": math.degrees(yaw)
    }
def show(
    state,
    phase
):
    print(
        f"[{args.model}] "
        f"{phase:<8} "
        f"x={state['x']:7.1f} "
        f"y={state['y']:7.1f} "
        f"z={state['z']:6.2f}m "
        f"V={state['speed']:5.2f}m/s "
        f"Vz={state['vz']:6.2f} "
        f"roll={state['roll']:6.1f} "
        f"pitch={state['pitch']:6.1f}"
    )


def abort():
    mavproxy("rc 1 1500")
    mavproxy("rc 2 1500")
    mavproxy("rc 4 1500")
    # Gazebo'da havadayken ariza sonrasi motoru kesme.
    # Yerdeyken guvenli gaz komutunu koru.
    throttle = FLIGHT_THROTTLE if AIRBORNE else 1000
    mavproxy(f"rc 3 {throttle}")
def runway_takeoff(
    set_state,
    get_state
):
    global AIRBORNE
    AIRBORNE = False
    print()
    print(
        "=========================================="
    )
    print(
        f"[{args.model}] PIST KALKISI"
    )
    print(
        "=========================================="
    )
    mavproxy(
        "rc 3 1000"
    )
    mavproxy(
        "mode MANUAL",
        0.3
    )
    mavproxy(
        "rc 1 1500"
    )
    mavproxy(
        "rc 2 1500"
    )
    mavproxy(
        "rc 4 1500"
    )
    set_plane(
        set_state,
        args.x,
        args.y,
        RUNWAY_Z
    )
    time.sleep(
        0.5
    )
    mavproxy(
        "mode FBWA",
        0.5
    )
    mavproxy(
        "rc 1 1500"
    )
    mavproxy(
        "rc 2 1500"
    )
    mavproxy(
        "rc 4 1500"
    )
    mavproxy(
        f"rc 3 {TAKEOFF_THROTTLE}"
    )
    print()
    print(
        f"[{args.model}] "
        "PIST KOSUSU BASLADI"
    )
    start = time.time()
    airborne_samples = 0
    while True:
        state = read_state(
            get_state
        )
        show(
            state,
            "RUNWAY"
        )
        if (
            state["z"] >= 0.50
            and
            state["vz"] >= 0.5
            and
            state["speed"] >= 13.0
        ):
            airborne_samples += 1
        else:
            airborne_samples = 0
        if (
            airborne_samples
            >= 2
        ):
            AIRBORNE = True
            break
        if (
            time.time() - start
            > 35.0
        ):
            print(
                f"[{args.model}] "
                "KALKIS BASARISIZ: "
                "TEKER KESEMEDI"
            )
            abort()
            return False
        if (
            state["x"]
            >= 135.0
        ):
            print(
                f"[{args.model}] "
                "KALKIS BASARISIZ: "
                "PIST SONU"
            )
            abort()
            return False
        if (
            abs(
                state["roll"]
            )
            >= 45.0
        ):
            print(
                f"[{args.model}] "
                "KALKIS BASARISIZ: "
                "ASIRI ROLL"
            )
            abort()
            return False
        if (
            abs(
                state["pitch"]
            )
            >= 35.0
        ):
            print(
                f"[{args.model}] "
                "KALKIS BASARISIZ: "
                "ASIRI PITCH"
            )
            abort()
            return False
        time.sleep(
            0.20
        )
    print()
    print(
        f"[{args.model}] "
        "TEKER KESME DOGRULANDI"
    )
    mavproxy(
        "rc 1 1500"
    )
    mavproxy(
        "rc 2 1500"
    )
    mavproxy(
        "rc 4 1500"
    )
    mavproxy(
        f"rc 3 {FLIGHT_THROTTLE}"
    )
    print(
        f"[{args.model}] "
        "STABIL UCUS KONTROL EDILIYOR..."
    )
    start = time.time()
    stable_samples = 0
    while (
        time.time() - start
        < 12.0
    ):
        time.sleep(
            0.20
        )
        state = read_state(
            get_state
        )
        show(
            state,
            "VERIFY"
        )
        if (
            abs(
                state["roll"]
            )
            >= 45.0
        ):
            print(
                f"[{args.model}] "
                "KALKIS BASARISIZ: "
                "ASIRI ROLL"
            )
            abort()
            return False
        if (
            abs(state["pitch"]) >= 30.0
            and state["vz"] < -2.0
        ):
            print(
                f"[{args.model}] "
                "KALKIS BASARISIZ: "
                "ASIRI PITCH"
            )
            abort()
            return False
        if (
            state["z"] <= 0.15
            and
            time.time() - start > 2.0
        ):
            print(
                f"[{args.model}] "
                "KALKIS BASARISIZ: "
                "YERE DONDU"
            )
            AIRBORNE = False
            abort()
            return False
        if (
            state["speed"]
            < 9.0
            and
            time.time() - start > 2.0
        ):
            print(
                f"[{args.model}] "
                "KALKIS BASARISIZ: "
                "STALL"
            )
            abort()
            return False
        if (
            time.time() - start
            >= 4.0
            and
            state["z"] >= 1.5
            and
            state["speed"] >= 12.0
            and
            abs(
                state["roll"]
            )
            <= 15.0
            and
            abs(
                state["pitch"]
            )
            <= 10.0
            and
            abs(
                state["vz"]
            )
            <= 4.0
        ):
            stable_samples += 1
        else:
            stable_samples = 0
        if (
            stable_samples
            >= 8
        ):
            print()
            print(
                "=========================================="
            )
            print(
                f"[{args.model}] "
                "KALKIS BASARIYLA TAMAMLANDI"
            )
            print(
                f"[{args.model}] "
                f"x={state['x']:.1f} "
                f"y={state['y']:.1f} "
                f"z={state['z']:.2f}m "
                f"V={state['speed']:.2f}m/s "
                f"roll={state['roll']:.1f} "
                f"pitch={state['pitch']:.1f}"
            )
            print(
                "=========================================="
            )
            return True
    print(
        f"[{args.model}] "
        "KALKIS BASARISIZ: "
        "STABIL UCUS DOGRULANAMADI"
    )
    abort()
    return False
def main():
    rospy.init_node(
        f"{args.model}_auto_takeoff",
        anonymous=True
    )
    rospy.wait_for_service(
        "/gazebo/set_model_state"
    )
    rospy.wait_for_service(
        "/gazebo/get_model_state"
    )
    set_state = (
        rospy.ServiceProxy(
            "/gazebo/set_model_state",
            SetModelState
        )
    )
    get_state = (
        rospy.ServiceProxy(
            "/gazebo/get_model_state",
            GetModelState
        )
    )
    print()
    print(
        "=========================================="
    )
    print(
        f"[{args.model}] "
        f"X={args.x:.1f} "
        f"Y={args.y:.1f}"
    )
    print(
        "=========================================="
    )
    mavproxy(
        "mode MANUAL",
        0.5
    )
    mavproxy(
        "rc 1 1500"
    )
    mavproxy(
        "rc 2 1500"
    )
    mavproxy(
        "rc 3 1000"
    )
    mavproxy(
        "rc 4 1500"
    )
    mavproxy(
        "arm throttle force",
        0.5
    )
    return runway_takeoff(
        set_state,
        get_state
    )
if __name__ == "__main__":
    try:
        success = main()
        raise SystemExit(
            0
            if success
            else 1
        )
    except Exception as error:
        print()
        print(
            f"[{args.model}] "
            f"HATA: {error}"
        )
        try:
            abort()
        except Exception:
            pass
        raise SystemExit(
            1
        )