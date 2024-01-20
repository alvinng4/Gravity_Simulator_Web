import math


class Settings:
    """A class to store all settings for gravity simulator."""

    DEFAULT_RESOLUTION = (1920, 1080)
    DEFAULT_STAR_IMG_SCALE = 5000
    DEFAULT_PLANET_IMG_SCALE = 100000
    DEFAULT_DISTANCE_SCALE = 200
    DEFAULT_dt = 0.1
    DEFAULT_TIME_SPEED = 1
    DEFAULT_EPSILON = 1e-2
    DEFAULT_NEW_STAR_MASS = 1
    MAX_FPS = 60
    BG_COLOR = (0, 0, 0)  # Background color

    DEFAULT_CHANGE_STAR_IMG_SCALE_SPEED = 500
    DEFAULT_CHANGE_PLANET_IMG_SCALE_SPEED = 10000
    DEFAULT_CHANGE_DISTANCE_SCALE_SPEED = 10

    DEFAULT_NEW_STAR_VELOCITY_SCALE = 0.0001
    MAX_STAR_IMG_SCALE = 100000
    MIN_STAR_IMG_SCALE = 0
    MAX_PLANET_IMG_SCALE = 1000000
    MIN_PLANET_IMG_SCALE = 0
    MAX_DISTANCE_SCALE = 1000
    MIN_DISTANCE_SCALE = 0
    MAX_DT = 100
    MIN_DT = 1e-10
    MAX_TIME_SPEED = 10000
    MIN_TIME_SPEED = 1
    MAX_EPSILON = 1e2
    MIN_EPSILON = 1e-15
    MAX_NEW_STAR_MASS = 1e7
    MIN_NEW_STAR_MASS = 1e-3

    def __init__(
        self,
        screen_width: int,
        screen_height: int,
    ):
        # To change the default settings of screen_width and screen_height, go to _read_command_line_arg function in __main__.py
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.star_img_scale = self.DEFAULT_STAR_IMG_SCALE
        self.planet_img_scale = self.DEFAULT_PLANET_IMG_SCALE
        self.time_speed = self.DEFAULT_TIME_SPEED
        self.dt = self.DEFAULT_dt
        self.distance_scale = self.DEFAULT_DISTANCE_SCALE
        self.epsilon = self.DEFAULT_EPSILON
        self.new_star_mass = self.DEFAULT_NEW_STAR_MASS
        self.set_all_parameters_changing_false()
        self.current_changing_parameter = None
        self.is_hide_gui = False

    def scroll_change_parameters(self, magnitude):
        self._update_parameter_changing_speed(magnitude)
        match self.current_changing_parameter:
            case "star_img_scale":
                self.star_img_scale += (
                    self.DEFAULT_CHANGE_STAR_IMG_SCALE_SPEED * magnitude
                )
            case "planet_img_scale":
                self.planet_img_scale += (
                    self.DEFAULT_CHANGE_PLANET_IMG_SCALE_SPEED * magnitude
                )
            case "distance_scale":
                self.distance_scale += (
                    self.DEFAULT_CHANGE_DISTANCE_SCALE_SPEED * magnitude
                )
            case "dt":
                self.dt += self.change_dt_speed * magnitude
            case "time_speed":
                self.time_speed += self.change_time_speed_speed * magnitude
            case "epsilon":
                self.epsilon += self.change_epsilon_speed * magnitude
            case "new_star_mass":
                self.new_star_mass += self.change_new_star_mass_speed * magnitude

    def _update_parameter_changing_speed(self, magnitude):
        if magnitude > 0:
            match self.current_changing_parameter:
                case "dt":
                    if not (self.dt < self.MIN_DT or self.dt > self.MAX_DT):
                        if self.dt != self.round_up_base_10(self.dt):
                            if self.dt + (
                                self.round_up_base_10(self.dt) / 10.0
                            ) * magnitude > self.round_up_base_10(self.dt):
                                self.change_dt_speed = (
                                    self.round_up_base_10(self.dt) - self.dt
                                ) / magnitude
                            else:
                                self.change_dt_speed = (
                                    self.round_up_base_10(self.dt) / 10
                                )
                        else:
                            if magnitude > 10:
                                self.change_dt_speed = self.round_up_base_10(
                                    self.dt
                                ) * (10 / magnitude)
                            else:
                                self.change_dt_speed = self.round_up_base_10(self.dt)
                case "time_speed":
                    if self.time_speed < 10:
                        if self.time_speed + 1 * magnitude > 10:
                            self.change_time_speed_speed = (
                                10 - self.time_speed
                            ) / magnitude
                        else:
                            self.change_time_speed_speed = 1
                    elif 10 <= self.time_speed < 100:
                        if self.time_speed + 5 * magnitude > 100:
                            self.change_time_speed_speed = (
                                100 - self.time_speed
                            ) / magnitude
                        else:
                            self.change_time_speed_speed = 5
                    elif 100 <= self.time_speed < 1000:
                        if self.time_speed + 10 * magnitude > 1000:
                            self.change_time_speed_speed = (
                                1000 - self.time_speed
                            ) / magnitude
                        else:
                            self.change_time_speed_speed = 10
                    else:
                        self.change_time_speed_speed = 50
                case "epsilon":
                    if not (self.epsilon < self.MIN_EPSILON or self.epsilon > self.MAX_EPSILON):
                        if self.epsilon != self.round_up_base_10(self.epsilon):
                            if self.epsilon + (
                                self.round_up_base_10(self.epsilon) / 10.0
                            ) * magnitude > self.round_up_base_10(self.epsilon):
                                self.change_epsilon_speed = (
                                    self.round_up_base_10(self.epsilon) - self.epsilon
                                ) / magnitude
                            else:
                                self.change_epsilon_speed = (
                                    self.round_up_base_10(self.epsilon) / 10
                                )
                        else:
                            if magnitude > 10:
                                self.change_epsilon_speed = self.round_up_base_10(
                                    self.epsilon
                                ) * (10 / magnitude)
                            else:
                                self.change_epsilon_speed = self.round_up_base_10(self.epsilon)
                case "new_star_mass":
                    if not (self.new_star_mass < self.MIN_NEW_STAR_MASS or self.new_star_mass > self.MAX_NEW_STAR_MASS):
                        if self.new_star_mass != self.round_up_base_10(self.new_star_mass):
                            if self.new_star_mass + (
                                self.round_up_base_10(self.new_star_mass) / 10.0
                            ) * magnitude > self.round_up_base_10(self.new_star_mass):
                                self.change_new_star_mass_speed = (
                                    self.round_up_base_10(self.new_star_mass) - self.new_star_mass
                                ) / magnitude
                            else:
                                self.change_new_star_mass_speed = (
                                    self.round_up_base_10(self.new_star_mass) / 10
                                )
                        else:
                            if magnitude > 10:
                                self.change_new_star_mass_speed = self.round_up_base_10(
                                    self.new_star_mass
                                ) * (10 / magnitude)
                            else:
                                self.change_new_star_mass_speed = self.round_up_base_10(self.new_star_mass)

        elif magnitude < 0:
            match self.current_changing_parameter:
                case "dt":
                    if not (self.dt < self.MIN_DT or self.dt > self.MAX_DT):
                        if self.dt != self.round_up_base_10(self.dt):
                            if (
                                self.dt
                                + (self.round_up_base_10(self.dt) / 10) * magnitude
                                < self.round_up_base_10(self.dt) / 10
                            ):
                                self.change_dt_speed = (
                                    self.dt - self.round_up_base_10(self.dt) / 10
                                ) / -magnitude
                            else:
                                self.change_dt_speed = (
                                    self.round_up_base_10(self.dt) / 10
                                )
                        else:
                            if -magnitude >= 10:
                                self.change_dt_speed = (
                                    self.round_up_base_10(self.dt)
                                    * (9 / 10)
                                    / -magnitude
                                )
                            else:
                                self.change_dt_speed = (
                                    self.round_up_base_10(self.dt) / 10
                                )
                case "time_speed":
                    if self.time_speed <= 10:
                        self.change_time_speed_speed = 1
                    elif 10 < self.time_speed < 15:
                        self.change_time_speed_speed = (self.time_speed - 5) / (
                            -magnitude
                        )
                    elif 15 <= self.time_speed <= 100:
                        self.change_time_speed_speed = 5
                    elif 100 < self.time_speed < 110:
                        self.change_time_speed_speed = (self.time_speed - 100) / (
                            -magnitude
                        )
                    elif 110 <= self.time_speed <= 1000:
                        self.change_time_speed_speed = 10
                    elif 1000 < self.time_speed < 1050:
                        self.change_time_speed_speed = (self.time_speed - 1050) / (
                            -magnitude
                        )
                    else:
                        self.change_time_speed_speed = 50
                case "epsilon":
                    if not (self.epsilon < self.MIN_EPSILON or self.epsilon > self.MAX_EPSILON):
                        if self.epsilon != self.round_up_base_10(self.epsilon):
                            if (
                                self.epsilon
                                + (self.round_up_base_10(self.epsilon) / 10) * magnitude
                                < self.round_up_base_10(self.epsilon) / 10
                            ):
                                self.change_epsilon_speed = (
                                    self.epsilon - self.round_up_base_10(self.epsilon) / 10
                                ) / -magnitude
                            else:
                                self.change_epsilon_speed = (
                                    self.round_up_base_10(self.epsilon) / 10
                                )
                        else:
                            if -magnitude >= 10:
                                self.change_epsilon_speed = (
                                    self.round_up_base_10(self.epsilon)
                                    * (9 / 10)
                                    / -magnitude
                                )
                            else:
                                self.change_epsilon_speed = (
                                    self.round_up_base_10(self.epsilon) / 10
                                )
                case "new_star_mass":
                    if not (self.new_star_mass < self.MIN_NEW_STAR_MASS or self.new_star_mass > self.MAX_NEW_STAR_MASS):
                        if self.new_star_mass != self.round_up_base_10(self.new_star_mass):
                            if (
                                self.new_star_mass
                                + (self.round_up_base_10(self.new_star_mass) / 10) * magnitude
                                < self.round_up_base_10(self.new_star_mass) / 10
                            ):
                                self.change_new_star_mass_speed = (
                                    self.new_star_mass - self.round_up_base_10(self.new_star_mass) / 10
                                ) / -magnitude
                            else:
                                self.change_new_star_mass_speed = (
                                    self.round_up_base_10(self.new_star_mass) / 10
                                )
                        else:
                            if -magnitude >= 10:
                                self.change_new_star_mass_speed = (
                                    self.round_up_base_10(self.new_star_mass)
                                    * (9 / 10)
                                    / -magnitude
                                )
                            else:
                                self.change_new_star_mass_speed = (
                                    self.round_up_base_10(self.new_star_mass) / 10
                                )

    @staticmethod
    def round_up_base_10(x: float) -> float:
        if x <= 0:
            return 0
        else:
            return 10 ** math.ceil(math.log10(x))

    def check_current_changing_parameter(self):
        if self.is_changing_star_img_scale == True:
            self.current_changing_parameter = "star_img_scale"
        elif self.is_changing_planet_img_scale == True:
            self.current_changing_parameter = "planet_img_scale"
        elif self.is_changing_distance_scale == True:
            self.current_changing_parameter = "distance_scale"
        elif self.is_changing_dt == True:
            self.current_changing_parameter = "dt"
        elif self.is_changing_time_speed == True:
            self.current_changing_parameter = "time_speed"
        elif self.is_changing_epsilon == True:
            self.current_changing_parameter = "epsilon"
        elif self.is_changing_new_star_mass == True:
            self.current_changing_parameter = "new_star_mass"

    def set_all_parameters_changing_false(self):
        self.is_changing_star_img_scale = False
        self.is_changing_planet_img_scale = False
        self.is_changing_distance_scale = False
        self.is_changing_dt = False
        self.is_changing_time_speed = False
        self.is_changing_epsilon = False 
        self.is_changing_new_star_mass = False

    def reset_parameters(self):
        self.star_img_scale = self.DEFAULT_STAR_IMG_SCALE
        self.planet_img_scale = self.DEFAULT_PLANET_IMG_SCALE
        self.time_speed = self.DEFAULT_TIME_SPEED
        self.dt = self.DEFAULT_dt
        self.distance_scale = self.DEFAULT_DISTANCE_SCALE
        self.epsilon = self.DEFAULT_EPSILON
        self.new_star_mass = self.DEFAULT_NEW_STAR_MASS

    @property
    def screen_width(self):
        return self._screen_width

    @property
    def screen_height(self):
        return self._screen_height

    @property
    def star_img_scale(self):
        return self._star_img_scale

    @property
    def planet_img_scale(self):
        return self._planet_img_scale

    @property
    def distance_scale(self):
        return self._distance_scale

    @property
    def dt(self):
        return self._dt

    @property
    def time_speed(self):
        return self._time_speed
    
    @property
    def epsilon(self):
        return self._epsilon
    
    @property
    def new_star_mass(self):
        return self._new_star_mass

    @screen_width.setter
    def screen_width(self, value):
        if value < 0:
            self._screen_width = 0
        else:
            self._screen_width = value

    @screen_height.setter
    def screen_height(self, value):
        if value < 0:
            self._screen_height = 0
        else:
            self._screen_height = value

    # Img may corrupt if the scale is too large.
    @star_img_scale.setter
    def star_img_scale(self, value):
        if value > self.MAX_STAR_IMG_SCALE:
            self._star_img_scale = self.MAX_STAR_IMG_SCALE
        elif value < self.MIN_STAR_IMG_SCALE:
            self._star_img_scale = self.MIN_STAR_IMG_SCALE
        else:
            self._star_img_scale = value

    # Img may corrupt if the scale is too large.
    @planet_img_scale.setter
    def planet_img_scale(self, value):
        if value > self.MAX_PLANET_IMG_SCALE:
            self._planet_img_scale = self.MAX_PLANET_IMG_SCALE
        elif value < self.MIN_PLANET_IMG_SCALE:
            self._planet_img_scale = self.MIN_PLANET_IMG_SCALE
        else:
            self._planet_img_scale = value

    @distance_scale.setter
    def distance_scale(self, value):
        if value > self.MAX_DISTANCE_SCALE:
            self._distance_scale = self.MAX_DISTANCE_SCALE
        elif value <= self.MIN_DISTANCE_SCALE:
            self._distance_scale = self.MIN_DISTANCE_SCALE
        else:
            self._distance_scale = value

    @dt.setter
    def dt(self, value):
        if value > self.MAX_DT:
            self._dt = self.MAX_DT
        elif value < self.MIN_DT:
            self._dt = self.MIN_DT
        else:
            self._dt = round(value, ndigits=16)

    @time_speed.setter
    def time_speed(self, value):
        if value > self.MAX_TIME_SPEED:
            self._time_speed = self.MAX_TIME_SPEED
        elif value < self.MIN_TIME_SPEED:
            self._time_speed = self.MIN_TIME_SPEED
        else:
            self._time_speed = int(value)

    @epsilon.setter
    def epsilon(self, value):
        if value > self.MAX_EPSILON:
            self._epsilon = self.MAX_EPSILON
        elif value < self.MIN_EPSILON:
            self._epsilon = self.MIN_EPSILON
        else:
            self._epsilon = round(value, ndigits=16)

    @new_star_mass.setter
    def new_star_mass(self, value):
        if value > self.MAX_NEW_STAR_MASS:
            self._new_star_mass = self.MAX_NEW_STAR_MASS
        elif value < self.MIN_NEW_STAR_MASS:
            self._new_star_mass = self.MIN_NEW_STAR_MASS
        else:
            self._new_star_mass = round(value, ndigits=16)