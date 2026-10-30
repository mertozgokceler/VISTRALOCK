import time


class VisualTrackingController:

    def __init__(self):

        self.active = False

        self.center_pwm = 1500

        self.roll_gain = 1.2
        self.pitch_gain = 0.8

        self.roll_deadband = 12
        self.pitch_deadband = 15

        self.min_roll_pwm = 1300
        self.max_roll_pwm = 1700

        self.min_pitch_pwm = 1200
        self.max_pitch_pwm = 1800

        self.command_interval = 0.12

        self.last_command_time = 0.0

    def start(self):

        self.active = True

        self.last_command_time = 0.0

    def stop(self):

        self.active = False

    def calculate_commands(
        self,
        bbox,
        image_width,
        image_height
    ):

        x1, y1, x2, y2 = bbox

        target_x = (
            x1 + x2
        ) / 2.0

        target_y = (
            y1 + y2
        ) / 2.0

        center_x = (
            image_width / 2.0
        )

        center_y = (
            image_height / 2.0
        )

        error_x = (
            target_x - center_x
        )

        error_y = (
            target_y - center_y
        )

        if abs(error_x) <= self.roll_deadband:

            roll_pwm = (
                self.center_pwm
            )

        else:

            roll_pwm = int(
                self.center_pwm
                + error_x
                * self.roll_gain
            )

        if abs(error_y) <= self.pitch_deadband:

            pitch_pwm = (
                self.center_pwm
            )

        else:

            pitch_pwm = int(
                self.center_pwm
                + error_y
                * self.pitch_gain
            )

        roll_pwm = max(
            self.min_roll_pwm,
            min(
                self.max_roll_pwm,
                roll_pwm
            )
        )

        pitch_pwm = max(
            self.min_pitch_pwm,
            min(
                self.max_pitch_pwm,
                pitch_pwm
            )
        )

        return (
            roll_pwm,
            pitch_pwm,
            error_x,
            error_y
        )

    def should_send(self):

        current_time = (
            time.monotonic()
        )

        if (
            current_time
            - self.last_command_time
            < self.command_interval
        ):

            return False

        self.last_command_time = (
            current_time
        )

        return True