import math
import time

from models.tracking_metrics import TrackingMetrics


class TrackingController:

    def __init__(self):

        self.track_distance_threshold = 80.0
        self.max_altitude_difference = 30.0
        self.max_heading_error = 90.0
        self.altitude_deadband = 5.0
        self.min_suitability_score = 60.0

        self.candidate_confirm_time = 2.0

        self.candidate_start_time = None
        self.candidate_confirmed = False

        self.reject_cooldown = 10.0
        self.reject_cooldown_until = None

        self.tracking_enabled = False

    def set_tracking_enabled(
        self,
        enabled
    ):

        self.tracking_enabled = enabled

        if not enabled:

            self.candidate_start_time = None
            self.candidate_confirmed = False
            self.reject_cooldown_until = None

    def calculate_metrics(
        self,
        own_state,
        target_state
    ):

        dx = (
            target_state.x
            - own_state.x
        )

        dy = (
            target_state.y
            - own_state.y
        )

        dz = (
            target_state.z
            - own_state.z
        )

        distance = math.sqrt(
            dx ** 2
            + dy ** 2
            + dz ** 2
        )

        target_bearing_math = math.degrees(
            math.atan2(
                dy,
                dx
            )
        )

        heading_error = self.normalize_angle(
            target_bearing_math
            - own_state.yaw_deg
        )

        target_bearing = (
            90.0
            - target_bearing_math
        ) % 360.0

        horizontal_direction = (
            self.calculate_horizontal_direction(
                heading_error
            )
        )

        vertical_direction = (
            self.calculate_vertical_direction(
                dz
            )
        )

        distance_score = max(
            0.0,
            1.0
            - distance
            / self.track_distance_threshold
        )

        altitude_score = max(
            0.0,
            1.0
            - abs(dz)
            / self.max_altitude_difference
        )

        heading_score = max(
            0.0,
            1.0
            - abs(heading_error)
            / self.max_heading_error
        )

        suitability_score = (
            distance_score * 0.50
            + heading_score * 0.30
            + altitude_score * 0.20
        ) * 100.0

        distance_ok = (
            distance
            <= self.track_distance_threshold
        )

        altitude_ok = (
            abs(dz)
            <= self.max_altitude_difference
        )

        heading_ok = (
            abs(heading_error)
            <= self.max_heading_error
        )

        candidate_ok = (
            distance_ok
            and altitude_ok
            and heading_ok
            and suitability_score
            >= self.min_suitability_score
        )

        return TrackingMetrics(
            distance=distance,
            altitude_difference=dz,
            target_bearing=target_bearing,
            heading_error=heading_error,
            horizontal_direction=horizontal_direction,
            vertical_direction=vertical_direction,
            suitability_score=suitability_score,
            candidate_ok=candidate_ok
        )

    def normalize_angle(
        self,
        angle
    ):

        while angle > 180.0:
            angle -= 360.0

        while angle < -180.0:
            angle += 360.0

        return angle

    def calculate_horizontal_direction(
        self,
        heading_error
    ):

        if abs(heading_error) <= 10.0:
            return "ONDE"

        if (
            10.0
            < heading_error
            <= 90.0
        ):
            return "SOL-ON"

        if (
            -90.0
            <= heading_error
            < -10.0
        ):
            return "SAG-ON"

        if (
            90.0
            < heading_error
            < 170.0
        ):
            return "SOL-ARKA"

        if (
            -170.0
            < heading_error
            < -90.0
        ):
            return "SAG-ARKA"

        return "ARKADA"

    def calculate_vertical_direction(
        self,
        altitude_difference
    ):

        if (
            altitude_difference
            > self.altitude_deadband
        ):
            return "YUKARIDA"

        if (
            altitude_difference
            < -self.altitude_deadband
        ):
            return "ASAGIDA"

        return "AYNI SEVIYEDE"

    def update_candidate(
        self,
        metrics
    ):

        if not self.tracking_enabled:

            self.candidate_start_time = None
            self.candidate_confirmed = False

            return False

        current_time = time.monotonic()

        if (
            self.reject_cooldown_until
            is not None
        ):

            if (
                current_time
                < self.reject_cooldown_until
            ):

                self.candidate_start_time = None

                return False

            self.reject_cooldown_until = None

        if not metrics.candidate_ok:

            self.candidate_start_time = None
            self.candidate_confirmed = False

            return False

        if self.candidate_confirmed:
            return False

        if self.candidate_start_time is None:

            self.candidate_start_time = (
                current_time
            )

            return False

        elapsed = (
            current_time
            - self.candidate_start_time
        )

        if (
            elapsed
            >= self.candidate_confirm_time
        ):

            self.candidate_confirmed = True

            return True

        return False

    def reject_candidate(
        self
    ):

        self.candidate_start_time = None
        self.candidate_confirmed = False

        self.reject_cooldown_until = (
            time.monotonic()
            + self.reject_cooldown
        )

    def reset_candidate(
        self
    ):

        self.candidate_start_time = None
        self.candidate_confirmed = False