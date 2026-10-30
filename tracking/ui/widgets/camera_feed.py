from PyQt5.QtWidgets import (
    QFrame,
    QLabel
)

from PyQt5.QtCore import (
    Qt,
    QRect
)

from PyQt5.QtGui import (
    QImage,
    QPixmap,
    QPainter,
    QPen,
    QColor
)


class CameraFeed(QFrame):

    def __init__(self):
        super().__init__()

        self.current_pixmap = None

        self.image_width = 640
        self.image_height = 480

        self.detections = []

        self.video_label = QLabel(
            self
        )

        self.video_label.setAlignment(
            Qt.AlignCenter
        )

        self.video_label.setText(
            "WAITING FOR CAMERA..."
        )

        self.video_label.setStyleSheet("""
            QLabel {
                background-color: #05070B;
                color: #64748B;
                border: none;
                font-size: 13px;
                font-weight: bold;
            }
        """)

        self.roi_overlay = QLabel(
            self
        )

        self.roi_overlay.setAttribute(
            Qt.WA_TransparentForMouseEvents
        )

        self.roi_overlay.setStyleSheet(
            "background: transparent;"
        )

        self.detection_overlay = QLabel(
            self
        )

        self.detection_overlay.setAttribute(
            Qt.WA_TransparentForMouseEvents
        )

        self.detection_overlay.setStyleSheet(
            "background: transparent;"
        )

        self.setMinimumSize(
            320,
            240
        )

        self.setStyleSheet("""
            CameraFeed {
                background-color: #05070B;
                border: 1px solid #263244;
                border-radius: 8px;
            }
        """)

    def update_frame(
        self,
        frame
    ):

        height, width, channels = (
            frame.shape
        )

        size_changed = (
            width != self.image_width
            or height != self.image_height
        )

        self.image_width = width
        self.image_height = height

        bytes_per_line = (
            channels * width
        )

        image = QImage(
            frame.data,
            width,
            height,
            bytes_per_line,
            QImage.Format_RGB888
        ).copy()

        self.current_pixmap = (
            QPixmap.fromImage(
                image
            )
        )

        self.update_video()

        if size_changed:

            self.create_roi_overlay()

            self.create_detection_overlay()

    def update_video(
        self
    ):

        if self.current_pixmap is None:
            return

        scaled_pixmap = (
            self.current_pixmap.scaled(
                self.video_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )

        self.video_label.setPixmap(
            scaled_pixmap
        )

    def update_detections(
        self,
        detections
    ):

        self.detections = detections

        self.create_detection_overlay()

    def create_roi_overlay(
        self
    ):

        if (
            self.width() <= 0
            or self.height() <= 0
        ):
            return

        overlay = QPixmap(
            self.size()
        )

        overlay.fill(
            Qt.transparent
        )

        painter = QPainter(
            overlay
        )

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        display_rect = (
            self.calculate_image_rect()
        )

        if display_rect is None:

            painter.end()

            return

        roi_x1 = int(
            display_rect.x()
            + display_rect.width() * 0.25
        )

        roi_y1 = int(
            display_rect.y()
            + display_rect.height() * 0.10
        )

        roi_x2 = int(
            display_rect.x()
            + display_rect.width() * 0.75
        )

        roi_y2 = int(
            display_rect.y()
            + display_rect.height() * 0.90
        )

        roi_rect = QRect(
            roi_x1,
            roi_y1,
            roi_x2 - roi_x1,
            roi_y2 - roi_y1
        )

        pen = QPen(
            QColor(
                "#FACC15"
            )
        )

        pen.setWidth(
            2
        )

        painter.setPen(
            pen
        )

        painter.drawRect(
            roi_rect
        )

        painter.end()

        self.roi_overlay.setPixmap(
            overlay
        )

        self.roi_overlay.raise_()

        self.detection_overlay.raise_()

    def create_detection_overlay(
        self
    ):

        if (
            self.width() <= 0
            or self.height() <= 0
        ):
            return

        overlay = QPixmap(
            self.size()
        )

        overlay.fill(
            Qt.transparent
        )

        if (
            not self.detections
            or self.image_width <= 0
            or self.image_height <= 0
        ):

            self.detection_overlay.setPixmap(
                overlay
            )

            return

        display_rect = (
            self.calculate_image_rect()
        )

        if display_rect is None:
            return

        scale_x = (
            display_rect.width()
            / self.image_width
        )

        scale_y = (
            display_rect.height()
            / self.image_height
        )

        painter = QPainter(
            overlay
        )

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        box_pen = QPen(
            QColor(
                "#FF1744"
            )
        )

        box_pen.setWidth(
            2
        )

        painter.setPen(
            box_pen
        )

        for detection in self.detections:

            bbox = detection.get(
                "bbox"
            )

            if (
                bbox is None
                or len(bbox) != 4
            ):
                continue

            x1, y1, x2, y2 = bbox

            screen_x1 = int(
                display_rect.x()
                + x1 * scale_x
            )

            screen_y1 = int(
                display_rect.y()
                + y1 * scale_y
            )

            screen_x2 = int(
                display_rect.x()
                + x2 * scale_x
            )

            screen_y2 = int(
                display_rect.y()
                + y2 * scale_y
            )

            box_rect = QRect(
                screen_x1,
                screen_y1,
                screen_x2 - screen_x1,
                screen_y2 - screen_y1
            )

            painter.drawRect(
                box_rect
            )

            target_center_x = int(
                (screen_x1 + screen_x2) / 2
            )

            target_center_y = int(
                (screen_y1 + screen_y2) / 2
            )

            image_center_x = (
                display_rect.center().x()
            )

            image_center_y = (
                display_rect.center().y()
            )

            painter.drawEllipse(
                target_center_x - 3,
                target_center_y - 3,
                6,
                6
            )

            painter.drawLine(
                image_center_x,
                image_center_y,
                target_center_x,
                target_center_y
            )

            confidence = detection.get(
                "confidence",
                0.0
            )

            class_name = detection.get(
                "class_name",
                "UAV"
            )

            track_id = detection.get(
                "track_id"
            )

            if track_id is not None:

                label = (
                    f"id:{track_id} "
                    f"{class_name.upper()} "
                    f"{confidence:.2f}"
                )

            else:

                label = (
                    f"{class_name.upper()} "
                    f"{confidence:.2f}"
                )

            painter.drawText(
                screen_x1,
                max(
                    18,
                    screen_y1 - 6
                ),
                label
            )

        painter.end()

        self.detection_overlay.setPixmap(
            overlay
        )

        self.detection_overlay.raise_()

    def calculate_image_rect(
        self
    ):

        if (
            self.image_width <= 0
            or self.image_height <= 0
        ):
            return None

        widget_width = (
            self.width()
        )

        widget_height = (
            self.height()
        )

        image_ratio = (
            self.image_width
            / self.image_height
        )

        widget_ratio = (
            widget_width
            / widget_height
        )

        if widget_ratio > image_ratio:

            display_height = (
                widget_height
            )

            display_width = int(
                display_height
                * image_ratio
            )

        else:

            display_width = (
                widget_width
            )

            display_height = int(
                display_width
                / image_ratio
            )

        x = int(
            (
                widget_width
                - display_width
            ) / 2
        )

        y = int(
            (
                widget_height
                - display_height
            ) / 2
        )

        return QRect(
            x,
            y,
            display_width,
            display_height
        )

    def resizeEvent(
        self,
        event
    ):

        super().resizeEvent(
            event
        )

        self.video_label.setGeometry(
            self.rect()
        )

        self.roi_overlay.setGeometry(
            self.rect()
        )

        self.detection_overlay.setGeometry(
            self.rect()
        )

        self.update_video()

        self.create_roi_overlay()

        self.create_detection_overlay()