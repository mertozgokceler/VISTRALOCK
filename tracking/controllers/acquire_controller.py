import time


class AcquireController:

    def __init__(self):

        self.deadband = 5.0

        self.max_heading_error = 60.0

        self.center_pwm = 1500

        self.max_roll_delta = 250

        self.command_interval = 0.20

        self.last_command_time = 0.0
        self.last_pwm = None

        self.active = False

    def start(self):

        self.active = True

        self.last_pwm = None
        self.last_command_time = 0.0

    def stop(self):

        self.active = False

        self.last_pwm = None

    def calculate_roll_pwm(
        self,
        heading_error
    ):

        if not self.active:
            return None

        if abs(heading_error) <= self.deadband:
            return self.center_pwm

        normalized_error = min(
            abs(heading_error)
            / self.max_heading_error,
            1.0
        )

        roll_delta = int(
            normalized_error
            * self.max_roll_delta
        )

        if heading_error > 0:

            pwm = (
                self.center_pwm
                - roll_delta
            )

        else:

            pwm = (
                self.center_pwm
                + roll_delta
            )

        return pwm

    def should_send(
        self,
        pwm
    ):

        if pwm is None:
            return False

        current_time = time.monotonic()

        if (
            current_time
            - self.last_command_time
            < self.command_interval
        ):
            return False

        if (
            self.last_pwm is not None
            and abs(
                pwm - self.last_pwm
            ) < 10
        ):
            return False

        self.last_command_time = current_time
        self.last_pwm = pwm

        return True