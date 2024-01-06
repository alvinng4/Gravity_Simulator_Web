class Camera:
    def __init__(self):
        self.pos_x = 0
        self.pos_y = 0
        self.speed_x = 10
        self.speed_y = 10

        # Movement flag
        self.moving_right = False
        self.moving_left = False
        self.moving_up = False
        self.moving_down = False

    def pos(self):
        return (self.pos_x, self.pos_y)

    def speed_x(self):
        return self.speed_x

    def speed_y(self):
        return self.speed_y

    def update_movement(self):
        if self.moving_right == True:
            self.pos_x += self.speed_x
        if self.moving_left == True:
            self.pos_x -= self.speed_x
        if self.moving_up == True:
            self.pos_y -= self.speed_y
        if self.moving_down == True:
            self.pos_y += self.speed_y
