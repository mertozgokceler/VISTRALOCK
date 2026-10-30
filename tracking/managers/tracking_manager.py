#!/usr/bin/env python3

from PyQt5.QtCore import (
    QObject,
    pyqtSignal
)


class TrackingManager(QObject):

    status_changed = pyqtSignal(
        str
    )

    candidate_found = pyqtSignal(
        object
    )

    candidate_cleared = pyqtSignal()

    target_metrics_updated = pyqtSignal(
        int,
        object
    )

    active_target_changed = pyqtSignal(
        object
    )

    tracking_started = pyqtSignal(
        int
    )

    tracking_stopped = pyqtSignal()

    def __init__(
        self,
        tracking_controller,
        acquire_controller,
        visual_tracking_controller,
        target_lock_controller,
        geofence_manager,
        ownship_control_service
    ):

        super().__init__()

        self.tracking_controller = (
            tracking_controller
        )

        self.acquire_controller = (
            acquire_controller
        )

        self.visual_tracking_controller = (
            visual_tracking_controller
        )

        self.target_lock_controller = (
            target_lock_controller
        )

        self.geofence_manager = (
            geofence_manager
        )

        self.ownship_control_service = (
            ownship_control_service
        )

        self.pending_candidate_id = None

        self.active_target_id = None

    def update_aircraft_states(
        self,
        own_state,
        target_state
    ):

        if self.geofence_manager.update(
            own_state,
            self.active_target_id
        ):

            return

        metrics = (
            self.tracking_controller.calculate_metrics(
                own_state,
                target_state
            )
        )

        if self.acquire_controller.active:

            roll_pwm = (
                self.acquire_controller.calculate_roll_pwm(
                    metrics.heading_error
                )
            )

            if self.acquire_controller.should_send(
                roll_pwm
            ):

                self.ownship_control_service.send_ownship_rc_command(
                    1,
                    roll_pwm
                )

        self.target_metrics_updated.emit(
            int(
                target_state.aircraft_id
            ),
            metrics
        )

        if (
            self.pending_candidate_id
            is not None
        ):

            return

        if (
            self.active_target_id
            is not None
        ):

            return

        candidate_confirmed = (
            self.tracking_controller.update_candidate(
                metrics
            )
        )

        if not candidate_confirmed:
            return

        self.pending_candidate_id = (
            int(
                target_state.aircraft_id
            )
        )

        self.status_changed.emit(
            "CANDIDATE"
        )

        self.candidate_found.emit(
            metrics
        )

    def set_tracking_enabled(
        self,
        enabled
    ):

        was_enabled = (
            self.tracking_controller.tracking_enabled
        )

        self.tracking_controller.set_tracking_enabled(
            enabled
        )

        if (
            enabled
            and not was_enabled
        ):

            self.status_changed.emit(
                "SEARCH"
            )

            return

        if (
            not enabled
            and was_enabled
        ):

            self.pending_candidate_id = None

            self.candidate_cleared.emit()

            self.status_changed.emit(
                "STANDBY"
            )

    def accept_candidate(
        self
    ):

        if (
            self.pending_candidate_id
            is None
        ):

            return

        self.active_target_id = (
            self.pending_candidate_id
        )

        self.pending_candidate_id = None

        self.target_lock_controller.reset()

        self.visual_tracking_controller.stop()

        self.candidate_cleared.emit()

        self.active_target_changed.emit(
            self.active_target_id
        )

        self.tracking_started.emit(
            self.active_target_id
        )

        self.acquire_controller.start()

        self.status_changed.emit(
            "ACQUIRE"
        )

    def reject_candidate(
        self
    ):

        self.pending_candidate_id = None

        self.candidate_cleared.emit()

        self.tracking_controller.reject_candidate()

        self.status_changed.emit(
            "SEARCH"
        )

    def stop_tracking(
        self
    ):

        self.acquire_controller.stop()

        self.visual_tracking_controller.stop()

        self.target_lock_controller.reset()

        self.geofence_manager.reset()

        self.pending_candidate_id = None

        self.active_target_id = None

        self.active_target_changed.emit(
            None
        )

        self.tracking_stopped.emit()

        self.candidate_cleared.emit()

        self.tracking_controller.reject_candidate()

        self.status_changed.emit(
            "SEARCH"
        )

    def reset(
        self
    ):

        self.acquire_controller.stop()

        self.visual_tracking_controller.stop()

        self.target_lock_controller.reset()

        self.pending_candidate_id = None

        self.active_target_id = None

        self.active_target_changed.emit(
            None
        )

        self.candidate_cleared.emit()