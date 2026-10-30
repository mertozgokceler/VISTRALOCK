import math
import time

import rospy

from PyQt5.QtCore import (
    QObject,
    pyqtSignal,
    QTimer
)

from gazebo_msgs.msg import ModelStates

from tf.transformations import (
    euler_from_quaternion
)

from models.aircraft_state import AircraftState
from std_msgs.msg import Bool

class RosAircraftProvider(QObject):

    aircraft_states_updated = pyqtSignal(
        object,
        object
    )

    connection_status_changed = pyqtSignal(
        bool
    )

    tracking_enabled_changed = pyqtSignal(
        bool
    )

    def __init__(self):
        super().__init__()

        self.own_model_name = (
            "mini_talon_2"
        )

        self.target_model_name = (
            "mini_talon_clean"
        )

        self.connection_timeout = 2.0

        self.last_data_time = None
        self.is_online = False

        self.connection_timer = QTimer(
            self
        )

        self.connection_timer.timeout.connect(
            self.check_connection
        )

        self.connection_timer.start(
            200
        )

        self.tracking_enabled = False

        self.subscriber = rospy.Subscriber(
            "/gazebo/model_states",
            ModelStates,
            self.model_states_callback,
            queue_size=1
        )

        self.tracking_subscriber = rospy.Subscriber(
            "/tracking/enabled",
            Bool,
            self.tracking_enabled_callback,
            queue_size=1
        )

    def model_states_callback(
        self,
        msg
    ):

        self.last_data_time = (
            time.monotonic()
        )

        if not self.is_online:

            self.is_online = True

            self.connection_status_changed.emit(
                True
            )

        if (
            self.own_model_name
            not in msg.name
        ):
            return

        if (
            self.target_model_name
            not in msg.name
        ):
            return

        own_index = msg.name.index(
            self.own_model_name
        )

        target_index = msg.name.index(
            self.target_model_name
        )

        own_state = self.create_aircraft_state(
            aircraft_id=2,
            model_name=self.own_model_name,
            pose=msg.pose[own_index],
            twist=msg.twist[own_index]
        )

        target_state = self.create_aircraft_state(
            aircraft_id=1,
            model_name=self.target_model_name,
            pose=msg.pose[target_index],
            twist=msg.twist[target_index]
        )

        self.aircraft_states_updated.emit(
            own_state,
            target_state
        )

    def check_connection(
        self
    ):

        if self.last_data_time is None:
            return

        elapsed = (
            time.monotonic()
            - self.last_data_time
        )

        if (
            elapsed > self.connection_timeout
            and self.is_online
        ):

            self.is_online = False

            self.connection_status_changed.emit(
                False
            )

    def create_aircraft_state(
        self,
        aircraft_id,
        model_name,
        pose,
        twist
    ):

        quaternion = [
            pose.orientation.x,
            pose.orientation.y,
            pose.orientation.z,
            pose.orientation.w
        ]

        roll, pitch, yaw = (
            euler_from_quaternion(
                quaternion
            )
        )

        roll_deg = math.degrees(
            roll
        )

        pitch_deg = math.degrees(
            pitch
        )

        yaw_deg = math.degrees(
            yaw
        )

        compass_heading_deg = (
            90.0 - yaw_deg
        ) % 360.0

        return AircraftState(
            aircraft_id=aircraft_id,
            model_name=model_name,

            x=pose.position.x,
            y=pose.position.y,
            z=pose.position.z,

            roll_deg=roll_deg,
            pitch_deg=pitch_deg,
            yaw_deg=yaw_deg,

            compass_heading_deg=compass_heading_deg,

            velocity_x=twist.linear.x,
            velocity_y=twist.linear.y,
            velocity_z=twist.linear.z
        )

    def tracking_enabled_callback(
        self,
        msg
    ):

        self.tracking_enabled = bool(
            msg.data
        )

        self.tracking_enabled_changed.emit(
            self.tracking_enabled
        )