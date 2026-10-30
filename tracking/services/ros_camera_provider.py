import rospy

from PyQt5.QtCore import (
    QObject,
    pyqtSignal
)

from sensor_msgs.msg import Image
from cv_bridge import CvBridge


class RosCameraProvider(QObject):

    frame_received = pyqtSignal(object)

    def __init__(self):
        super().__init__()

        self.bridge = CvBridge()

        self.camera_topic = (
            "/mini_talon_2/"
            "front_camera/"
            "camera/"
            "image_raw"
        )

        self.subscriber = rospy.Subscriber(
            self.camera_topic,
            Image,
            self.image_callback,
            queue_size=1,
            buff_size=2**24
        )

    def image_callback(
        self,
        msg
    ):

        try:

            frame = self.bridge.imgmsg_to_cv2(
                msg,
                desired_encoding="rgb8"
            )

            self.frame_received.emit(
                frame
            )

        except Exception as error:

            rospy.logwarn_throttle(
                2.0,
                f"Camera conversion error: {error}"
            )