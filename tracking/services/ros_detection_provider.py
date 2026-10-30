import json
import rospy

from PyQt5.QtCore import (
    QObject,
    pyqtSignal
)

from std_msgs.msg import String


class RosDetectionProvider(QObject):

    detections_received = pyqtSignal(
        object
    )

    def __init__(self):
        super().__init__()

        self.subscriber = rospy.Subscriber(
            "/yolo/detections",
            String,
            self.detection_callback,
            queue_size=1
        )

    def detection_callback(
        self,
        msg
    ):

        try:

            data = json.loads(
                msg.data
            )

            detections = data.get(
                "detections",
                []
            )

            self.detections_received.emit(
                detections
            )

        except Exception as error:

            rospy.logerr(
                f"Detection parse error: {error}"
            )