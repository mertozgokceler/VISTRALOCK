#!/usr/bin/env python3

import math
import re

import rospy

from gazebo_msgs.msg import ModelStates

from PyQt5.QtCore import (
    QObject,
    pyqtSignal
)


class RosMultiAircraftProvider(QObject):

    aircraft_states_updated = pyqtSignal(object)
    aircraft_ids_updated = pyqtSignal(object)

    def __init__(self):

        super().__init__()

        self.last_aircraft_ids = []

        self.subscriber = rospy.Subscriber(
            "/gazebo/model_states",
            ModelStates,
            self.model_states_callback,
            queue_size=1
        )

    def get_aircraft_id(
        self,
        model_name
    ):

        if model_name == "mini_talon_clean":
            return 1

        match = re.fullmatch(
            r"mini_talon_(\d+)",
            model_name
        )

        if match is None:
            return None

        return int(
            match.group(1)
        )

    def quaternion_to_heading(
        self,
        quaternion
    ):

        x = quaternion.x
        y = quaternion.y
        z = quaternion.z
        w = quaternion.w

        sin_yaw = (
            2.0
            * (
                w * z
                + x * y
            )
        )

        cos_yaw = (
            1.0
            - 2.0
            * (
                y * y
                + z * z
            )
        )

        yaw = math.atan2(
            sin_yaw,
            cos_yaw
        )

        yaw_deg = math.degrees(
            yaw
        )

        heading = (
            90.0
            - yaw_deg
        ) % 360.0

        return heading

    def model_states_callback(
        self,
        msg
    ):

        aircraft_states = {}

        for index, model_name in enumerate(
            msg.name
        ):

            aircraft_id = (
                self.get_aircraft_id(
                    model_name
                )
            )

            if aircraft_id is None:
                continue

            pose = msg.pose[index]
            twist = msg.twist[index]

            vx = twist.linear.x
            vy = twist.linear.y
            vz = twist.linear.z

            speed = math.sqrt(
                vx * vx
                + vy * vy
                + vz * vz
            )

            heading = (
                self.quaternion_to_heading(
                    pose.orientation
                )
            )

            aircraft_states[
                aircraft_id
            ] = {
                "aircraft_id": aircraft_id,
                "model_name": model_name,

                "x": pose.position.x,
                "y": pose.position.y,
                "z": pose.position.z,

                "vx": vx,
                "vy": vy,
                "vz": vz,

                "speed": speed,
                "heading_deg": heading
            }

        aircraft_ids = sorted(
            aircraft_states.keys()
        )

        if (
            aircraft_ids
            != self.last_aircraft_ids
        ):

            self.last_aircraft_ids = (
                aircraft_ids.copy()
            )

            self.aircraft_ids_updated.emit(
                aircraft_ids
            )

            print(
                "AIRCRAFT DETECTED:",
                aircraft_ids
            )

        self.aircraft_states_updated.emit(
            aircraft_states
        )