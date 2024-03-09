import os
import sys

import pygame
from pygame.sprite import Sprite

from settings import Settings


class Grav_obj(Sprite):
    # Conversion factor from km^3 s^-2 to AU^3 d^-2
    CONVERSION_FACTOR = (86400**2) / (149597870.7**3)
    # GM values (km^3 s^-2)
    # ref: https://ssd.jpl.nasa.gov/doc/Park.2021.AJ.DE440.pdf
    GM_SI = {
        "Sun": 132712440041.279419,
        "Mercury": 22031.868551,
        "Venus": 324858.592000,
        "Earth": 398600.435507,
        "Mars": 42828.375816,
        "Jupiter": 126712764.100000,
        "Saturn": 37940584.841800,
        "Uranus": 5794556.400000,
        "Neptune": 6836527.100580,
        "Moon": 4902.800118,
        "Pluto": 975.500000,
        "Ceres": 62.62890,
        "Vesta": 17.288245,
    }
    # GM values (AU^3 d^-2)
    GM = {
        "Sun": 132712440041.279419 * CONVERSION_FACTOR,
        "Mercury": 22031.868551 * CONVERSION_FACTOR,
        "Venus": 324858.592000 * CONVERSION_FACTOR,
        "Earth": 398600.435507 * CONVERSION_FACTOR,
        "Mars": 42828.375816 * CONVERSION_FACTOR,
        "Jupiter": 126712764.100000 * CONVERSION_FACTOR,
        "Saturn": 37940584.841800 * CONVERSION_FACTOR,
        "Uranus": 5794556.400000 * CONVERSION_FACTOR,
        "Neptune": 6836527.100580 * CONVERSION_FACTOR,
        "Moon": 4902.800118 * CONVERSION_FACTOR,
        "Pluto": 975.500000 * CONVERSION_FACTOR,
        "Ceres": 62.62890 * CONVERSION_FACTOR,
        "Vesta": 17.288245 * CONVERSION_FACTOR,
    }
    # Solar system masses (M_sun^-1)
    SOLAR_SYSTEM_MASSES = {
        "Sun": 1.0,
        "Mercury": GM_SI["Mercury"] / GM_SI["Sun"],
        "Venus": GM_SI["Venus"] / GM_SI["Sun"],
        "Earth": GM_SI["Earth"] / GM_SI["Sun"],
        "Mars": GM_SI["Mars"] / GM_SI["Sun"],
        "Jupiter": GM_SI["Jupiter"] / GM_SI["Sun"],
        "Saturn": GM_SI["Saturn"] / GM_SI["Sun"],
        "Uranus": GM_SI["Uranus"] / GM_SI["Sun"],
        "Neptune": GM_SI["Neptune"] / GM_SI["Sun"],
        "Moon": GM_SI["Moon"] / GM_SI["Sun"],
        "Pluto": GM_SI["Pluto"] / GM_SI["Sun"],
        "Ceres": GM_SI["Ceres"] / GM_SI["Sun"],
        "Vesta": GM_SI["Vesta"] / GM_SI["Sun"],
    }
    # Gravitational constant (kg^-1 m^3 s^-2):
    G_SI = 6.67430e-11
    # Gravitational constant (M_sun^-1 AU^3 d^-2):
    G = GM["Sun"]

    # Solar system position and velocities data
    # Units: AU-D
    # Coordinate center: Solar System Barycenter
    # Data dated on A.D. 2024-Jan-01 00:00:00.0000 TDB
    # Computational data generated by NASA JPL Horizons System https://ssd.jpl.nasa.gov/horizons/
    SOLAR_SYSTEM_POS = {
        "Sun": [-7.967955691533730e-03, -2.906227441573178e-03, 2.103054301547123e-04],
        "Mercury": [
            -2.825983269538632e-01,
            1.974559795958082e-01,
            4.177433558063677e-02,
        ],
        "Venus": [
            -7.232103701666379e-01,
            -7.948302026312400e-02,
            4.042871428174315e-02,
        ],
        "Earth": [-1.738192017257054e-01, 9.663245550235138e-01, 1.553901854897183e-04],
        "Mars": [-3.013262392582653e-01, -1.454029331393295e00, -2.300531433991428e-02],
        "Jupiter": [3.485202469657674e00, 3.552136904413157e00, -9.271035442798399e-02],
        "Saturn": [8.988104223143450e00, -3.719064854634689e00, -2.931937777323593e-01],
        "Uranus": [1.226302417897505e01, 1.529738792480545e01, -1.020549026883563e-01],
        "Neptune": [
            2.983501460984741e01,
            -1.793812957956852e00,
            -6.506401132254588e-01,
        ],
        "Moon": [-1.762788124769829e-01, 9.674377513177153e-01, 3.236901585768862e-04],
        "Pluto": [1.720200478843485e01, -3.034155683573043e01, -1.729127607100611e00],
        "Ceres": [-1.103880510367569e00, -2.533340440444230e00, 1.220283937721780e-01],
        "Vesta": [-8.092549658731499e-02, 2.558381434460076e00, -6.695836142398572e-02],
    }
    SOLAR_SYSTEM_VEL = {
        "Sun": [4.875094764261564e-06, -7.057133213976680e-06, -4.573453713094512e-08],
        "Mercury": [
            -2.232165900189702e-02,
            -2.157207103176252e-02,
            2.855193410495743e-04,
        ],
        "Venus": [
            2.034068201002341e-03,
            -2.020828626592994e-02,
            -3.945639843855159e-04,
        ],
        "Earth": [
            -1.723001232538228e-02,
            -2.967721342618870e-03,
            6.382125383116755e-07,
        ],
        "Mars": [1.424832259345280e-02, -1.579236181580905e-03, -3.823722796161561e-04],
        "Jupiter": [
            -5.470970658852281e-03,
            5.642487338479145e-03,
            9.896190602066252e-05,
        ],
        "Saturn": [
            1.822013845554067e-03,
            5.143470425888054e-03,
            -1.617235904887937e-04,
        ],
        "Uranus": [
            -3.097615358317413e-03,
            2.276781932345769e-03,
            4.860433222241686e-05,
        ],
        "Neptune": [
            1.676536611817232e-04,
            3.152098732861913e-03,
            -6.877501095688201e-05,
        ],
        "Moon": [
            -1.746667306153906e-02,
            -3.473438277358121e-03,
            -3.359028758606074e-05,
        ],
        "Pluto": [2.802810313667557e-03, 8.492056438614633e-04, -9.060790113327894e-04],
        "Ceres": [
            8.978653480111301e-03,
            -4.873256528198994e-03,
            -1.807162046049230e-03,
        ],
        "Vesta": [
            -1.017876585480054e-02,
            -5.452367109338154e-04,
            1.255870551153315e-03,
        ],
    }
    # Solar radius (AU)
    SOLAR_RADIUS = 0.004650467261

    def __init__(
        self,
        grav_sim,
        params: dict,
        img_path: str = None,
        name: str = None,
    ):
        super().__init__()
        self.screen = grav_sim.screen
        self.screen_rect = self.screen.get_rect()
        self.camera = grav_sim.camera
        self.settings = grav_sim.settings
        self.params = params
        self.diameter = 2 * self.params["R"]
        if name == "Sun":
            self.img_diameter = self.diameter * self.settings.star_img_scale
        else:
            self.img_diameter = self.diameter * self.settings.planet_img_scale

        if img_path:
            try:
                load_image = pygame.image.load(img_path).convert_alpha()
                self.image = pygame.transform.scale(
                    load_image, (self.img_diameter, self.img_diameter)
                )
                self.rect = self.image.get_rect()
            except FileNotFoundError:
                sys.exit(
                    "Error: Image not found. Make sure the image path provided for Grav_obj is correct."
                )
                
    def update(self, gravity_sim):
        self.remove_out_of_range_objs(gravity_sim)
        self.update_apparent_pos()

    def remove_out_of_range_objs(self, gravity_sim):
        """Remove object when position is out of range"""
        if abs(self.params["r1"]) > self.settings.MAX_RANGE or abs(self.params["r2"]) > self.settings.MAX_RANGE or abs(self.params["r3"]) > self.settings.MAX_RANGE:
            self.kill()
            print("System message: Out of range object removed.")
            gravity_sim.simulator.is_initialize = True        

    def update_apparent_pos(self):
        """Update the apparent position of all grav_objs with camera"""
        self.rect.center = (
            self.params["r1"] * self.settings.distance_scale
            + self.screen_rect.centerx
            - self.camera.pos[0],
            -self.params["r2"] * self.settings.distance_scale
            + self.screen_rect.centery
            - self.camera.pos[1],
        )

    def create_star(grav_sim, mouse_pos, camera_pos, drag_mouse_pos, drag_camera_pos):
        main_dir_path = os.path.dirname(__file__)
        path_sun = os.path.join(main_dir_path, "assets/images/sun.png")
        m = (
            1
            * 0.5
            * grav_sim.stats.holding_rclick_time
            * grav_sim.settings.new_star_mass_scale
        )
        R = Grav_obj.SOLAR_RADIUS * (m ** (1.0 / 3.0))
        new_star_r1 = (mouse_pos[0] - grav_sim.screen.get_rect().centerx + camera_pos[0]) / grav_sim.settings.distance_scale
        new_star_r2 = -(mouse_pos[1] - grav_sim.screen.get_rect().centery + camera_pos[1])/ grav_sim.settings.distance_scale
        new_star_r3 = 0.0

        # Check if two objects has the exact same position, which would causes error
        flag = True 
        for grav_obj in grav_sim.grav_objs:
            if new_star_r1 == grav_obj.params["r1"] and new_star_r2 == grav_obj.params["r2"] and new_star_r3 == grav_obj.params["r3"]:
                flag = False

        if flag == True:
            grav_obj = Grav_obj(
                grav_sim,
                {
                    "r1": new_star_r1,
                    "r2": new_star_r2,
                    "r3": new_star_r3,
                    "v1": -(
                        (drag_mouse_pos[0] - mouse_pos[0])
                        + (drag_camera_pos[0] - camera_pos[0])
                    )
                    * Settings.DEFAULT_NEW_STAR_VELOCITY_SCALE,
                    "v2": (
                        (drag_mouse_pos[1] - mouse_pos[1])
                        + (drag_camera_pos[1] - camera_pos[1])
                    )
                    * Settings.DEFAULT_NEW_STAR_VELOCITY_SCALE,
                    "v3": 0.0,
                    "m": m,
                    "R": R,
                },
                path_sun,
                name="Sun",
            )
            grav_sim.grav_objs.add(grav_obj)
            grav_sim.simulator.is_initialize = True
            grav_sim.simulator.is_initialize_integrator = (
                grav_sim.simulator.current_integrator
            )

    @staticmethod
    def create_solor_system(grav_sim):
        """
        Create the solar system
        Data dated on A.D. 2024-Jan-01 00:00:00.0000 TDB
        Computational data generated by NASA JPL Horizons System https://ssd.jpl.nasa.gov/horizons/
        """
        main_dir_path = os.path.dirname(__file__)
        path_sun = os.path.join(main_dir_path, "assets/images/sun.png")
        path_mercury = os.path.join(main_dir_path, "assets/images/mercury.png")
        path_venus = os.path.join(main_dir_path, "assets/images/venus.png")
        path_earth = os.path.join(main_dir_path, "assets/images/earth.png")
        path_mars = os.path.join(main_dir_path, "assets/images/mars.png")
        path_jupiter = os.path.join(main_dir_path, "assets/images/jupiter.png")
        path_saturn = os.path.join(main_dir_path, "assets/images/saturn.png")
        path_uranus = os.path.join(main_dir_path, "assets/images/uranus.png")
        path_neptune = os.path.join(main_dir_path, "assets/images/neptune.png")
        # r1 - r3: Positions (AU), v1 - v3: Velocities (AU/d), m: Mass (Solar masses)
        sun = Grav_obj(
            grav_sim,
            {
                "r1": Grav_obj.SOLAR_SYSTEM_POS["Sun"][0],
                "r2": Grav_obj.SOLAR_SYSTEM_POS["Sun"][1],
                "r3": Grav_obj.SOLAR_SYSTEM_POS["Sun"][2],
                "v1": Grav_obj.SOLAR_SYSTEM_VEL["Sun"][0],
                "v2": Grav_obj.SOLAR_SYSTEM_VEL["Sun"][1],
                "v3": Grav_obj.SOLAR_SYSTEM_VEL["Sun"][2],
                "m": Grav_obj.SOLAR_SYSTEM_MASSES["Sun"],
                "R": Grav_obj.SOLAR_RADIUS,
            },
            path_sun,
            name="Sun",
        )
        mercury = Grav_obj(
            grav_sim,
            {
                "r1": Grav_obj.SOLAR_SYSTEM_POS["Mercury"][0],
                "r2": Grav_obj.SOLAR_SYSTEM_POS["Mercury"][1],
                "r3": Grav_obj.SOLAR_SYSTEM_POS["Mercury"][2],
                "v1": Grav_obj.SOLAR_SYSTEM_VEL["Mercury"][0],
                "v2": Grav_obj.SOLAR_SYSTEM_VEL["Mercury"][1],
                "v3": Grav_obj.SOLAR_SYSTEM_VEL["Mercury"][2],
                "m": Grav_obj.SOLAR_SYSTEM_MASSES["Mercury"],
                "R": 1.63083872e-05,
            },
            path_mercury,
        )
        venus = Grav_obj(
            grav_sim,
            {
                "r1": Grav_obj.SOLAR_SYSTEM_POS["Venus"][0],
                "r2": Grav_obj.SOLAR_SYSTEM_POS["Venus"][1],
                "r3": Grav_obj.SOLAR_SYSTEM_POS["Venus"][2],
                "v1": Grav_obj.SOLAR_SYSTEM_VEL["Venus"][0],
                "v2": Grav_obj.SOLAR_SYSTEM_VEL["Venus"][1],
                "v3": Grav_obj.SOLAR_SYSTEM_VEL["Venus"][2],
                "m": Grav_obj.SOLAR_SYSTEM_MASSES["Venus"],
                "R": 4.04537843e-05,
            },
            path_venus,
        )
        earth = Grav_obj(
            grav_sim,
            {
                "r1": Grav_obj.SOLAR_SYSTEM_POS["Earth"][0],
                "r2": Grav_obj.SOLAR_SYSTEM_POS["Earth"][1],
                "r3": Grav_obj.SOLAR_SYSTEM_POS["Earth"][2],
                "v1": Grav_obj.SOLAR_SYSTEM_VEL["Earth"][0],
                "v2": Grav_obj.SOLAR_SYSTEM_VEL["Earth"][1],
                "v3": Grav_obj.SOLAR_SYSTEM_VEL["Earth"][2],
                "m": Grav_obj.SOLAR_SYSTEM_MASSES["Earth"],
                "R": 4.25875046e-05,
            },
            path_earth,
        )
        mars = Grav_obj(
            grav_sim,
            {
                "r1": Grav_obj.SOLAR_SYSTEM_POS["Mars"][0],
                "r2": Grav_obj.SOLAR_SYSTEM_POS["Mars"][1],
                "r3": Grav_obj.SOLAR_SYSTEM_POS["Mars"][2],
                "v1": Grav_obj.SOLAR_SYSTEM_VEL["Mars"][0],
                "v2": Grav_obj.SOLAR_SYSTEM_VEL["Mars"][1],
                "v3": Grav_obj.SOLAR_SYSTEM_VEL["Mars"][2],
                "m": Grav_obj.SOLAR_SYSTEM_MASSES["Mars"],
                "R": 2.26574081e-05,
            },
            path_mars,
        )
        jupiter = Grav_obj(
            grav_sim,
            {
                "r1": Grav_obj.SOLAR_SYSTEM_POS["Jupiter"][0],
                "r2": Grav_obj.SOLAR_SYSTEM_POS["Jupiter"][1],
                "r3": Grav_obj.SOLAR_SYSTEM_POS["Jupiter"][2],
                "v1": Grav_obj.SOLAR_SYSTEM_VEL["Jupiter"][0],
                "v2": Grav_obj.SOLAR_SYSTEM_VEL["Jupiter"][1],
                "v3": Grav_obj.SOLAR_SYSTEM_VEL["Jupiter"][2],
                "m": Grav_obj.SOLAR_SYSTEM_MASSES["Jupiter"],
                "R": 4.6732617e-04,
            },
            path_jupiter,
        )
        saturn = Grav_obj(
            grav_sim,
            {
                "r1": Grav_obj.SOLAR_SYSTEM_POS["Saturn"][0],
                "r2": Grav_obj.SOLAR_SYSTEM_POS["Saturn"][1],
                "r3": Grav_obj.SOLAR_SYSTEM_POS["Saturn"][2],
                "v1": Grav_obj.SOLAR_SYSTEM_VEL["Saturn"][0],
                "v2": Grav_obj.SOLAR_SYSTEM_VEL["Saturn"][1],
                "v3": Grav_obj.SOLAR_SYSTEM_VEL["Saturn"][2],
                "m": Grav_obj.SOLAR_SYSTEM_MASSES["Saturn"],
                "R": 3.89256877e-04 * (157 / 57),  # Img scale for Saturn's ring
            },
            path_saturn,
        )
        uranus = Grav_obj(
            grav_sim,
            {
                "r1": Grav_obj.SOLAR_SYSTEM_POS["Uranus"][0],
                "r2": Grav_obj.SOLAR_SYSTEM_POS["Uranus"][1],
                "r3": Grav_obj.SOLAR_SYSTEM_POS["Uranus"][2],
                "v1": Grav_obj.SOLAR_SYSTEM_VEL["Uranus"][0],
                "v2": Grav_obj.SOLAR_SYSTEM_VEL["Uranus"][1],
                "v3": Grav_obj.SOLAR_SYSTEM_VEL["Uranus"][2],
                "m": Grav_obj.SOLAR_SYSTEM_MASSES["Uranus"],
                "R": 1.69534499e-04,
            },
            path_uranus,
        )
        neptune = Grav_obj(
            grav_sim,
            {
                "r1": Grav_obj.SOLAR_SYSTEM_POS["Neptune"][0],
                "r2": Grav_obj.SOLAR_SYSTEM_POS["Neptune"][1],
                "r3": Grav_obj.SOLAR_SYSTEM_POS["Neptune"][2],
                "v1": Grav_obj.SOLAR_SYSTEM_VEL["Neptune"][0],
                "v2": Grav_obj.SOLAR_SYSTEM_VEL["Neptune"][1],
                "v3": Grav_obj.SOLAR_SYSTEM_VEL["Neptune"][2],
                "m": Grav_obj.SOLAR_SYSTEM_MASSES["Neptune"],
                "R": 1.64587904e-04,
            },
            path_neptune,
        )
        grav_sim.grav_objs.add(sun)
        grav_sim.grav_objs.add(mercury)
        grav_sim.grav_objs.add(venus)
        grav_sim.grav_objs.add(earth)
        grav_sim.grav_objs.add(mars)
        grav_sim.grav_objs.add(jupiter)
        grav_sim.grav_objs.add(saturn)
        grav_sim.grav_objs.add(uranus)
        grav_sim.grav_objs.add(neptune)

    @staticmethod
    def create_figure_8(grav_sim):
        """
        Create a figure-8 orbit
        Data from the book Moving Planets Around: An Introduction to
        N-Body Simulations Applied to Exoplanetary Systems, Ch.7, Page 109
        As the data given use G = 1, the mass is converted by m / G, since a = GM/r^2.
        """
        # Currently use sun as object. May or may not change later.
        main_dir_path = os.path.dirname(__file__)
        path_sun = os.path.join(main_dir_path, "assets/images/sun.png")
        object_1 = Grav_obj(
            grav_sim,
            {
                "r1": 0.970043,
                "r2": -0.24308753,
                "r3": 0.0,
                "v1": 0.466203685,
                "v2": 0.43236573,
                "v3": 0.0,
                "m": 1.0 / Grav_obj.G,
                "R": Grav_obj.SOLAR_RADIUS,  # The radius is arbitrary. Here we give it the solar radii as it have 1 solar mass
            },
            path_sun,
            name="Sun",
        )
        object_2 = Grav_obj(
            grav_sim,
            {
                "r1": -0.970043,
                "r2": 0.24308753,
                "r3": 0.0,
                "v1": 0.466203685,
                "v2": 0.43236573,
                "v3": 0.0,
                "m": 1.0 / Grav_obj.G,
                "R": Grav_obj.SOLAR_RADIUS,  # The radius is arbitrary. Here we give it the solar radii as it have 1 solar mass
            },
            path_sun,
            name="Sun",
        )
        object_3 = Grav_obj(
            grav_sim,
            {
                "r1": 0.0,
                "r2": 0.0,
                "r3": 0.0,
                "v1": -0.93240737,
                "v2": -0.86473146,
                "v3": 0.0,
                "m": 1.0 / Grav_obj.G,
                "R": Grav_obj.SOLAR_RADIUS,  # The radius is arbitrary. Here we give it the solar radii as it have 1 solar mass
            },
            path_sun,
            name="Sun",
        )
        grav_sim.grav_objs.add(object_1)
        grav_sim.grav_objs.add(object_2)
        grav_sim.grav_objs.add(object_3)

    @staticmethod
    def create_pyth_3_body(grav_sim):
        """
        Create a Pythagorean three-body orbit
        Data from the book Moving Planets Around: An Introduction to
        N-Body Simulations Applied to Exoplanetary Systems, Ch.7, Page 109
        As the data given use G = 1, the mass is converted by m / G, since a = GM / r^2.
        """
        # Currently use sun as object. May or may not change later.
        main_dir_path = os.path.dirname(__file__)
        path_sun = os.path.join(main_dir_path, "assets/images/sun.png")
        object_1 = Grav_obj(
            grav_sim,
            {
                "r1": 1.0,
                "r2": 3.0,
                "r3": 0.0,
                "v1": 0.0,
                "v2": 0.0,
                "v3": 0.0,
                "m": 3.0 / Grav_obj.G,
                "R": Grav_obj.SOLAR_RADIUS,  # The radius is arbitrary. Here we give it the solar radii as it have 1 solar mass
            },
            path_sun,
            name="Sun",
        )
        object_2 = Grav_obj(
            grav_sim,
            {
                "r1": -2.0,
                "r2": -1.0,
                "r3": 0.0,
                "v1": 0.0,
                "v2": 0.0,
                "v3": 0.0,
                "m": 4.0 / Grav_obj.G,
                "R": Grav_obj.SOLAR_RADIUS,  # The radius is arbitrary. Here we give it the solar radii as it have 1 solar mass
            },
            path_sun,
            name="Sun",
        )
        object_3 = Grav_obj(
            grav_sim,
            {
                "r1": 1.0,
                "r2": -1.0,
                "r3": 0.0,
                "v1": 0.0,
                "v2": 0.0,
                "v3": 0.0,
                "m": 5.0 / Grav_obj.G,
                "R": Grav_obj.SOLAR_RADIUS,  # The radius is arbitrary. Here we give it the solar radii as it have 1 solar mass
            },
            path_sun,
            name="Sun",
        )
        grav_sim.grav_objs.add(object_1)
        grav_sim.grav_objs.add(object_2)
        grav_sim.grav_objs.add(object_3)
