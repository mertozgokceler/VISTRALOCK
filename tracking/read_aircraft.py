#!/usr/bin/env python3

import math
import rospy
from gazebo_msgs.msg import ModelStates
from tf.transformations import euler_from_quaternion


TRACK_DISTANCE_THRESHOLD = 80.0
ALTITUDE_DEADBAND = 5.0
MAX_ALTITUDE_DIFFERENCE = 30.0
MAX_HEADING_ERROR = 90.0

MIN_SUITABILITY_SCORE = 60.0
CANDIDATE_CONFIRM_TIME = 2.0

candidate_start_time = None
candidate_confirmed = False
last_print_time = 0.0


def callback(msg):

    global last_print_time
    global candidate_start_time
    global candidate_confirmed

    current_time = rospy.get_time()

    if current_time - last_print_time < 0.5:
        return

    last_print_time = current_time

    if (
        "mini_talon_2" not in msg.name
        or "mini_talon_clean" not in msg.name
    ):
        return

    own_index = msg.name.index(
        "mini_talon_2"
    )

    target_index = msg.name.index(
        "mini_talon_clean"
    )

    own_pose = msg.pose[
        own_index
    ]

    target_pose = msg.pose[
        target_index
    ]

    dx = (
        target_pose.position.x
        -
        own_pose.position.x
    )

    dy = (
        target_pose.position.y
        -
        own_pose.position.y
    )

    dz = (
        target_pose.position.z
        -
        own_pose.position.z
    )

    distance = math.sqrt(
        dx**2 +
        dy**2 +
        dz**2
    )

    target_bearing = math.degrees(
        math.atan2(
            dy,
            dx
        )
    )

    q = own_pose.orientation

    roll, pitch, yaw = euler_from_quaternion(
        [
            q.x,
            q.y,
            q.z,
            q.w
        ]
    )

    own_heading = math.degrees(
        yaw
    )

    heading_error = (
        target_bearing
        -
        own_heading
    )

    if heading_error > 180:
        heading_error -= 360

    elif heading_error < -180:
        heading_error += 360

    if abs(heading_error) <= 10:
        target_direction = "ONDE"

    elif 10 < heading_error <= 90:
        target_direction = "SOL-ON"

    elif -90 <= heading_error < -10:
        target_direction = "SAG-ON"

    elif 90 < heading_error < 170:
        target_direction = "SOL-ARKA"

    elif -170 < heading_error < -90:
        target_direction = "SAG-ARKA"

    else:
        target_direction = "ARKADA"

    if dz > ALTITUDE_DEADBAND:
        target_altitude = "YUKARIDA"

    elif dz < -ALTITUDE_DEADBAND:
        target_altitude = "ASAGIDA"

    else:
        target_altitude = "AYNI SEVIYEDE"

    distance_score = max(
        0.0,
        1.0
        -
        distance
        /
        TRACK_DISTANCE_THRESHOLD
    )

    altitude_score = max(
        0.0,
        1.0
        -
        abs(dz)
        /
        MAX_ALTITUDE_DIFFERENCE
    )

    heading_score = max(
        0.0,
        1.0
        -
        abs(heading_error)
        /
        MAX_HEADING_ERROR
    )

    suitability_score = (
        distance_score * 0.50
        +
        heading_score * 0.30
        +
        altitude_score * 0.20
    ) * 100

    distance_ok = (
        distance
        <=
        TRACK_DISTANCE_THRESHOLD
    )

    altitude_ok = (
        abs(dz)
        <=
        MAX_ALTITUDE_DIFFERENCE
    )

    heading_ok = (
        abs(heading_error)
        <=
        MAX_HEADING_ERROR
    )

    candidate_ok = (
        distance_ok
        and altitude_ok
        and heading_ok
        and suitability_score
        >=
        MIN_SUITABILITY_SCORE
    )

    print(
        f"ID 2 (BIZIM): "
        f"x={own_pose.position.x:.1f} "
        f"y={own_pose.position.y:.1f} "
        f"z={own_pose.position.z:.1f}"
    )

    print(
        f"ID 1 (RAKIP): "
        f"x={target_pose.position.x:.1f} "
        f"y={target_pose.position.y:.1f} "
        f"z={target_pose.position.z:.1f}"
    )

    print(
        f"Mesafe: "
        f"{distance:.1f} metre"
    )

    print(
        f"Bizim heading: "
        f"{own_heading:.1f} derece"
    )

    print(
        f"Rakip yonu: "
        f"{target_bearing:.1f} derece"
    )

    print(
        f"Heading error: "
        f"{heading_error:.1f} derece"
    )

    print(
        f"Rakip konumu: "
        f"{target_direction}"
    )

    print(
        f"Dikey konum: "
        f"{target_altitude}"
    )

    print(
        f"Irtifa farki: "
        f"{dz:+.1f} metre"
    )

    print(
        f"Takip uygunluk skoru: "
        f"%{suitability_score:.1f}"
    )

    if not candidate_ok:

        print(
            "ID 1 su an takip icin uygun degil."
        )

        if not distance_ok:
            print(
                "- Sebep: Mesafe fazla."
            )

        if not altitude_ok:
            print(
                "- Sebep: Irtifa farki fazla."
            )

        if not heading_ok:
            print(
                "- Sebep: Rakip arka bolgede."
            )

        if (
            distance_ok
            and altitude_ok
            and heading_ok
            and suitability_score
            <
            MIN_SUITABILITY_SCORE
        ):
            print(
                "- Sebep: Uygunluk skoru dusuk."
            )

    if candidate_ok:

        if candidate_start_time is None:
            candidate_start_time = rospy.get_time()

        candidate_duration = (
            rospy.get_time()
            -
            candidate_start_time
        )

        if (
            candidate_duration
            >=
            CANDIDATE_CONFIRM_TIME
            and
            not candidate_confirmed
        ):

            candidate_confirmed = True

            print(
                ">>> ID 1 TAKIP ADAYI "
                "OLARAK DOGRULANDI"
            )

        elif not candidate_confirmed:

            print(
                f"Aday dogrulaniyor: "
                f"{candidate_duration:.1f} / "
                f"{CANDIDATE_CONFIRM_TIME:.1f} saniye"
            )

        else:

            print(
                "ID 1 takip adayi: DOGRULANDI"
            )

    else:

        candidate_start_time = None
        candidate_confirmed = False

    print(
        "------------------------"
    )


rospy.init_node(
    "aircraft_reader"
)

rospy.Subscriber(
    "/gazebo/model_states",
    ModelStates,
    callback
)

rospy.spin()