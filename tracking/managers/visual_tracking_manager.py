from PyQt5.QtCore import QObject, pyqtSignal


class VisualTrackingManager(QObject):

    detections_updated = pyqtSignal(object)
    status_changed = pyqtSignal(str)
    # Real 4-second ROI lock progress; separate from initial target acquisition.
    lock_progress_updated = pyqtSignal(float, bool)

    def __init__(
        self,
        yolo_service,
        target_lock_controller,
        visual_tracking_controller,
        acquire_controller,
        ownship_control_service,
        geofence_manager,
        tracking_manager,
        frame_size_provider,
    ):
        super().__init__()

        self.yolo_service = yolo_service
        self.target_lock_controller = target_lock_controller
        self.visual_tracking_controller = visual_tracking_controller
        self.acquire_controller = acquire_controller
        self.ownship_control_service = ownship_control_service
        self.geofence_manager = geofence_manager
        self.tracking_manager = tracking_manager

        self.frame_size_provider = frame_size_provider

    def handle_detections(self, detections):

        if not self.yolo_service.is_running():
            self.target_lock_controller.reset_roi_lock()
            self.detections_updated.emit([])
            self.lock_progress_updated.emit(0.0, False)
            return

        self.detections_updated.emit(detections)

        if self.geofence_manager.return_active:
            self.target_lock_controller.reset_roi_lock()
            self.lock_progress_updated.emit(0.0, False)
            return

        if self.tracking_manager.active_target_id is None:
            self.target_lock_controller.reset_roi_lock()
            self.lock_progress_updated.emit(0.0, False)
            return

        image_width, image_height = self.frame_size_provider()

        if image_width <= 0 or image_height <= 0:
            return

        result = self.target_lock_controller.update(
            detections,
            image_width,
            image_height,
        )

        self.lock_progress_updated.emit(
            float(result.get("lock_seconds", 0.0)),
            bool(result.get("lock_success", False)),
        )
        if result.get("lock_just_succeeded", False):
            print("ROI LOCK SUCCESS (4.0 s):", result.get("track_id"))

        if result.get("neutralize", False):
            self.neutralize()

        self._handle_lock_event(result)

        target_detection = result.get("detection")

        if target_detection is None:
            return

        if not self.visual_tracking_controller.active:
            return

        if not self.visual_tracking_controller.should_send():
            return

        self._send_visual_control(
            target_detection,
            image_width,
            image_height,
        )

    def _handle_lock_event(self, result):

        event = result["event"]

        if event == "LOCKED":
            self.acquire_controller.stop()
            self.visual_tracking_controller.start()

            self.status_changed.emit(
                "VISUAL TRACKING"
            )

            print(
                "VISUAL TARGET LOCKED:",
                result["track_id"],
            )

        elif event == "LOST":

            if result.get("neutralize", False):

                self.status_changed.emit(
                    "REACQUIRE"
                )

                print(
                    "VISUAL TARGET LOST:",
                    result["track_id"],
                )

        elif event == "REACQUIRING":

            self.status_changed.emit(
                "REACQUIRE"
            )

            print(
                "REACQUIRE CANDIDATE:",
                result.get("candidate_id"),
            )

        elif event == "REACQUIRED":

            self.status_changed.emit(
                "VISUAL TRACKING"
            )

            print(
                "VISUAL TARGET REACQUIRED:",
                result.get("old_track_id"),
                "->",
                result["track_id"],
            )

    def _send_visual_control(
        self,
        target_detection,
        image_width,
        image_height,
    ):

        (
            roll_pwm,
            pitch_pwm,
            error_x,
            error_y,
        ) = self.visual_tracking_controller.calculate_commands(
            target_detection["bbox"],
            image_width,
            image_height,
        )

        self.ownship_control_service.send_ownship_rc_command(
            1,
            roll_pwm,
        )

        self.ownship_control_service.send_ownship_rc_command(
            4,
            pitch_pwm,
        )

        print(
            "VISUAL:",
            f"ID={self.target_lock_controller.active_track_id}",
            f"X={error_x:.1f}",
            f"Y={error_y:.1f}",
            f"ROLL={roll_pwm}",
            f"PITCH={pitch_pwm}",
        )

    def neutralize(self):

        self.ownship_control_service.send_ownship_rc_command(
            1,
            1500,
        )

        self.ownship_control_service.send_ownship_rc_command(
            4,
            1500,
        )

    def stop(self):

        self.target_lock_controller.reset()
        self.visual_tracking_controller.stop()

        self.detections_updated.emit([])
        self.lock_progress_updated.emit(0.0, False)