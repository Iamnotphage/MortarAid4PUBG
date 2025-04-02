import math

class calculator:
    """
    This class calculates the distance setting of a mortar based on the elevation angle and horizontal distance.    
    It uses the formula derived from the physics of projectile motion.
    The maximum distance is set to 700 meters.
    """
    def __init__(self):
        self.scale_factor = 0.0
        self.horizontal_distance = 0.0 # horizontal distance to the target (max range)
        self.evelation_angle = 0.0 # evelation angle to the target (in degrees)
        self.result = 0 # distance setting of the mortar
        self.MAX_DISTANCE = 700 # maximum distance in mortar range
        self.MAX_DEGREE = 26.19 # maximum degree of elevation angle
        self.CENTER_PIXEL_Y = 719 # center of the screen in pixels (for 2160 x 1440 resolution)

    def set_scale_factor(self, point1, point2):
        """
        Sets the scale factor based on the distance between two points.
        """
        delta_x = point2[0] - point1[0]
        delta_y = point2[1] - point1[1]
        distance_in_pixels = (delta_x) ** 2 + (delta_y) ** 2
        
        self.scale_factor = 100.0 / math.sqrt(distance_in_pixels)

    
    def get_horizontal_distance(self, point1, point2):
        """
        Returns the horizontal distance to the target.
        """
        delta_x = point2[0] - point1[0]
        delta_y = point2[1] - point1[1]
        distance_in_pixels = (delta_x) ** 2 + (delta_y) ** 2
        distance_in_meters = distance_in_pixels * self.scale_factor * self.scale_factor

        self.horizontal_distance = math.sqrt(distance_in_meters)
        return self.horizontal_distance
    
    def get_evelation_angle(self, point):
        """
        Returns the elevation angle to the target.
        """
        
        # 0 degree is the center of the screen
        # self.MAX_DEGREE is the top of the screen

        # print(point)

        delta_y = self.CENTER_PIXEL_Y - point[1]

        angle_in_degrees = delta_y * self.MAX_DEGREE / self.CENTER_PIXEL_Y
        self.evelation_angle = angle_in_degrees
        return self.evelation_angle

    def solve(self, beta=0.0, L=0.0):
        """
        Returns the distance setting of the mortar based on the elevation angle and horizontal distance."
        """

        print(beta)
        print(L)

        # same horizontal distance
        if beta == 0:
            self.result = L
            return self.result
        
        # variables
        tan_beta = math.tan(math.radians(beta))
        M = self.MAX_DISTANCE

        delta = M ** 2 - 2 * L * M * tan_beta - L ** 2
        if delta < 0:
            print("No solution")
            self.result = -1
            return self.result

        intermediate = M - math.sqrt(M ** 2 - 2 * L * M * tan_beta - L ** 2)

        # calculate the distance
        self.result = (L + tan_beta * intermediate) / (tan_beta ** 2 + 1)

        return self.result