import asyncio
import ctypes
import math
from pathlib import Path
import platform
import sys
import time

import numpy as np 

import os

import pygame
import pygame.font
from pygame.sprite import Sprite

class GravitySimulator:
    """Overall class to manage the main program."""

    def __init__(self):
        """
        Initialize the main program.
        Initialization dependencies:
            settings: none
            menu: none
            camera: none
            stats: settings
            grav_objs: camera, settings
            simulator: stats, settings
        """
        # Use c library to perform simulation
        self.is_c_lib = True
        self.c_lib = ctypes.cdll.LoadLibrary(
                    str(Path(__file__).parent / "c_lib.dll")
                )
        self.c_lib = ctypes.cdll.LoadLibrary(
                        str(Path(__file__).parent / "c_lib.dylib")
                    )
        self.c_lib = ctypes.cdll.LoadLibrary(
                            str(Path(__file__).parent / "c_lib.so")
                        )
        if self.is_c_lib:
            try:
                print("System message: Trying to load c_lib.dll.")
                self.c_lib = ctypes.cdll.LoadLibrary(
                    str(Path(__file__).parent / "c_lib.dll")
                )
            except:
                print("System message: Loading c_lib.dll failed. Trying to load c_lib.dylib.")
                try:
                    self.c_lib = ctypes.cdll.LoadLibrary(
                        str(Path(__file__).parent / "c_lib.dylib")
                    )
                except:
                    print("System message: Loading c_lib.dylib failed. Trying to load c_lib.so.")
                    try:
                        self.c_lib = ctypes.cdll.LoadLibrary(
                            str(Path(__file__).parent / "c_lib.so")
                        )
                    except:
                        print("System message: Loading c_lib.so failed. Running with numpy.")
                        self.is_c_lib = False

        if self.is_c_lib:
            self.c_lib.compute_energy.restype = ctypes.c_double

        pygame.init()

        self.settings = Settings(
            pygame.display.Info().current_w,
            pygame.display.Info().current_h,
        )

        self.screen = pygame.display.set_mode(
            (self.settings.screen_width, self.settings.screen_height),
        )
        #pygame.display.set_caption("Gravity Simulator")
        self.clock = pygame.time.Clock()
        self.menu = Menu(self)
        self.camera = Camera()
        self.stats = Stats(self)
        self.grav_objs = pygame.sprite.Group()
        self.simulator = Simulator(self)

    async def run_prog(self):
        """The main loop for the program"""
        while True:
            self._check_events()
            self._update_events()
            self._simulation()
            self._check_energy_error()
            self._update_screen()
            self.clock.tick(self.settings.MAX_FPS)
            await asyncio.sleep(0)

    def _check_events(self):
        self.simulator.check_current_integrator()
        self.settings.check_current_changing_parameter()
        for event in pygame.event.get():
            match event.type:
                case pygame.KEYDOWN:
                    self._check_key_down_events(event)
                case pygame.KEYUP:
                    self._check_key_up_events(event)
                case pygame.MOUSEBUTTONDOWN:
                    self._check_mouse_button_down_events(event)
                case pygame.MOUSEBUTTONUP:
                    self._check_mouse_button_up_events(event)
                case pygame.MOUSEWHEEL:
                    self.settings.scroll_change_parameters(event.y)
                case pygame.QUIT:
                    sys.exit()

    def _update_events(self):
        self.camera.update_movement()
        self.grav_objs.update(self)
        self.stats.update(self)

    def _simulation(self):
        if self.grav_objs and not self.stats.is_paused:
            self.simulator.run_simulation(self)
            self.simulator.unload_value(self)

    def _check_energy_error(self):
        if math.isnan(self.stats.total_energy):
            self._kill_all_objects()
            print("System message: removed all objects due to infinity energy error.")
    
    def _kill_all_objects(self):
        for grav_obj in self.grav_objs:
            grav_obj.kill()

        self.stats.total_energy = 0.0
        self.simulator.is_initialize = True

    def _update_screen(self):
        self.screen.fill(Settings.BG_COLOR)
        self.grav_objs.draw(self.screen)
        if self.settings.is_hide_gui == False:
            self.stats.draw(self)
        if self.stats.is_holding_rclick == True:
            self._new_star_draw_line_circle()
        if self.menu.menu_active == True:
            self.menu.draw()
        pygame.display.flip()

    def _check_key_up_events(self, event):
        match event.key:
            case up if up in [pygame.K_w, pygame.K_UP]:
                self.camera.moving_up = False
            case left if left in [pygame.K_a, pygame.K_LEFT]:
                self.camera.moving_left = False
            case down if down in [pygame.K_s, pygame.K_DOWN]:
                self.camera.moving_down = False
            case right if right in [pygame.K_d, pygame.K_RIGHT]:
                self.camera.moving_right = False

    def _check_key_down_events(self, event):
        match event.key:
            case up if up in [pygame.K_w, pygame.K_UP]:
                self.camera.moving_up = True
            case left if left in [pygame.K_a, pygame.K_LEFT]:
                self.camera.moving_left = True
            case down if down in [pygame.K_s, pygame.K_DOWN]:
                self.camera.moving_down = True
            case right if right in [pygame.K_d, pygame.K_RIGHT]:
                self.camera.moving_right = True
            case pygame.K_p:
                if self.stats.is_paused == False:
                    self.stats.start_pause()
                elif self.stats.is_paused == True:
                    self.stats.end_pause()
            case pygame.K_f:
                pygame.display.toggle_fullscreen()
            case pygame.K_h:
                self.settings.is_hide_gui = not self.settings.is_hide_gui
            case pygame.K_r:
                self.settings.reset_parameters()
            case pygame.K_ESCAPE:
                if self.menu.main_menu_active == False:
                    self.menu.menu_active = not self.menu.menu_active

    def _check_mouse_button_down_events(self, event):
        if event.button == 1:  # left click
            mouse_pos = pygame.mouse.get_pos()
            self.stats.check_button(self, mouse_pos)
            if self.menu.menu_active == True:
                self.menu.check_button(self, mouse_pos)
        elif event.button == 3:  # right click
            if self.menu.menu_active == False:
                mouse_pos = pygame.mouse.get_pos()
                self.stats.start_holding_rclick()
                self.new_star_mouse_pos = mouse_pos
                self.new_star_camera_pos = self.camera.pos

    def _check_mouse_button_up_events(self, event):
        if event.button == 3:  # right click up
            if self.stats.is_holding_rclick == True:
                self.new_star_drag_mouse_pos = (
                    pygame.mouse.get_pos()
                )  # for object's velocity
                self.stats.end_holding_rclick()
                Grav_obj.create_star(
                    self,
                    self.new_star_mouse_pos,
                    self.new_star_camera_pos,
                    self.new_star_drag_mouse_pos,
                    self.camera.pos,
                )

    def _new_star_draw_line_circle(self):
        pygame.draw.line(
            self.screen,
            "white",
            (
                self.new_star_mouse_pos[0]
                + (self.new_star_camera_pos[0] - self.camera.pos[0]),
                self.new_star_mouse_pos[1]
                + (self.new_star_camera_pos[1] - self.camera.pos[1]),
            ),
            pygame.mouse.get_pos(),
        )
        m = 1 * 0.5 * self.stats.holding_rclick_time * self.settings.new_star_mass_scale
        R = Grav_obj.SOLAR_RADIUS * (m ** (1.0 / 3.0))
        img_R = (
            R
            * (699.0 / 894.0)  # Actual Sun size in images/sun.png with size (894 x 894)
            * self.settings.star_img_scale
        )
        new_star_circle_pos = [
            self.new_star_mouse_pos[0]
            + (self.new_star_camera_pos[0] - self.camera.pos[0]),
            self.new_star_mouse_pos[1]
            + (self.new_star_camera_pos[1] - self.camera.pos[1]),
        ]
        pygame.draw.circle(self.screen, "orange", new_star_circle_pos, img_R, width=1)

class Camera:
    def __init__(self):
        self._pos = [0, 0]
        self.speed = [10, 10]

        # Movement flag
        self.moving_right = False
        self.moving_left = False
        self.moving_up = False
        self.moving_down = False

    @property
    def pos(self):
        return tuple(self._pos)

    def update_movement(self):
        if self.moving_right == True:
            self._pos[0] += self.speed[0]
        if self.moving_left == True:
            self._pos[0] -= self.speed[0]
        if self.moving_up == True:
            self._pos[1] -= self.speed[1]
        if self.moving_down == True:
            self._pos[1] += self.speed[1]




class Text_box:
    """A class to build text boxes"""

    def __init__(
        self,
        grav_sim,
        font_size: int,
        size_factor_x: float = None,
        size_factor_y: float = None,
        size_x: int = None,
        size_y: int = None,
        font: str = None,
        msg: str = None,
        text_box_color: tuple = None,
        text_color: tuple = (255, 255, 255),
        center: tuple = None,
        text_box_left_top: tuple = (0, 0),
    ) -> None:
        """Initialize text box attributes."""
        self.screen = grav_sim.screen
        self.screen_rect = self.screen.get_rect()

        # Set the dimensions and properties of the text box.
        if size_factor_x != None:
            self.width = size_factor_x * grav_sim.settings.screen_width
        else:
            self.width = size_x
        if size_factor_y != None:
            self.height = size_factor_y * grav_sim.settings.screen_height
        else:
            self.height = size_y

        self.textbox_color = text_box_color
        self.text_color = text_color
        main_dir_path = os.path.dirname(__file__)
        path_manrope = os.path.join(main_dir_path, "assets/fonts/Manrope-Regular.ttf")
        if font == "Manrope":
            self.font = pygame.font.Font(path_manrope, font_size)
        else:
            self.font = pygame.font.SysFont(font, font_size)

        # Build the text box's rect object and center it.
        self.center = center
        self.text_box_left_top = text_box_left_top
        self.rect = pygame.Rect(
            self.text_box_left_top[0],
            self.text_box_left_top[1],
            self.width,
            self.height,
        )
        if self.center:
            self.rect.center = self.center

        # The message needs to be printed only once.
        if msg:
            self.print_msg(msg)

    def print_msg(self, msg) -> None:
        """Turn msg into a rendered image and center text on the text box."""
        self.msg_image = self.font.render(
            msg, True, self.text_color, self.textbox_color
        )
        self.msg_image_rect = self.msg_image.get_rect()
        if self.center:
            self.msg_image_rect.center = self.rect.center
        else:
            self.msg_image_rect.left = self.text_box_left_top[0]
            self.msg_image_rect.top = self.text_box_left_top[1]

    def draw(self) -> None:
        """Draw blank text box and then draw message."""
        if self.textbox_color:
            self.screen.fill(self.textbox_color, self.rect)

        self.screen.blit(self.msg_image, self.msg_image_rect)






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
        if self.remove_out_of_range_objs():
            gravity_sim.simulator.is_initialize = True   
        else:
            self.update_apparent_pos()

    def remove_out_of_range_objs(self):
        """Remove object when position is out of range"""
        if abs(self.params["r1"]) > self.settings.MAX_RANGE or abs(self.params["r2"]) > self.settings.MAX_RANGE or abs(self.params["r3"]) > self.settings.MAX_RANGE:
            self.kill()
            print("System message: Out of range object removed.")
            return True 
        else:
            return False  
               

    def update_apparent_pos(self):
        """Update the apparent position of all grav_objs with camera"""
        try:
            self.rect.center = (
                self.params["r1"] * self.settings.distance_scale
                + self.screen_rect.centerx
                - self.camera.pos[0],
                -self.params["r2"] * self.settings.distance_scale
                + self.screen_rect.centery
                - self.camera.pos[1],
            )
        except TypeError:
            pass


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
                    * grav_sim.settings.new_star_speed_scale * Settings.NEW_STAR_SPEED_CONVERT_FACTOR,
                    "v2": (
                        (drag_mouse_pos[1] - mouse_pos[1])
                        + (drag_camera_pos[1] - camera_pos[1])
                    )
                    * grav_sim.settings.new_star_speed_scale * Settings.NEW_STAR_SPEED_CONVERT_FACTOR,
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


class Menu:
    """A class to build the menu"""

    def __init__(self, grav_sim):
        """Initialize button attributes."""
        self.screen = grav_sim.screen
        self.screen_rect = self.screen.get_rect()
        self.settings = grav_sim.settings
        self.main_menu_active = True
        self.menu_active = True

        self.main_menu_caption = Text_box(
            grav_sim,
            72,
            0,
            0,
            msg="Gravity Simulator",
            font="Manrope",
            center=(
                self.screen_rect.centerx,
                self.screen_rect.centery - 0.3 * self.settings.screen_height,
            ),
        )
        self.resume_button = Text_box(
            grav_sim,
            48,
            0.25,
            0.05,
            msg="Resume",
            text_box_color=(220, 220, 220),
            text_color=(0, 0, 0),
            center=(
                self.screen_rect.centerx,
                self.screen_rect.centery - 0.22 * self.settings.screen_height,
            ),
        )
        self.void_button = Text_box(
            grav_sim,
            48,
            0.25,
            0.05,
            msg="Void",
            text_box_color=(220, 220, 220),
            text_color=(0, 0, 0),
            center=(
                self.screen_rect.centerx,
                self.screen_rect.centery - 0.14 * self.settings.screen_height,
            ),
        )
        self.solar_system_button = Text_box(
            grav_sim,
            48,
            0.25,
            0.05,
            msg="Solar System",
            text_box_color=(220, 220, 220),
            text_color=(0, 0, 0),
            center=(
                self.screen_rect.centerx,
                self.screen_rect.centery - 0.06 * self.settings.screen_height,
            ),
        )
        self.figure_8_button = Text_box(
            grav_sim,
            48,
            0.25,
            0.05,
            msg="Figure 8 orbit",
            text_box_color=(220, 220, 220),
            text_color=(0, 0, 0),
            center=(
                self.screen_rect.centerx,
                self.screen_rect.centery - (-0.02) * self.settings.screen_height,
            ),
        )
        self.pyth_3_body_button = Text_box(
            grav_sim,
            48,
            0.25,
            0.05,
            msg="Pythagorean three-body",
            text_box_color=(220, 220, 220),
            text_color=(0, 0, 0),
            center=(
                self.screen_rect.centerx,
                self.screen_rect.centery - (-0.1) * self.settings.screen_height,
            ),
        )
        self.exit_button = Text_box(
            grav_sim,
            48,
            0.25,
            0.05,
            msg="Exit",
            text_box_color=(220, 220, 220),
            text_color=(0, 0, 0),
            center=(
                self.screen_rect.centerx,
                self.screen_rect.centery - (-0.18) * self.settings.screen_height,
            ),
        )
        self.main_menu_button = Text_box(
            grav_sim,
            48,
            0.25,
            0.05,
            msg="Main Menu",
            text_box_color=(220, 220, 220),
            text_color=(0, 0, 0),
            center=(
                self.screen_rect.centerx,
                self.screen_rect.centery - (-0.18) * self.settings.screen_height,
            ),
        )

    def draw(self):
        """Draw the menu buttons"""
        if self.main_menu_active == True:
            self.main_menu_caption.draw()
            self.exit_button.draw()
        else:
            self.resume_button.draw()
            self.main_menu_button.draw()

        self.void_button.draw()
        self.solar_system_button.draw()
        self.figure_8_button.draw()
        self.pyth_3_body_button.draw()

    def check_button(self, grav_sim, mouse_pos):
        """Check if there is any click on the buttons"""
        if self.main_menu_active == False:
            if self.resume_button.rect.collidepoint(mouse_pos):
                self.menu_active = False
            if self.main_menu_button.rect.collidepoint(mouse_pos):
                grav_sim.grav_objs.empty()
                grav_sim.stats.reset(grav_sim)
                self.main_menu_active = True
        else:
            if self.exit_button.rect.collidepoint(mouse_pos):
                sys.exit()
        if self.void_button.rect.collidepoint(mouse_pos):
            self._menu_common_actions(grav_sim)
            self.settings.expected_time_scale = 1e5
        if self.solar_system_button.rect.collidepoint(mouse_pos):
            self._menu_common_actions(grav_sim)
            Grav_obj.create_solor_system(grav_sim)
            self.settings.expected_time_scale = 1e5
        if self.figure_8_button.rect.collidepoint(mouse_pos):
            self._menu_common_actions(grav_sim)
            Grav_obj.create_figure_8(grav_sim)
            self.settings.expected_time_scale = 1e5
        if self.pyth_3_body_button.rect.collidepoint(mouse_pos):
            self._menu_common_actions(grav_sim)
            Grav_obj.create_pyth_3_body(grav_sim)
            self.settings.expected_time_scale = 1e2

    def _menu_common_actions(self, grav_sim):
        grav_sim.grav_objs.empty()
        grav_sim.stats.reset(grav_sim)
        self.menu_active = False
        self.main_menu_active = False




class Settings:
    """A class to store all settings for gravity simulator."""

    # If you want to change the default integrator, go to simulator.py __init__
    MAX_FPS = 60
    BG_COLOR = (0, 0, 0)  # Background color
    MAX_RANGE = 100000 # Max object distance from origin

    DEFAULT_STAR_IMG_SCALE = 5000
    DEFAULT_PLANET_IMG_SCALE = 100000
    DEFAULT_DISTANCE_SCALE = 150
    DEFAULT_NEW_STAR_MASS_SCALE = 1
    DEFAULT_NEW_STAR_SPEED_SCALE = 1
    DEFAULT_DT = 0.1
    DEFAULT_TIME_SPEED = 1
    DEFAULT_MAX_ITERATION = 10
    DEFAULT_MIN_ITERATION = 1
    DEFAULT_TOLERANCE = 1e-6
    DEFAULT_EXPECTED_TIME_SCALE = 1e4

    MAX_STAR_IMG_SCALE = 100000
    MIN_STAR_IMG_SCALE = 1
    MAX_PLANET_IMG_SCALE = 500000
    MIN_PLANET_IMG_SCALE = 1
    MAX_DISTANCE_SCALE = 1000
    MIN_DISTANCE_SCALE = 1
    MAX_NEW_STAR_MASS_SCALE = 1000
    MIN_NEW_STAR_MASS_SCALE = 1e-3
    MAX_NEW_STAR_SPEED_SCALE = 1000
    MIN_NEW_STAR_SPEED_SCALE = 1
    MAX_DT = 100
    MIN_DT = 1e-10
    MAX_TIME_SPEED = 200000
    MIN_TIME_SPEED = 1
    MAX_MAX_ITERATION = 50000
    MIN_MAX_ITERATION = 1
    MAX_MIN_ITERATION = 50000
    MIN_MIN_ITERATION = 1
    MAX_TOLERANCE = 1e-4
    MIN_TOLERANCE = 1e-15
    MAX_EXPECTED_TIME_SCALE = 1e10
    MIN_EXPECTED_TIME_SCALE = 1

    DEFAULT_CHANGE_STAR_IMG_SCALE_SPEED = 1000
    DEFAULT_CHANGE_PLANET_IMG_SCALE_SPEED = 10000
    DEFAULT_CHANGE_DISTANCE_SCALE_SPEED = 10

    NEW_STAR_SPEED_CONVERT_FACTOR = 1e-4 # Multiply with new_star_speed_scale to get the actual scale

    def __init__(
        self,
        screen_width: int,
        screen_height: int,
    ) -> None:
        # To change the default settings of screen_width and screen_height, go to _read_command_line_arg function in __main__.py
        self.screen_width = 1920
        self.screen_height = 1080
        self.star_img_scale = self.DEFAULT_STAR_IMG_SCALE
        self.planet_img_scale = self.DEFAULT_PLANET_IMG_SCALE
        self.distance_scale = self.DEFAULT_DISTANCE_SCALE
        self.new_star_mass_scale = self.DEFAULT_NEW_STAR_MASS_SCALE
        self.new_star_speed_scale = self.DEFAULT_NEW_STAR_SPEED_SCALE
        self.dt = self.DEFAULT_DT
        self.time_speed = self.DEFAULT_TIME_SPEED
        # Initializing internal variable directly because min_iteration.setter and max_iteration.setter depends on each other
        self._max_iteration = self.DEFAULT_MAX_ITERATION
        self._min_iteration = self.DEFAULT_MIN_ITERATION
        self.tolerance = self.DEFAULT_TOLERANCE
        self.expected_time_scale = self.DEFAULT_EXPECTED_TIME_SCALE
        self.set_all_parameters_changing_false()
        self.current_changing_parameter = None
        self.is_hide_gui = False

    def scroll_change_parameters(self, magnitude):
        match self.current_changing_parameter:
            case "star_img_scale":
                for _ in range(abs(magnitude)):
                    if self.star_img_scale >= 10000:
                        if magnitude > 0:
                            self.star_img_scale += (
                                self.DEFAULT_CHANGE_STAR_IMG_SCALE_SPEED
                            )
                        elif magnitude < 0:
                            self.star_img_scale -= (
                                self.DEFAULT_CHANGE_STAR_IMG_SCALE_SPEED
                            )
                    else:
                        self.star_img_scale += self._rate_of_change(
                            self.star_img_scale, magnitude
                        )
            case "planet_img_scale":
                for _ in range(abs(magnitude)):
                    if self.planet_img_scale >= 100000:
                        if magnitude > 0:
                            self.planet_img_scale += (
                                self.DEFAULT_CHANGE_PLANET_IMG_SCALE_SPEED
                            )
                        elif magnitude < 0:
                            self.planet_img_scale -= (
                                self.DEFAULT_CHANGE_PLANET_IMG_SCALE_SPEED
                            )
                    else:
                        self.planet_img_scale += self._rate_of_change(
                            self.planet_img_scale, magnitude
                        )
            case "distance_scale":
                for _ in range(abs(magnitude)):
                    if self.distance_scale >= 100:
                        if magnitude > 0:
                            self.distance_scale += (
                                self.DEFAULT_CHANGE_DISTANCE_SCALE_SPEED
                            )
                        elif magnitude < 0:
                            self.distance_scale -= (
                                self.DEFAULT_CHANGE_DISTANCE_SCALE_SPEED
                            )
                    else:
                        self.distance_scale += self._rate_of_change(
                            self.distance_scale, magnitude
                        )
            case "new_star_mass_scale":
                for _ in range(abs(magnitude)):
                    self.new_star_mass_scale += self._rate_of_change(
                        self.new_star_mass_scale, magnitude
                    )
            case "new_star_speed_scale":
                for _ in range(abs(magnitude)):
                    self.new_star_speed_scale += self._rate_of_change(
                        self.new_star_speed_scale, magnitude
                    )
            case "dt":
                for _ in range(abs(magnitude)):
                    self.dt += self._rate_of_change(self.dt, magnitude)
            case "time_speed":
                for _ in range(abs(magnitude)):
                    self.time_speed += self._rate_of_change(self.time_speed, magnitude)
            case "max_iteration":
                for _ in range(abs(magnitude)):
                    self.max_iteration += self._rate_of_change(
                        self.max_iteration, magnitude
                    )
            case "min_iteration":
                for _ in range(abs(magnitude)):
                    self.min_iteration += self._rate_of_change(
                        self.min_iteration, magnitude
                    )
            case "tolerance":
                for _ in range(abs(magnitude)):
                    self.tolerance += self._rate_of_change(self.tolerance, magnitude)

    @staticmethod
    def _rate_of_change(x: float, magnitude: int) -> float:
        if magnitude > 0:
            return 10 ** math.floor(math.log10(x))
        elif magnitude < 0:
            if f"{x:e}"[0] == "1":
                return -x * 0.1
            else:
                return -(10 ** math.floor(math.log10(x)))

    def check_current_changing_parameter(self):
        if self.is_changing_star_img_scale == True:
            self.current_changing_parameter = "star_img_scale"
        elif self.is_changing_planet_img_scale == True:
            self.current_changing_parameter = "planet_img_scale"
        elif self.is_changing_distance_scale == True:
            self.current_changing_parameter = "distance_scale"
        elif self.is_changing_new_star_mass_scale == True:
            self.current_changing_parameter = "new_star_mass_scale"
        elif self.is_changing_new_star_speed_scale == True:
            self.current_changing_parameter = "new_star_speed_scale"
        elif self.is_changing_dt == True:
            self.current_changing_parameter = "dt"
        elif self.is_changing_time_speed == True:
            self.current_changing_parameter = "time_speed"
        elif self.is_changing_max_iteration == True:
            self.current_changing_parameter = "max_iteration"
        elif self.is_changing_min_iteration == True:
            self.current_changing_parameter = "min_iteration"
        elif self.is_changing_tolerance == True:
            self.current_changing_parameter = "tolerance"

    def set_all_parameters_changing_false(self):
        self.is_changing_star_img_scale = False
        self.is_changing_planet_img_scale = False
        self.is_changing_distance_scale = False
        self.is_changing_new_star_mass_scale = False
        self.is_changing_new_star_speed_scale = False
        self.is_changing_dt = False
        self.is_changing_time_speed = False
        self.is_changing_max_iteration = False
        self.is_changing_min_iteration = False
        self.is_changing_tolerance = False

    def reset_parameters(self):
        self.star_img_scale = self.DEFAULT_STAR_IMG_SCALE
        self.planet_img_scale = self.DEFAULT_PLANET_IMG_SCALE
        self.time_speed = self.DEFAULT_TIME_SPEED
        self.new_star_mass_scale = self.DEFAULT_NEW_STAR_MASS_SCALE
        self.new_star_speed_scale = self.DEFAULT_NEW_STAR_SPEED_SCALE
        self.dt = self.DEFAULT_DT
        self.distance_scale = self.DEFAULT_DISTANCE_SCALE
        self.max_iteration = self.DEFAULT_MAX_ITERATION
        self.min_iteration = self.DEFAULT_MIN_ITERATION
        self.tolerance = self.DEFAULT_TOLERANCE

    @property
    def screen_width(self):
        return self._screen_width

    @screen_width.setter
    def screen_width(self, value):
        if value < 0:
            self._screen_width = 0
        else:
            self._screen_width = value

    @property
    def screen_height(self):
        return self._screen_height

    @screen_height.setter
    def screen_height(self, value):
        if value < 0:
            self._screen_height = 0
        else:
            self._screen_height = value

    @property
    def star_img_scale(self):
        return self._star_img_scale

    # Img may corrupt if the scale is too large.
    @star_img_scale.setter
    def star_img_scale(self, value):
        if value > self.MAX_STAR_IMG_SCALE:
            self._star_img_scale = self.MAX_STAR_IMG_SCALE
        elif value < self.MIN_STAR_IMG_SCALE:
            self._star_img_scale = self.MIN_STAR_IMG_SCALE
        else:
            self._star_img_scale = int(value)

    @property
    def planet_img_scale(self):
        return self._planet_img_scale

    # Img may corrupt if the scale is too large.
    @planet_img_scale.setter
    def planet_img_scale(self, value):
        if value > self.MAX_PLANET_IMG_SCALE:
            self._planet_img_scale = self.MAX_PLANET_IMG_SCALE
        elif value < self.MIN_PLANET_IMG_SCALE:
            self._planet_img_scale = self.MIN_PLANET_IMG_SCALE
        else:
            self._planet_img_scale = int(value)

    @property
    def distance_scale(self):
        return self._distance_scale

    @distance_scale.setter
    def distance_scale(self, value):
        if value > self.MAX_DISTANCE_SCALE:
            self._distance_scale = self.MAX_DISTANCE_SCALE
        elif value <= self.MIN_DISTANCE_SCALE:
            self._distance_scale = self.MIN_DISTANCE_SCALE
        else:
            self._distance_scale = int(value)

    @property
    def new_star_mass_scale(self):
        return self._new_star_mass_scale

    @new_star_mass_scale.setter
    def new_star_mass_scale(self, value):
        if value > self.MAX_NEW_STAR_MASS_SCALE:
            self._new_star_mass_scale = self.MAX_NEW_STAR_MASS_SCALE
        elif value < self.MIN_NEW_STAR_MASS_SCALE:
            self._new_star_mass_scale = self.MIN_NEW_STAR_MASS_SCALE
        else:
            self._new_star_mass_scale = round(value, ndigits=15)

    @property
    def new_star_speed_scale(self):
        return self._new_star_speed_scale

    @new_star_speed_scale.setter
    def new_star_speed_scale(self, value):
        if value > self.MAX_NEW_STAR_SPEED_SCALE:
            self._new_star_speed_scale = self.MAX_NEW_STAR_SPEED_SCALE
        elif value < self.MIN_NEW_STAR_SPEED_SCALE:
            self._new_star_speed_scale = self.MIN_NEW_STAR_SPEED_SCALE
        else:
            self._new_star_speed_scale = int(value)

    @property
    def dt(self):
        return self._dt

    @dt.setter
    def dt(self, value):
        if value > self.MAX_DT:
            self._dt = self.MAX_DT
        elif value < self.MIN_DT:
            self._dt = self.MIN_DT
        else:
            self._dt = round(value, ndigits=15)

    @property
    def time_speed(self):
        return self._time_speed

    @time_speed.setter
    def time_speed(self, value):
        if value > self.MAX_TIME_SPEED:
            self._time_speed = self.MAX_TIME_SPEED
        elif value < self.MIN_TIME_SPEED:
            self._time_speed = self.MIN_TIME_SPEED
        else:
            self._time_speed = int(value)

    @property
    def max_iteration(self):
        return self._max_iteration

    @max_iteration.setter
    def max_iteration(self, value):
        if value > self.MAX_MAX_ITERATION:
            self._max_iteration = self.MAX_MAX_ITERATION
        elif value < self.MIN_MAX_ITERATION:
            self._max_iteration = self.MIN_MAX_ITERATION
        elif value < self.min_iteration:
            self._max_iteration = self.min_iteration
        else:
            self._max_iteration = int(value)

    @property
    def min_iteration(self):
        return self._min_iteration

    @min_iteration.setter
    def min_iteration(self, value):
        if value > self.MAX_MIN_ITERATION:
            self._min_iteration = self.MAX_MIN_ITERATION
        elif value > self.max_iteration:
            self._min_iteration = self.max_iteration
        elif value < self.MIN_MIN_ITERATION:
            self._min_iteration = self.MIN_MIN_ITERATION
        else:
            self._min_iteration = int(value)

    @property
    def tolerance(self):
        return self._tolerance

    @tolerance.setter
    def tolerance(self, value):
        if value > self.MAX_TOLERANCE:
            self._tolerance = self.MAX_TOLERANCE
        elif value < self.MIN_TOLERANCE:
            self._tolerance = self.MIN_TOLERANCE
        else:
            self._tolerance = round(value, ndigits=15)

    @property
    def expected_time_scale(self):
        return self._expected_time_scale

    @expected_time_scale.setter
    def expected_time_scale(self, value):
        if value > self.MAX_EXPECTED_TIME_SCALE:
            self._expected_time_scale = self.MAX_EXPECTED_TIME_SCALE
        elif value < self.MIN_EXPECTED_TIME_SCALE:
            self._expected_time_scale = self.MIN_EXPECTED_TIME_SCALE
        else:
            self._expected_time_scale = value


class FIXED_STEP_SIZE_INTEGRATOR:
    """Fixed step size integrators: Euler, Euler Cromer, RK4, Leap Frog"""

    def simulation(self, simulator, integrator, objects_count, m, G, dt, time_speed):
        if simulator.is_c_lib == True:
            match integrator:
                case "euler":
                    if (
                        simulator.is_initialize == True
                        and simulator.is_initialize_integrator == "euler"
                    ):
                        simulator.is_initialize = False

                    simulator.c_lib.euler(
                        ctypes.c_int(objects_count), 
                        simulator.x.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), 
                        simulator.v.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), 
                        m.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), 
                        ctypes.c_double(G), 
                        ctypes.c_double(dt), 
                        ctypes.c_int(time_speed)
                    )
                
                case "euler_cromer":
                    if (
                        simulator.is_initialize == True
                        and simulator.is_initialize_integrator == "euler_cromer"
                    ):
                        simulator.is_initialize = False

                    simulator.c_lib.euler_cromer(
                        ctypes.c_int(objects_count), 
                        simulator.x.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), 
                        simulator.v.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), 
                        m.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), 
                        ctypes.c_double(G), 
                        ctypes.c_double(dt), 
                        ctypes.c_int(time_speed)
                    )

                case "rk4":
                    if (
                        simulator.is_initialize == True
                        and simulator.is_initialize_integrator == "rk4"
                    ):
                        simulator.is_initialize = False

                    simulator.c_lib.rk4(
                        ctypes.c_int(objects_count), 
                        simulator.x.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), 
                        simulator.v.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), 
                        m.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), 
                        ctypes.c_double(G), 
                        ctypes.c_double(dt), 
                        ctypes.c_int(time_speed)
                    )

                case "leapfrog":
                    if (
                        simulator.is_initialize == True
                        and simulator.is_initialize_integrator == "leapfrog"
                    ):
                        simulator.c_lib.acceleration(
                            ctypes.c_int(objects_count), 
                            simulator.x.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), 
                            simulator.a.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), 
                            m.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), 
                            ctypes.c_double(G), 
                        )
                        simulator.is_initialize = False

                    simulator.c_lib.leapfrog(
                        ctypes.c_int(objects_count), 
                        simulator.x.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), 
                        simulator.v.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), 
                        simulator.a.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), 
                        m.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), 
                        ctypes.c_double(G), 
                        ctypes.c_double(dt), 
                        ctypes.c_int(time_speed)
                    )

        elif simulator.is_c_lib == False:
            match integrator:
                case "euler":
                    if (
                        simulator.is_initialize == True
                        and simulator.is_initialize_integrator == "euler"
                    ):
                        simulator.is_initialize = False

                    simulator.x, simulator.v = self._euler(objects_count, simulator.x, simulator.v, m, G, dt, time_speed)
                
                case "euler_cromer":
                    if (
                        simulator.is_initialize == True
                        and simulator.is_initialize_integrator == "euler_cromer"
                    ):
                        simulator.is_initialize = False

                    simulator.x, simulator.v = self._euler_cromer(objects_count, simulator.x, simulator.v, m, G, dt, time_speed)

                case "rk4":
                    if (
                        simulator.is_initialize == True
                        and simulator.is_initialize_integrator == "rk4"
                    ):
                        simulator.is_initialize = False

                    simulator.x, simulator.v = self._rk4(
                        objects_count,
                        simulator.x,
                        simulator.v,
                        m,
                        G,
                        dt,
                        time_speed,
                    )

                case "leapfrog":
                    if (
                        simulator.is_initialize == True
                        and simulator.is_initialize_integrator == "leapfrog"
                    ):
                        simulator.a = acceleration(
                            objects_count, simulator.x, m, G
                        )
                        simulator.is_initialize = False

                    simulator.x, simulator.v, simulator.a = self._leapfrog(
                        objects_count,
                        simulator.x,
                        simulator.v,
                        simulator.a,
                        m,
                        G,
                        dt,
                        time_speed,
                    )


    @staticmethod
    def _euler(objects_count, x, v, m, G, dt, time_speed):
        for _ in range(time_speed):
            a = acceleration(objects_count, x, m, G)
            x += v * dt
            v += a * dt 

        return x, v 

    @staticmethod
    def _euler_cromer(objects_count, x, v, m, G, dt, time_speed):
        for _ in range(time_speed):
            a = acceleration(objects_count, x, m, G)
            v += a * dt             
            x += v * dt

        return x, v

    @staticmethod
    def _rk4(objects_count, x, v, m, G, dt, time_speed):
        for _ in range(time_speed):
            vk1 = acceleration(objects_count, x, m, G)
            xk1 = v

            vk2 = acceleration(objects_count, x + 0.5 * xk1 * dt, m, G)
            xk2 = v + 0.5 * vk1 * dt

            vk3 = acceleration(objects_count, x + 0.5 * xk2 * dt, m, G)
            xk3 = v + 0.5 * vk2 * dt

            vk4 = acceleration(objects_count, x + xk3 * dt, m, G)
            xk4 = v + vk3 * dt

            v = v + dt * (vk1 + 2 * vk2 + 2 * vk3 + vk4) / 6.0
            x = x + dt * (xk1 + 2 * xk2 + 2 * xk3 + xk4) / 6.0

        return x, v

    @staticmethod
    def _leapfrog(objects_count, x, v, a, m, G, dt, time_speed):
        a_1 = a
        for _ in range(time_speed):
            a_0 = a_1
            x = x + v * dt + a_0 * 0.5 * dt * dt
            a_1 = acceleration(objects_count, x, m, G)
            v = v + (a_0 + a_1) * 0.5 * dt

        return x, v, a_1


class IAS15:
    """IAS15 integrator"""
    def __init__(self):
        # Recommended tolerance: 1e-9

        # Safety factors for step-size control
        self.safety_fac = 0.25

        # For fixed step integration, choose exponent = 0
        self.exponent = 1.0 / 7.0

        # Tolerance of predictor-corrector algorithm
        self.tolerance_pc = 1e-16

        # Initializing auxiliary variables
        self.nodes, self.dim_nodes = self._ias15_radau_spacing()
        self.aux_c = self._ias15_aux_c()    
        self.aux_r = self._ias15_aux_r()

    def simulation(self, simulator, objects_count, m, G, tolerance, expected_time_scale, max_iteration, min_iteration):
        if simulator.is_initialize == True and simulator.is_initialize_integrator == "ias15":
            # Initializing auxiliary variables
            self.aux_b0 = np.zeros((self.dim_nodes - 1, objects_count, 3))
            self.aux_b = np.zeros((self.dim_nodes - 1, objects_count, 3))
            self.aux_g = np.zeros((self.dim_nodes - 1, objects_count, 3))
            self.aux_e = np.zeros((self.dim_nodes - 1, objects_count, 3))

            simulator.a = acceleration(objects_count, simulator.x, m, G)

            self.dt = self._ias15_initial_time_step(objects_count, 15, simulator.x, simulator.v, simulator.a, m, G)

            self.ias15_refine_flag = 0

            simulator.is_initialize = False
        
        # Simulation
        if simulator.is_c_lib == True:
            count = ctypes.c_int(0)
            temp_simulation_time = ctypes.c_double(simulator.stats.simulation_time)
            temp_dt = ctypes.c_double(self.dt)
            temp_ias15_refine_flag = ctypes.c_int(self.ias15_refine_flag)

            simulator.c_lib.ias15(
                ctypes.c_int(objects_count), 
                simulator.x.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), 
                simulator.v.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), 
                simulator.a.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), 
                m.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), 
                ctypes.c_double(G), 
                ctypes.c_int(self.dim_nodes),
                self.nodes.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), 
                self.aux_c.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), 
                self.aux_r.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), 
                self.aux_b0.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), 
                self.aux_b.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), 
                self.aux_g.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), 
                self.aux_e.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), 
                ctypes.byref(temp_simulation_time), 
                ctypes.byref(temp_dt),
                ctypes.c_double(expected_time_scale),
                ctypes.byref(count),
                ctypes.c_double(tolerance),
                ctypes.c_double(self.tolerance_pc),
                ctypes.c_double(self.safety_fac),
                ctypes.c_double(self.exponent),
                ctypes.byref(temp_ias15_refine_flag),
                ctypes.c_int(max_iteration),
                ctypes.c_int(min_iteration),
            )
            simulator.stats.simulation_time = temp_simulation_time.value
            self.dt = temp_dt.value
            self.ias15_refine_flag = temp_ias15_refine_flag.value

        elif simulator.is_c_lib == False:
            count = 0
            t0 = simulator.stats.simulation_time
            for _ in range(max_iteration):
                (
                    simulator.x,
                    simulator.v,
                    simulator.a,
                    simulator.stats.simulation_time,
                    self.dt,
                    self.aux_g,
                    self.aux_b,
                    self.aux_e,
                    self.aux_b0,
                    self.ias15_refine_flag,
                ) = self._ias15_step(
                    objects_count,
                    simulator.x,
                    simulator.v,
                    simulator.a,
                    m,
                    G,
                    simulator.stats.simulation_time,
                    self.dt,
                    expected_time_scale,
                    self.dim_nodes,
                    self.nodes,
                    self.aux_b0,
                    self.aux_b,
                    self.aux_c,
                    self.aux_e,
                    self.aux_g,
                    self.aux_r,
                    tolerance,
                    self.tolerance_pc,
                    self.exponent,
                    self.safety_fac,
                    self.ias15_refine_flag,
                    self._ias15_approx_pos,
                    self._ias15_approx_vel,
                    self._ias15_compute_aux_b,
                    self._ias15_compute_aux_g,
                    self._ias15_refine_aux_b,
                )

                count += 1
                if count >= min_iteration and simulator.stats.simulation_time > (t0 + expected_time_scale * 1e-5):
                    break
    
    @staticmethod
    def _ias15_step(
        objects_count,
        x0,
        v0,
        a0,
        m,
        G,
        t,
        dt,
        tf,
        dim_nodes,
        nodes,
        aux_b0,
        aux_b,
        aux_c,
        aux_e,
        aux_g,
        aux_r,
        tolerance,
        tolerance_pc,
        exponent,
        safety_fac,
        ias15_refine_flag,
        ias15_approx_pos,
        ias15_approx_vel,
        ias15_compute_aux_b,
        ias15_compute_aux_g,
        ias15_refine_aux_b,
    ):
        """
        Advance IAS15 for one step
        """
        # Main Loop
        ias15_integrate_flag = 0
        aux_a = np.zeros((dim_nodes, objects_count, 3))
        while True:
            # Loop for predictor-corrector algorithm
            # 12 = max iterations
            for _ in range(12):
                # Advance along the Gauss-Radau sequence
                for i in range(dim_nodes):
                    # Estimate position and velocity with current aux_b and nodes
                    x = ias15_approx_pos(x0, v0, a0, nodes[i], aux_b, dt)
                    v = ias15_approx_vel(v0, a0, nodes[i], aux_b, dt)

                    # Evaluate force function and store result
                    aux_a[i] = acceleration(objects_count, x, m, G)
                    aux_g = ias15_compute_aux_g(aux_g, aux_r, aux_a, i)
                    aux_b = ias15_compute_aux_b(aux_b, aux_g, aux_c, i)

                # Estimate convergence
                delta_b7 = aux_b[-1] - aux_b0[-1]
                aux_b0 = aux_b
                if np.max(np.abs(delta_b7)) / np.max(np.abs(aux_a[-1])) < tolerance_pc:
                    break
                
            # Advance step
            x = ias15_approx_pos(x0, v0, a0, 1.0, aux_b, dt)
            v = ias15_approx_vel(v0, a0, 1.0, aux_b, dt)
            a = acceleration(objects_count, x, m, G)

            # Estimate relative error
            error_b7 = np.max(np.abs(aux_b[-1])) / np.max(np.abs(a))
            error = (error_b7 / tolerance) ** exponent
            
            # Step-size for the next step
            if error != 0:
                dt_new = dt / error
            else:
                dt_new = dt

            # Accept the step
            if error <= 1 or dt == tf * 1e-12:
                # Report accepted step
                ias15_integrate_flag = 1
                t += dt
                aux_b, aux_e = ias15_refine_aux_b(
                    aux_b, aux_e, dt, dt_new, ias15_refine_flag
                )
                ias15_refine_flag = 1

                if t >= tf:
                    ias15_integrate_flag = 2
                    break

            # Step size for the next iteration
            if (dt_new / dt) > (1.0 / safety_fac):
                dt = dt / safety_fac
            elif dt_new < dt * safety_fac:
                dt = dt * safety_fac
            else:
                dt = dt_new

            if dt_new / tf < 1e-12:
                dt = tf * 1e-12

            if ias15_integrate_flag > 0:
                break

        return (
            x,
            v,
            a,
            t,
            dt,
            aux_g,
            aux_b,
            aux_e,
            aux_b0,
            ias15_refine_flag,
        )

    @staticmethod
    def _ias15_approx_pos(x0, v0, a0, node, aux_b, dt):
        x = x0 + dt * node * (
            v0
            + dt
            * node
            * (
                a0
                + node
                * (
                    aux_b[0] / 3.0
                    + node
                    * (
                        aux_b[1] / 6.0
                        + node
                        * (
                            aux_b[2] / 10.0
                            + node
                            * (
                                aux_b[3] / 15.0
                                + node
                                * (
                                    aux_b[4] / 21.0
                                    + node * (aux_b[5] / 28.0 + node * aux_b[6] / 36.0)
                                )
                            )
                        )
                    )
                )
            )
            / 2.0
        )

        return x

    @staticmethod
    def _ias15_approx_vel(v0, a0, node, aux_b, dt):
        v = v0 + dt * node * (
            a0
            + node
            * (
                aux_b[0] / 2.0
                + node
                * (
                    aux_b[1] / 3.0
                    + node
                    * (
                        aux_b[2] / 4.0
                        + node
                        * (
                            aux_b[3] / 5.0
                            + node
                            * (
                                aux_b[4] / 6.0
                                + node * (aux_b[5] / 7.0 + node * aux_b[6] / 8.0)
                            )
                        )
                    )
                )
            )
        )

        return v

    @staticmethod
    def _ias15_initial_time_step(
        objects_count: int,
        power: int,
        x,
        v,
        a,
        m,
        G,
    ) -> float:
        """
        Calculate the initial time step for IAS15

        Reference: Moving Planets Around: An Introduction to N-Body Simulations Applied to Exoplanetary Systems
        Chapter 8, Page 149
        """
        d_0 = np.max(np.abs(x))
        d_1 = np.max(np.abs(a))

        if d_0 < 1e-5 or d_1 < 1e-5:
            dt_0 = 1e-6
        else:
            dt_0 = 0.01 * (d_0 / d_1)

        x_1 = x + dt_0 * v
        # v_1 = v + dt_0 * a
        a_1 = acceleration(objects_count, x_1, m, G)
        d_2 = np.max(np.abs(a_1 - a)) / dt_0

        if max(d_1, d_2) <= 1e-15:
            dt_1 = max(1e-6, dt_0 * 1e-3)
        else:
            dt_1 = (0.01 / max(d_1, d_2)) ** (1.0 / (1.0 + power))
        dt = min(100 * dt_0, dt_1)

        return dt
    
    @staticmethod
    def _ias15_radau_spacing():
        """
        Return the the nodes and its dimension for IAS15

        :rtype: numpy.array, int
        """
        dim_nodes = 8
        nodes = np.zeros(dim_nodes)

        nodes[0] = 0.0
        nodes[1] = 0.056262560536922146465652191032
        nodes[2] = 0.180240691736892364987579942809
        nodes[3] = 0.352624717113169637373907770171
        nodes[4] = 0.547153626330555383001448557652
        nodes[5] = 0.734210177215410531523210608306
        nodes[6] = 0.885320946839095768090359762932
        nodes[7] = 0.977520613561287501891174500429

        return nodes, dim_nodes

    @staticmethod
    def _ias15_compute_aux_b(aux_b, aux_g, aux_c, i):
        """
        Calculate the auxiliary coefficients b for IAS15

        :rtype: numpy.array
        """

        if i >= 1:
            aux_b[0] = (
                aux_c[0, 0] * aux_g[0]
                + aux_c[1, 0] * aux_g[1]
                + aux_c[2, 0] * aux_g[2]
                + aux_c[3, 0] * aux_g[3]
                + aux_c[4, 0] * aux_g[4]
                + aux_c[5, 0] * aux_g[5]
                + aux_c[6, 0] * aux_g[6]
            )

        if i >= 2:
            aux_b[1] = (
                aux_c[1, 1] * aux_g[1]
                + aux_c[2, 1] * aux_g[2]
                + aux_c[3, 1] * aux_g[3]
                + aux_c[4, 1] * aux_g[4]
                + aux_c[5, 1] * aux_g[5]
                + aux_c[6, 1] * aux_g[6]
            )
        if i >= 3:
            aux_b[2] = (
                aux_c[2, 2] * aux_g[2]
                + aux_c[3, 2] * aux_g[3]
                + aux_c[4, 2] * aux_g[4]
                + aux_c[5, 2] * aux_g[5]
                + aux_c[6, 2] * aux_g[6]
            )
        if i >= 4:
            aux_b[3] = (
                aux_c[3, 3] * aux_g[3]
                + aux_c[4, 3] * aux_g[4]
                + aux_c[5, 3] * aux_g[5]
                + aux_c[6, 3] * aux_g[6]
            )
        if i >= 5:
            aux_b[4] = (
                aux_c[4, 4] * aux_g[4] + aux_c[5, 4] * aux_g[5] + aux_c[6, 4] * aux_g[6]
            )
        if i >= 6:
            aux_b[5] = aux_c[5, 5] * aux_g[5] + aux_c[6, 5] * aux_g[6]
        if i >= 7:
            aux_b[6] = aux_c[6, 6] * aux_g[6]

        return aux_b

    @staticmethod
    def _ias15_aux_c():
        """
        Return the auxiliary coefficients c for IAS15

        :rtype: numpy.array
        :rshape: (7, 7)
        """
        aux_c = np.zeros((7, 7))
        for i in range(7):
            aux_c[i, i] = 1.0

        aux_c[1, 0] = -0.0562625605369221464656522

        aux_c[2, 0] = 0.01014080283006362998648180399549641417413495311078
        aux_c[2, 1] = -0.2365032522738145114532321

        aux_c[3, 0] = -0.0035758977292516175949344589284567187362040464593728
        aux_c[3, 1] = 0.09353769525946206589574845561035371499343547051116
        aux_c[3, 2] = -0.5891279693869841488271399

        aux_c[4, 0] = 0.0019565654099472210769005672379668610648179838140913
        aux_c[4, 1] = -0.054755386889068686440808430671055022602028382584495
        aux_c[4, 2] = 0.41588120008230686168862193041156933067050816537030
        aux_c[4, 3] = -1.1362815957175395318285885

        aux_c[5, 0] = -0.0014365302363708915424459554194153247134438571962198
        aux_c[5, 1] = 0.042158527721268707707297347813203202980228135395858
        aux_c[5, 2] = -0.36009959650205681228976647408968845289781580280782
        aux_c[5, 3] = 1.2501507118406910258505441186857527694077565516084
        aux_c[5, 4] = -1.8704917729329500633517991

        aux_c[6, 0] = 0.0012717903090268677492943117622964220889484666147501
        aux_c[6, 1] = -0.038760357915906770369904626849901899108502158354383
        aux_c[6, 2] = 0.36096224345284598322533983078129066420907893718190
        aux_c[6, 3] = -1.4668842084004269643701553461378480148761655599754
        aux_c[6, 4] = 2.9061362593084293014237914371173946705384212479246
        aux_c[6, 5] = -2.7558127197720458314421589

        return aux_c

    @staticmethod
    def _ias15_compute_aux_g(aux_g, aux_r, aux_a, i):
        # Retrieve required accelerations
        F1 = aux_a[0]
        F2 = aux_a[1]
        F3 = aux_a[2]
        F4 = aux_a[3]
        F5 = aux_a[4]
        F6 = aux_a[5]
        F7 = aux_a[6]
        F8 = aux_a[7]

        # Update aux_g
        if i >= 1:
            aux_g[0] = (F2 - F1) * aux_r[1, 0]
        if i >= 2:
            aux_g[1] = ((F3 - F1) * aux_r[2, 0] - aux_g[0]) * aux_r[2, 1]
        if i >= 3:
            aux_g[2] = (
                ((F4 - F1) * aux_r[3, 0] - aux_g[0]) * aux_r[3, 1] - aux_g[1]
            ) * aux_r[3, 2]
        if i >= 4:
            aux_g[3] = (
                (((F5 - F1) * aux_r[4, 0] - aux_g[0]) * aux_r[4, 1] - aux_g[1])
                * aux_r[4, 2]
                - aux_g[2]
            ) * aux_r[4, 3]
        if i >= 5:
            aux_g[4] = (
                (
                    (((F6 - F1) * aux_r[5, 0] - aux_g[0]) * aux_r[5, 1] - aux_g[1])
                    * aux_r[5, 2]
                    - aux_g[2]
                )
                * aux_r[5, 3]
                - aux_g[3]
            ) * aux_r[5, 4]
        if i >= 6:
            aux_g[5] = (
                (
                    (
                        (((F7 - F1) * aux_r[6, 0] - aux_g[0]) * aux_r[6, 1] - aux_g[1])
                        * aux_r[6, 2]
                        - aux_g[2]
                    )
                    * aux_r[6, 3]
                    - aux_g[3]
                )
                * aux_r[6, 4]
                - aux_g[4]
            ) * aux_r[6, 5]
        if i >= 7:
            aux_g[6] = (
                (
                    (
                        (
                            (((F8 - F1) * aux_r[7, 0] - aux_g[0]) * aux_r[7, 1] - aux_g[1])
                            * aux_r[7, 2]
                            - aux_g[2]
                        )
                        * aux_r[7, 3]
                        - aux_g[3]
                    )
                    * aux_r[7, 4]
                    - aux_g[4]
                )
                * aux_r[7, 5]
                - aux_g[5]
            ) * aux_r[7, 6]

        return aux_g

    @staticmethod
    def _ias15_aux_r():
        """
        Return the auxiliary coefficients r for IAS15

        :rtype: numpy.array
        :rshape: (8, 8)
        """
        aux_r = np.zeros((8, 8))

        aux_r[1, 0] = 17.773808914078000840752659565672904106978971632681
        aux_r[2, 0] = 5.5481367185372165056928216140765061758579336941398
        aux_r[3, 0] = 2.8358760786444386782520104428042437400879003147949
        aux_r[4, 0] = 1.8276402675175978297946077587371204385651628457154
        aux_r[5, 0] = 1.3620078160624694969370006292445650994197371928318
        aux_r[6, 0] = 1.1295338753367899027322861542728593509768148769105
        aux_r[7, 0] = 1.0229963298234867458386119071939636779024159134103

        aux_r[2, 1] = 8.0659386483818866885371256689687154412267416180207
        aux_r[3, 1] = 3.3742499769626352599420358188267460448330087696743
        aux_r[4, 1] = 2.0371118353585847827949159161566554921841792590404
        aux_r[5, 1] = 1.4750402175604115479218482480167404024740127431358
        aux_r[6, 1] = 1.2061876660584456166252036299646227791474203527801
        aux_r[7, 1] = 1.0854721939386423840467243172568913862030118679827

        aux_r[3, 2] = 5.8010015592640614823286778893918880155743979164251
        aux_r[4, 2] = 2.7254422118082262837742722003491334729711450288807
        aux_r[5, 2] = 1.8051535801402512604391147435448679586574414080693
        aux_r[6, 2] = 1.4182782637347391537713783674858328433713640692518
        aux_r[7, 2] = 1.2542646222818777659905422465868249586862369725826

        aux_r[4, 3] = 5.1406241058109342286363199091504437929335189668304
        aux_r[5, 3] = 2.6206449263870350811541816031933074696730227729812
        aux_r[6, 3] = 1.8772424961868100972169920283109658335427446084411
        aux_r[7, 3] = 1.6002665494908162609916716949161150366323259154408

        aux_r[5, 4] = 5.3459768998711075141214909632277898045770336660354
        aux_r[6, 4] = 2.9571160172904557478071040204245556508352776929762
        aux_r[7, 4] = 2.3235983002196942228325345451091668073608955835034

        aux_r[6, 5] = 6.6176620137024244874471284891193925737033291491748
        aux_r[7, 5] = 4.1099757783445590862385761824068782144723082633980

        aux_r[7, 6] = 10.846026190236844684706431007823415424143683137181

        return aux_r

    @staticmethod
    def _ias15_refine_aux_b(aux_b, aux_e, dt, dt_new, ias15_refine_flag):
        if ias15_refine_flag != 0:
            delta_aux_b = aux_b - aux_e
        else:
            delta_aux_b = aux_b * 0

        # Compute q and the powers of q:
        q = dt_new / dt
        q2 = q * q
        q3 = q2 * q
        q4 = q3 * q
        q5 = q4 * q
        q6 = q5 * q
        q7 = q6 * q

        aux_e[0] = q * (
            aux_b[6] * 7.0
            + aux_b[5] * 6.0
            + aux_b[4] * 5.0
            + aux_b[3] * 4.0
            + aux_b[2] * 3.0
            + aux_b[1] * 2.0
            + aux_b[0]
        )
        aux_e[1] = q2 * (
            aux_b[6] * 21.0
            + aux_b[5] * 15.0
            + aux_b[4] * 10.0
            + aux_b[3] * 6.0
            + aux_b[2] * 3.0
            + aux_b[1]
        )
        aux_e[2] = q3 * (
            aux_b[6] * 35.0 + aux_b[5] * 20.0 + aux_b[4] * 10.0 + aux_b[3] * 4.0 + aux_b[2]
        )
        aux_e[3] = q4 * (aux_b[6] * 35.0 + aux_b[5] * 15.0 + aux_b[4] * 5.0 + aux_b[3])
        aux_e[4] = q5 * (aux_b[6] * 21.0 + aux_b[5] * 6.0 + aux_b[4])
        aux_e[5] = q6 * (aux_b[6] * 7.0 + aux_b[5])
        aux_e[6] = q7 * aux_b[6]

        aux_b = aux_e + delta_aux_b

        return aux_b, aux_e




class RK_EMBEDDED:
    """Embedded RK integrators: RKF45, DOPRI, DVERK, RKF78"""
    def simulation(self, simulator, objects_count, m, G, abs_tolerance, rel_tolerance, expected_time_scale, max_iteration, min_iteration):
        # Initialization
        if simulator.is_initialize == True and simulator.is_initialize_integrator == simulator.current_integrator:
            match simulator.current_integrator:
                case "rkf45":
                    order = 45
                case "dopri":
                    order = 54
                case "dverk":
                    order = 65
                case "rkf78":
                    order = 78
                case _:
                    raise ValueError("Invalid integrator!")
                
            (
                self.power,
                self.power_test,
                self.coeff,
                self.weights,
                self.weights_test,
            ) = self._rk_embedded_butcher_tableaus(order)
            
            simulator.a = acceleration(
                objects_count, simulator.x, m, G
            )
            self.rk_dt = self._rk_embedded_initial_time_step(
                objects_count,
                self.power,
                simulator.x,
                simulator.v,
                simulator.a,
                m,
                G,
                abs_tolerance,
                rel_tolerance,
            )

            simulator.is_initialize = False

        # Simulation
        temp_simulation_time = ctypes.c_double(simulator.stats.simulation_time)
        temp_rk_dt = ctypes.c_double(self.rk_dt)
        if simulator.is_c_lib == True:
            simulator.c_lib.rk_embedded(
                ctypes.c_int(objects_count), 
                simulator.x.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), 
                simulator.v.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), 
                m.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), 
                ctypes.c_double(G), 
                ctypes.c_double(expected_time_scale),
                ctypes.byref(temp_simulation_time), 
                ctypes.byref(temp_rk_dt),
                ctypes.c_int(self.power),
                ctypes.c_int(self.power_test),
                ctypes.c_int(np.shape(self.coeff)[-1]),
                self.coeff.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                ctypes.c_int(len(self.weights)),
                self.weights.ctypes.data_as(
                    ctypes.POINTER(ctypes.c_double)
                ),
                self.weights_test.ctypes.data_as(
                    ctypes.POINTER(ctypes.c_double)
                ),
                ctypes.c_int(max_iteration),
                ctypes.c_int(min_iteration),
                ctypes.c_double(abs_tolerance),
                ctypes.c_double(rel_tolerance),
            )
            simulator.stats.simulation_time = temp_simulation_time.value 
            self.rk_dt = temp_rk_dt.value

        elif simulator.is_c_lib == False:
            (
                simulator.x,
                simulator.v,
                simulator.stats.simulation_time,
                self.rk_dt,
            ) = self._rk_embedded(
                objects_count,
                simulator.x,
                simulator.v,
                m,
                G,
                expected_time_scale,
                simulator.stats.simulation_time,
                self.rk_dt,
                self.power,
                self.power_test,
                self.coeff,
                self.weights,
                self.weights_test,
                max_iteration,
                min_iteration,
                abs_tolerance,
                rel_tolerance,
            )


    @staticmethod
    def _rk_embedded(
        objects_count: int,
        x,
        v,
        m,
        G,
        expected_time_scale: float,
        simulation_time,
        actual_dt,
        power,
        power_test,
        coeff,
        weights,
        weights_test,
        max_iteration: int,
        min_iteration: int,
        abs_tolerance: float,
        rel_tolerance: float,
    ):
        # Initializing
        t = simulation_time
        stages = len(weights)
        min_power = min([power, power_test])
        error_estimation_delta_weights = weights - weights_test

        # Safety factors for step-size control:
        safety_fac_max = 6.0
        safety_fac_min = 0.33
        safety_fac = 0.38 ** (1.0 / (1.0 + min_power))

        # Initialize vk and xk
        vk = np.zeros((stages, objects_count, 3))
        xk = np.zeros((stages, objects_count, 3))

        for i in range(max_iteration):
            # Calculate xk and vk
            vk[0] = acceleration(objects_count, x, m, G)
            xk[0] = np.copy(v)
            for stage in range(1, stages):
                temp_v = np.zeros((objects_count, 3))
                temp_x = np.zeros((objects_count, 3))
                for j in range(stage):
                    temp_v += coeff[stage - 1][j] * vk[j]
                    temp_x += coeff[stage - 1][j] * xk[j]
                vk[stage] = acceleration(objects_count, x + actual_dt * temp_x, m, G)
                xk[stage] = v + actual_dt * temp_v

            # Calculate x_1, v_1 and also delta x, delta v for error estimation
            temp_v = np.zeros((objects_count, 3))
            temp_x = np.zeros((objects_count, 3))
            error_estimation_delta_x = np.zeros((objects_count, 3))
            error_estimation_delta_v = np.zeros((objects_count, 3))
            for stage in range(stages):
                temp_v += weights[stage] * vk[stage]
                temp_x += weights[stage] * xk[stage]
                error_estimation_delta_v += (
                    error_estimation_delta_weights[stage] * vk[stage]
                )
                error_estimation_delta_x += (
                    error_estimation_delta_weights[stage] * xk[stage]
                )
            v_1 = v + actual_dt * temp_v
            x_1 = x + actual_dt * temp_x
            error_estimation_delta_v *= actual_dt
            error_estimation_delta_x *= actual_dt

            # Error calculation
            tolerance_scale_v = (
                abs_tolerance + np.maximum(np.abs(v), np.abs(v_1)) * rel_tolerance
            )
            tolerance_scale_x = (
                abs_tolerance + np.maximum(np.abs(x), np.abs(x_1)) * rel_tolerance
            )

            # Sum up all the elements of x/tol and v/tol, square and divide by the total number of elements
            sum = np.sum(np.square(error_estimation_delta_x / tolerance_scale_x)) + np.sum(
                np.square(error_estimation_delta_v / tolerance_scale_v)
            )
            error = (sum / (objects_count * 3 * 2)) ** 0.5

            if error <= 1 or actual_dt == expected_time_scale * 1e-12:
                t += actual_dt
                x = x_1
                v = v_1

            if error == 0.0: # Prevent extreme cases where the error is smaller than machine zero
                dt_new = actual_dt
            else:    
                dt_new = actual_dt * safety_fac / error ** (1.0 / (1.0 + min_power))
            # Prevent dt to be too small or too large relative to the last time step
            if dt_new > safety_fac_max * actual_dt:
                actual_dt = safety_fac_max * actual_dt
            elif dt_new < safety_fac_min * actual_dt:
                actual_dt = safety_fac_min * actual_dt
            else:
                actual_dt = dt_new

            if dt_new / expected_time_scale < 1e-12:
                actual_dt = expected_time_scale * 1e-12

            if i >= min_iteration and t > (simulation_time + expected_time_scale * 1e-5):
                return x, v, t, actual_dt

        # Return values once it reaches max iterations
        return x, v, t, actual_dt

    @staticmethod
    def _rk_embedded_initial_time_step(
        objects_count: int,
        power: int,
        x,
        v,
        a,
        m,
        G,
        abs_tolerance: float,
        rel_tolerance: float,
    ) -> float:
        """
        Calculate the initial time step for embedded rk method

        Modified: Return dt * 1e-2 since this function gives initial dt thats too large

        Reference: Moving Planets Around: An Introduction to N-Body Simulations Applied to Exoplanetary Systems
        Chapter 6, Page 92 - 94
        """
        tolerance_scale_x = abs_tolerance + rel_tolerance * np.abs(x)
        tolerance_scale_v = abs_tolerance + rel_tolerance * np.abs(v)
        sum_0 = np.sum(np.square(x / tolerance_scale_x)) + np.sum(
            np.square(v / tolerance_scale_v)
        )
        sum_1 = np.sum(np.square(v / tolerance_scale_x)) + np.sum(
            np.square(a / tolerance_scale_v)
        )
        d_0 = (sum_0 / (objects_count * 3 * 2)) ** 0.5
        d_1 = (sum_1 / (objects_count * 3 * 2)) ** 0.5

        if d_0 < 1e-5 or d_1 < 1e-5:
            dt_0 = 1e-4
        else:
            dt_0 = d_0 / d_1

        x_1 = x + (dt_0 / 100) * v
        v_1 = v + (dt_0 / 100) * a
        a_1 = acceleration(objects_count, x_1, m, G)

        # Calculate d_2 to measure how much the derivatives have changed.
        sum_2 = np.sum(np.square((v_1 - v) / tolerance_scale_x)) + np.sum(
            np.square((a_1 - a) / tolerance_scale_v)
        )
        d_2 = (sum_2 / (objects_count * 3 * 2)) ** 0.5 / dt_0

        if max(d_1, d_2) <= 1e-15:
            dt_1 = max(1e-6, dt_0 * 1e-3)
        else:
            dt_1 = (0.01 / max(d_1, d_2)) ** (1.0 / (1.0 + power))
        dt = min(100 * dt_0, dt_1)

        return dt * 1e-2

    @staticmethod
    def _rk_embedded_butcher_tableaus(order):
        """
        Butcher tableaus for embedded rk

        Reference: Moving Planets Around: An Introduction to N-Body Simulations Applied to Exoplanetary Systems
        Chapter 6, Page 100 - 101

        :raise ValueError: If order is not in [45, 54, 78, 65]
        :return: power, power_test, coeff, weights, weights_test
        :rtype: numpy.array
        """
        # Select integrator
        # 45) Runge-Kutta-Fehleberg 4(5)
        # 54) Dormand-Prince 5(4)
        # 78) Runge-Kutta-Fehlberg 7(8)
        # 65) Verner's method 6(5), DVERK

        match order:
            # RUNGE-KUTTA-FEHLBERG 4(5)
            case 45:
                # Order
                power = 4
                power_test = 5
                # nodes = np.array([1.0 / 4.0, 3.0 / 8.0, 12.0 / 13.0, 1.0, 0.5])
                coeff = np.array(
                    [
                        [1.0 / 4.0, 0.0, 0.0, 0.0, 0.0],
                        [3.0 / 32.0, 9.0 / 32.0, 0.0, 0.0, 0.0],
                        [1932.0 / 2197.0, -7200.0 / 2197.0, 7296.0 / 2197.0, 0.0, 0.0],
                        [439.0 / 216.0, -8.0, 3680.0 / 513.0, -845.0 / 4104.0, 0.0],
                        [-8.0 / 27.0, 2.0, -3544.0 / 2565.0, 1859.0 / 4104.0, -11.0 / 40.0],
                    ]
                )

                weights = np.array(
                    [25.0 / 216.0, 0.0, 1408.0 / 2565.0, 2197.0 / 4104.0, -0.2, 0.0]
                )
                weights_test = np.array(
                    [
                        16.0 / 135.0,
                        0.0,
                        6656.0 / 12825.0,
                        28561.0 / 56430.0,
                        -9.0 / 50.0,
                        2.0 / 55.0,
                    ]
                )

            # DORMAND-PRINCE 5(4)
            case 54:
                # order
                power = 5
                power_test = 4
                # nodes = np.array([1.0 / 5.0, 3.0 / 10.0, 4.0 / 5.0, 8.0 / 9.0, 1.0, 1.0])
                coeff = np.array(
                    [
                        [1.0 / 5.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                        [3.0 / 40.0, 9.0 / 40.0, 0.0, 0.0, 0.0, 0.0],
                        [44.0 / 45.0, -56.0 / 15.0, 32.0 / 9.0, 0.0, 0.0, 0.0],
                        [
                            19372.0 / 6561.0,
                            -25360.0 / 2187.0,
                            64448.0 / 6561.0,
                            -212.0 / 729.0,
                            0.0,
                            0.0,
                        ],
                        [
                            9017.0 / 3168.0,
                            -355.0 / 33.0,
                            46732.0 / 5247.0,
                            49.0 / 176.0,
                            -5103.0 / 18656.0,
                            0.0,
                        ],
                        [
                            35.0 / 384.0,
                            0.0,
                            500.0 / 1113.0,
                            125.0 / 192.0,
                            -2187.0 / 6784.0,
                            11.0 / 84.0,
                        ],
                    ]
                )
                weights = np.array(
                    [
                        35.0 / 384.0,
                        0.0,
                        500.0 / 1113.0,
                        125.0 / 192.0,
                        -2187.0 / 6784.0,
                        11.0 / 84.0,
                        0.0,
                    ]
                )
                weights_test = np.array(
                    [
                        5179.0 / 57600.0,
                        0.0,
                        7571.0 / 16695.0,
                        393.0 / 640.0,
                        -92097.0 / 339200.0,
                        187.0 / 2100.0,
                        1.0 / 40.0,
                    ]
                )

            # RUNGE-KUTTA-FEHLBERG 7(8)
            case 78:
                # Order
                power = 7
                power_test = 8
                # nodes = np.array(
                #     [
                #         2.0 / 27.0,
                #         1.0 / 9.0,
                #         1.0 / 6.0,
                #         5.0 / 12.0,
                #         1.0 / 2.0,
                #         5.0 / 6.0,
                #         1.0 / 6.0,
                #         2.0 / 3.0,
                #         1.0 / 3.0,
                #         1.0,
                #         0.0,
                #         1.0,
                #     ]
                # )
                coeff = np.array(
                    [
                        [2.0 / 27.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                        [
                            1.0 / 36.0,
                            1.0 / 12.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                        ],
                        [
                            1.0 / 24.0,
                            0.0,
                            1.0 / 8.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                        ],
                        [
                            5.0 / 12.0,
                            0.0,
                            -25.0 / 16.0,
                            25.0 / 16.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                        ],
                        [
                            1.0 / 20.0,
                            0.0,
                            0.0,
                            1.0 / 4.0,
                            1.0 / 5.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                        ],
                        [
                            -25.0 / 108.0,
                            0.0,
                            0.0,
                            125.0 / 108.0,
                            -65.0 / 27.0,
                            125.0 / 54.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                        ],
                        [
                            31.0 / 300.0,
                            0.0,
                            0.0,
                            0.0,
                            61.0 / 225.0,
                            -2.0 / 9.0,
                            13.0 / 900.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                        ],
                        [
                            2.0,
                            0.0,
                            0.0,
                            -53.0 / 6.0,
                            704.0 / 45.0,
                            -107.0 / 9.0,
                            67.0 / 90.0,
                            3.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                        ],
                        [
                            -91.0 / 108.0,
                            0.0,
                            0.0,
                            23.0 / 108.0,
                            -976.0 / 135.0,
                            311.0 / 54.0,
                            -19.0 / 60.0,
                            17.0 / 6.0,
                            -1.0 / 12.0,
                            0.0,
                            0.0,
                            0.0,
                        ],
                        [
                            2383.0 / 4100.0,
                            0.0,
                            0.0,
                            -341.0 / 164.0,
                            4496.0 / 1025.0,
                            -301.0 / 82.0,
                            2133.0 / 4100.0,
                            45.0 / 82.0,
                            45.0 / 164.0,
                            18.0 / 41.0,
                            0.0,
                            0.0,
                        ],
                        [
                            3.0 / 205.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            -6.0 / 41.0,
                            -3.0 / 205.0,
                            -3.0 / 41.0,
                            3.0 / 41.0,
                            6.0 / 41.0,
                            0.0,
                            0.0,
                        ],
                        [
                            -1777.0 / 4100.0,
                            0.0,
                            0.0,
                            -341.0 / 164.0,
                            4496.0 / 1025.0,
                            -289.0 / 82.0,
                            2193.0 / 4100.0,
                            51.0 / 82.0,
                            33.0 / 164.0,
                            19.0 / 41.0,
                            0.0,
                            1.0,
                        ],
                    ]
                )

                weights = np.array(
                    [
                        41.0 / 840.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        34.0 / 105.0,
                        9.0 / 35.0,
                        9.0 / 35.0,
                        9.0 / 280.0,
                        9.0 / 280.0,
                        41.0 / 840.0,
                        0.0,
                        0.0,
                    ]
                )
                weights_test = np.array(
                    [
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        34.0 / 105.0,
                        9.0 / 35.0,
                        9.0 / 35.0,
                        9.0 / 280.0,
                        9.0 / 280.0,
                        0.0,
                        41.0 / 840.0,
                        41.0 / 840.0,
                    ]
                )

            # VERNER 6(5) DVERK
            case 65:
                # Order
                power = 6
                power_test = 7
                # nodes = np.array(
                #     [1.0 / 6.0, 4.0 / 15.0, 2.0 / 3.0, 5.0 / 6.0, 1.0, 1.0 / 15.0, 1.0]
                # )
                coeff = np.array(
                    [
                        [1.0 / 6.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                        [4.0 / 75.0, 16.0 / 75.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                        [5.0 / 6.0, -8.0 / 3.0, 5.0 / 2.0, 0.0, 0.0, 0.0, 0.0],
                        [
                            -165.0 / 64.0,
                            55.0 / 6.0,
                            -425.0 / 64.0,
                            85.0 / 96.0,
                            0.0,
                            0.0,
                            0.0,
                        ],
                        [
                            12.0 / 5.0,
                            -8.0,
                            4015.0 / 612.0,
                            -11.0 / 36.0,
                            88.0 / 255.0,
                            0.0,
                            0.0,
                        ],
                        [
                            -8263.0 / 15000.0,
                            124.0 / 75.0,
                            -643.0 / 680.0,
                            -81.0 / 250.0,
                            2484.0 / 10625.0,
                            0.0,
                            0.0,
                        ],
                        [
                            3501.0 / 1720.0,
                            -300.0 / 43.0,
                            297275.0 / 52632.0,
                            -319.0 / 2322.0,
                            24068.0 / 84065.0,
                            0.0,
                            3850.0 / 26703.0,
                        ],
                    ]
                )

                weights = np.array(
                    [
                        3.0 / 40.0,
                        0.0,
                        875.0 / 2244.0,
                        23.0 / 72.0,
                        264.0 / 1955.0,
                        0.0,
                        125.0 / 11592.0,
                        43.0 / 616.0,
                    ]
                )
                weights_test = np.array(
                    [
                        13.0 / 160.0,
                        0.0,
                        2375.0 / 5984.0,
                        5.0 / 16.0,
                        12.0 / 85.0,
                        3.0 / 44.0,
                        0.0,
                        0.0,
                    ]
                )

            case _:
                raise ValueError

        return power, power_test, coeff, weights, weights_test

def acceleration(objects_count, x, m, G):
    """
    Calculate acceleration by a = - GM/r^3 vec{r}
    """
    # Allocate memory
    temp_a = np.zeros((objects_count * objects_count, 3))

    # Calculations
    for j in range(objects_count):
        for k in range(j + 1, objects_count):
            R = x[j] - x[k]
            temp_value = G * R / np.linalg.norm(R) ** 3 
            temp_a[j * objects_count + k] = -temp_value * m[k]
            temp_a[k * objects_count + j] = temp_value * m[j]

    temp_a = temp_a.reshape((objects_count, objects_count, 3))
    a = np.sum(temp_a, axis=1)

    return a

def compute_energy(objects_count, x, v, m, G):
    E = 0
    for j in range(objects_count):
        E += 0.5 * m[j] * np.linalg.norm(v[j]) ** 2
        for k in range(j + 1, objects_count):
            R = x[j] - x[k]
            norm = np.linalg.norm(R)
            if norm != 0:
                E -= G * m[j] * m[k] / norm 
            else:
                return np.nan
    return E

class Simulator:
    def __init__(self, grav_sim):
        self.is_c_lib = grav_sim.is_c_lib
        if self.is_c_lib == True:
            self.c_lib = grav_sim.c_lib

        self.stats = grav_sim.stats
        self.settings = grav_sim.settings

        self.m = np.array([])
        self.x = np.array([])
        self.v = np.array([])
        self.a = np.array([])

        self.fixed_step_size_integrator = FIXED_STEP_SIZE_INTEGRATOR()
        self.rk_embedded_integrator = RK_EMBEDDED()
        self.ias15_integrator = IAS15()

        self.is_initialize = True
        self.set_all_integrators_false()
        self.is_rk4 = True  # Default integrator
        self.current_integrator = "rk4"
        self.is_initialize_integrator = "rk4"

    def run_simulation(self, grav_sim):
        if self.is_initialize == True:
            self.initialize_problem(grav_sim)

        # Simple euler is enough when there is no interaction
        if self.stats.objects_count == 1:
            self.fixed_step_size_integrator.simulation(
                self,
                "euler",
                self.stats.objects_count,
                self.m,
                Grav_obj.G,
                self.settings.dt,
                self.settings.time_speed,
            )
            self.stats.simulation_time += (
                self.settings.dt * self.settings.time_speed
            )
        else:
            match self.current_integrator:
                # Fixed step size integrators
                case "euler" | "euler_cromer" | "rk4" | "leapfrog":
                    self.fixed_step_size_integrator.simulation(
                        self,
                        self.current_integrator,
                        self.stats.objects_count,
                        self.m,
                        Grav_obj.G,
                        self.settings.dt,
                        self.settings.time_speed,
                        )
                    
                    self.stats.simulation_time += (
                        self.settings.dt * self.settings.time_speed
                    )
                # Embedded RK methods
                case "rkf45" | "dopri" | "dverk" | "rkf78":
                    self.rk_embedded_integrator.simulation(
                        self,
                        self.stats.objects_count,
                        self.m,
                        Grav_obj.G,
                        self.settings.tolerance,
                        self.settings.tolerance,
                        self.settings.expected_time_scale,
                        self.settings.max_iteration,
                        self.settings.min_iteration,
                    )

                case "ias15":
                    self.ias15_integrator.simulation(
                        self,
                        self.stats.objects_count,
                        self.m,
                        Grav_obj.G,
                        self.settings.tolerance,
                        self.settings.expected_time_scale,
                        self.settings.max_iteration,
                        self.settings.min_iteration,
                    )

        if self.is_c_lib == True:
            try:
                self.stats.total_energy = self.c_lib.compute_energy(
                    ctypes.c_int(self.stats.objects_count),
                    self.x.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), 
                    self.v.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), 
                    self.m.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), 
                    ctypes.c_double(Grav_obj.G),
                )
            except:
                self.stats.total_energy = compute_energy(
                    self.stats.objects_count, self.x, self.v, self.m, Grav_obj.G
                )
        elif self.is_c_lib == False:
            self.stats.total_energy = compute_energy(
                self.stats.objects_count, self.x, self.v, self.m, Grav_obj.G
            )

    def initialize_problem(self, grav_sim):
        """
        Initialize x, v and m
        """
        objects_count = grav_sim.stats.objects_count
        self.x = np.zeros((objects_count, 3))
        self.v = np.zeros((objects_count, 3))
        self.m = np.zeros(objects_count)
        for j in range(objects_count):
            self.x[j] = np.array(
                [grav_sim.grav_objs.sprites()[j].params[f"r{i + 1}"] for i in range(3)]
            )
            self.v[j] = np.array(
                [grav_sim.grav_objs.sprites()[j].params[f"v{i + 1}"] for i in range(3)]
            )
            self.m[j] = grav_sim.grav_objs.sprites()[j].params["m"]

    def unload_value(self, grav_sim):
        """
        Unload the position and velocity values back the to main system
        """
        for j in range(self.stats.objects_count):
            grav_sim.grav_objs.sprites()[j].params["r1"] = self.x[j][0]
            grav_sim.grav_objs.sprites()[j].params["r2"] = self.x[j][1]
            grav_sim.grav_objs.sprites()[j].params["r3"] = self.x[j][2]
            grav_sim.grav_objs.sprites()[j].params["v1"] = self.v[j][0]
            grav_sim.grav_objs.sprites()[j].params["v2"] = self.v[j][1]
            grav_sim.grav_objs.sprites()[j].params["v3"] = self.v[j][2]

    def set_all_integrators_false(self):
        self.is_euler = False
        self.is_euler_cromer = False
        self.is_rk4 = False
        self.is_leapfrog = False
        self.is_rkf45 = False
        self.is_dopri = False
        self.is_dverk = False
        self.is_rkf78 = False
        self.is_ias15 = False

    def check_current_integrator(self):
        """
        Check what integrators are currently chosen
        """
        if self.is_euler == True:
            self.current_integrator = "euler"
        elif self.is_euler_cromer == True:
            self.current_integrator = "euler_cromer"
        elif self.is_rk4 == True:
            self.current_integrator = "rk4"
        elif self.is_leapfrog == True:
            self.current_integrator = "leapfrog"
        elif self.is_rkf45 == True:
            self.current_integrator = "rkf45"
        elif self.is_dopri == True:
            self.current_integrator = "dopri"
        elif self.is_dverk == True:
            self.current_integrator = "dverk"
        elif self.is_rkf78 == True:
            self.current_integrator = "rkf78"
        elif self.is_ias15 == True:
            self.current_integrator = "ias15"




class Stats:
    """Track statistics for Gravity Simulator."""

    STATSBOARD_FONT_SIZE = 20
    STATSBOARD_SIZE_X = 260
    STATSBOARD_SIZE_Y = 23
    FIXED_STEP_SIZE_INTEGRATORS_COLOR = (120, 233, 250)
    ADAPTIVE_STEP_SIZE_INTEGRATORS_COLOR = (173, 255, 47)

    def __init__(self, grav_sim) -> None:
        self.simulation_time = 0
        self.fps = grav_sim.clock.get_fps()
        self.total_energy = 0
        self.settings = grav_sim.settings
        self.is_paused = False
        self.is_holding_rclick = False
        self._create_statsboard(grav_sim)
        self._statsboard_init_print_msg()

    def update(self, grav_sim) -> None:
        self.fps = grav_sim.clock.get_fps()
        self.objects_count = len(grav_sim.grav_objs)

        if grav_sim.menu.main_menu_active == True:
            self.start_time = time.time()
        if self.is_paused == False:
            self.run_time = time.time() - self.start_time

        # Count time for the create new star function
        if self.is_holding_rclick == True:
            self.holding_rclick_time = time.time() - self.holding_rclick_start_time

    def reset(self, grav_sim) -> None:
        self.start_time = time.time()
        self.simulation_time = 0
        self.total_energy = 0
        grav_sim.simulator.is_initialize = True
        grav_sim.simulator.is_initialize_integrator = (
            grav_sim.simulator.current_integrator
        )
        grav_sim.camera._pos[0] = 0
        grav_sim.camera._pos[1] = 0

    def start_pause(self) -> None:
        self.paused_start_time = time.time()
        self.is_paused = True

    def end_pause(self) -> None:
        self.start_time -= self.paused_start_time - time.time()
        self.is_paused = False

    def start_holding_rclick(self) -> None:
        self.holding_rclick_start_time = time.time()
        self.is_holding_rclick = True

    def end_holding_rclick(self) -> None:
        self.is_holding_rclick = False

    def print_msg(self) -> None:
        self.fps_board.print_msg(f"FPS = {self.fps:2.1f}")
        self.obj_count_board.print_msg(f"Object = {self.objects_count}")
        self.simulation_time_board.print_msg(
            f"Simulation Time = {self.simulation_time / 365.256363004:.1e} years"
        )
        self.run_time_board.print_msg(f"Run time = {self.run_time:.0f} seconds")
        self.total_energy_board.print_msg(f"Total Energy = {self.total_energy:.3e}")

        self.star_img_scale_board.print_msg(
            f"Star Image Scale = {self.settings.star_img_scale}"
        )
        self.planet_img_scale_board.print_msg(
            f"Planet Image Scale = {self.settings.planet_img_scale}"
        )
        self.distance_scale_board.print_msg(
            f"Distance Scale = {self.settings.distance_scale}"
        )
        self.new_star_mass_scale_board.print_msg(
            f"New star mass scale = {self.settings.new_star_mass_scale:g}x"
        )
        self.new_star_speed_scale_board.print_msg(
            f"New star speed scale = {self.settings.new_star_speed_scale:d}x"
        )
        self.dt_board.print_msg(f"dt = {self.settings.dt:g} days / frame")
        self.time_speed_board.print_msg(f"Time Speed = {self.settings.time_speed}x")
        self.max_iteration_board.print_msg(
            f"Max iterations / frame = {self.settings.max_iteration}"
        )
        self.min_iteration_board.print_msg(
            f"Min iterations / frame = {self.settings.min_iteration}"
        )
        self.tolerance_board.print_msg(f"Tolerance = {self.settings.tolerance:g}")

    def draw(self, grav_sim) -> None:
        self.print_msg()
        self.fps_board.draw()
        self.obj_count_board.draw()
        self.simulation_time_board.draw()
        self.run_time_board.draw()
        self.total_energy_board.draw()

        self.parameters_board.draw()
        self.star_img_scale_board.draw()
        self.planet_img_scale_board.draw()
        self.distance_scale_board.draw()
        self.new_star_mass_scale_board.draw()
        self.new_star_speed_scale_board.draw()
        self.dt_board.draw()
        self.time_speed_board.draw()
        self.max_iteration_board.draw()
        self.min_iteration_board.draw()
        self.tolerance_board.draw()

        self.integrators_board.draw()
        self.fixed_step_size_board.draw()
        self.euler_board.draw()
        self.euler_cromer_board.draw()
        self.rk4_board.draw()
        self.leapfrog_board.draw()

        self.adaptive_step_size_board.draw()
        self.rkf45_board.draw()
        self.dopri_board.draw()
        self.dverk_board.draw()
        self.rkf78_board.draw()
        self.ias15_board.draw()

        # Visual indicator for currently changing parameter
        match self.settings.current_changing_parameter:
            case "star_img_scale":
                pygame.draw.circle(
                    grav_sim.screen,
                    "yellow",
                    (290, self.star_img_scale_board.rect.centery + 5),
                    4,
                )
            case "planet_img_scale":
                pygame.draw.circle(
                    grav_sim.screen,
                    "yellow",
                    (290, self.planet_img_scale_board.rect.centery + 5),
                    4,
                )
            case "distance_scale":
                pygame.draw.circle(
                    grav_sim.screen,
                    "yellow",
                    (290, self.distance_scale_board.rect.centery + 5),
                    4,
                )
            case "new_star_mass_scale":
                pygame.draw.circle(
                    grav_sim.screen,
                    "yellow",
                    (290, self.new_star_mass_scale_board.rect.centery + 5),
                    4,
                )
            case "new_star_speed_scale":
                pygame.draw.circle(
                    grav_sim.screen,
                    "yellow",
                    (290, self.new_star_speed_scale_board.rect.centery + 5),
                    4,
                )
            case "dt":
                pygame.draw.circle(
                    grav_sim.screen, "yellow", (290, self.dt_board.rect.centery + 5), 4
                )
            case "time_speed":
                pygame.draw.circle(
                    grav_sim.screen,
                    "yellow",
                    (290, self.time_speed_board.rect.centery + 5),
                    4,
                )
            case "max_iteration":
                pygame.draw.circle(
                    grav_sim.screen,
                    "yellow",
                    (290, self.max_iteration_board.rect.centery + 5),
                    4,
                )
            case "min_iteration":
                pygame.draw.circle(
                    grav_sim.screen,
                    "yellow",
                    (290, self.min_iteration_board.rect.centery + 5),
                    4,
                )
            case "tolerance":
                pygame.draw.circle(
                    grav_sim.screen,
                    "yellow",
                    (290, self.tolerance_board.rect.centery + 5),
                    4,
                )

        # Visual indicator for currently selected integrator
        match grav_sim.simulator.current_integrator:
            case "euler":
                pygame.draw.circle(
                    grav_sim.screen,
                    "green",
                    (290, self.euler_board.rect.centery + 5),
                    4,
                )
            case "euler_cromer":
                pygame.draw.circle(
                    grav_sim.screen,
                    "green",
                    (290, self.euler_cromer_board.rect.centery + 5),
                    4,
                )
            case "rk4":
                pygame.draw.circle(
                    grav_sim.screen, "green", (290, self.rk4_board.rect.centery + 5), 4
                )
            case "leapfrog":
                pygame.draw.circle(
                    grav_sim.screen,
                    "green",
                    (290, self.leapfrog_board.rect.centery + 5),
                    4,
                )
            case "rkf45":
                pygame.draw.circle(
                    grav_sim.screen,
                    "green",
                    (290, self.rkf45_board.rect.centery + 5),
                    4,
                )
            case "dopri":
                pygame.draw.circle(
                    grav_sim.screen,
                    "green",
                    (290, self.dopri_board.rect.centery + 5),
                    4,
                )
            case "dverk":
                pygame.draw.circle(
                    grav_sim.screen,
                    "green",
                    (290, self.dverk_board.rect.centery + 5),
                    4,
                )
            case "rkf78":
                pygame.draw.circle(
                    grav_sim.screen,
                    "green",
                    (290, self.rkf78_board.rect.centery + 5),
                    4,
                )
            case "ias15":
                pygame.draw.circle(
                    grav_sim.screen,
                    "green",
                    (290, self.ias15_board.rect.centery + 5),
                    4,
                )
            
    def check_button(self, grav_sim, mouse_pos) -> None:
        """Check if there is any click on the buttons"""
        if self.settings.is_hide_gui == False:
            if self.star_img_scale_board.rect.collidepoint(mouse_pos):
                self.settings.set_all_parameters_changing_false()
                self.settings.is_changing_star_img_scale = True
            if self.planet_img_scale_board.rect.collidepoint(mouse_pos):
                self.settings.set_all_parameters_changing_false()
                self.settings.is_changing_planet_img_scale = True
            if self.distance_scale_board.rect.collidepoint(mouse_pos):
                self.settings.set_all_parameters_changing_false()
                self.settings.is_changing_distance_scale = True
            if self.new_star_mass_scale_board.rect.collidepoint(mouse_pos):
                self.settings.set_all_parameters_changing_false()
                self.settings.is_changing_new_star_mass_scale = True
            if self.new_star_speed_scale_board.rect.collidepoint(mouse_pos):
                self.settings.set_all_parameters_changing_false()
                self.settings.is_changing_new_star_speed_scale = True
            if self.dt_board.rect.collidepoint(mouse_pos):
                self.settings.set_all_parameters_changing_false()
                self.settings.is_changing_dt = True
            if self.time_speed_board.rect.collidepoint(mouse_pos):
                self.settings.set_all_parameters_changing_false()
                self.settings.is_changing_time_speed = True
            if self.max_iteration_board.rect.collidepoint(mouse_pos):
                self.settings.set_all_parameters_changing_false()
                self.settings.is_changing_max_iteration = True
            if self.min_iteration_board.rect.collidepoint(mouse_pos):
                self.settings.set_all_parameters_changing_false()
                self.settings.is_changing_min_iteration = True
            if self.tolerance_board.rect.collidepoint(mouse_pos):
                self.settings.set_all_parameters_changing_false()
                self.settings.is_changing_tolerance = True

            if self.euler_board.rect.collidepoint(mouse_pos):
                grav_sim.simulator.set_all_integrators_false()
                grav_sim.simulator.is_euler = True
                grav_sim.simulator.is_initialize = True
                grav_sim.simulator.is_initialize_integrator = "euler"
            if self.euler_cromer_board.rect.collidepoint(mouse_pos):
                grav_sim.simulator.set_all_integrators_false()
                grav_sim.simulator.is_euler_cromer = True
                grav_sim.simulator.is_initialize = True
                grav_sim.simulator.is_initialize_integrator = "euler_cromer"
            if self.rk4_board.rect.collidepoint(mouse_pos):
                grav_sim.simulator.set_all_integrators_false()
                grav_sim.simulator.is_rk4 = True
                grav_sim.simulator.is_initialize = True
                grav_sim.simulator.is_initialize_integrator = "rk4"
            if self.leapfrog_board.rect.collidepoint(mouse_pos):
                grav_sim.simulator.set_all_integrators_false()
                grav_sim.simulator.is_leapfrog = True
                grav_sim.simulator.is_initialize = True
                grav_sim.simulator.is_initialize_integrator = "leapfrog"

            if self.rkf45_board.rect.collidepoint(mouse_pos):
                grav_sim.simulator.set_all_integrators_false()
                grav_sim.simulator.is_rkf45 = True
                grav_sim.simulator.is_initialize = True
                grav_sim.simulator.is_initialize_integrator = "rkf45"
            if self.dopri_board.rect.collidepoint(mouse_pos):
                grav_sim.simulator.set_all_integrators_false()
                grav_sim.simulator.is_dopri = True
                grav_sim.simulator.is_initialize = True
                grav_sim.simulator.is_initialize_integrator = "dopri"
            if self.dverk_board.rect.collidepoint(mouse_pos):
                grav_sim.simulator.set_all_integrators_false()
                grav_sim.simulator.is_dverk = True
                grav_sim.simulator.is_initialize = True
                grav_sim.simulator.is_initialize_integrator = "dverk"
            if self.rkf78_board.rect.collidepoint(mouse_pos):
                grav_sim.simulator.set_all_integrators_false()
                grav_sim.simulator.is_rkf78 = True
                grav_sim.simulator.is_initialize = True
                grav_sim.simulator.is_initialize_integrator = "rkf78"
            if self.ias15_board.rect.collidepoint(mouse_pos):
                grav_sim.simulator.set_all_integrators_false()
                grav_sim.simulator.is_ias15 = True
                grav_sim.simulator.is_initialize = True
                grav_sim.simulator.is_initialize_integrator = "ias15"

    def _statsboard_init_print_msg(self) -> None:
        self.parameters_board.print_msg("Parameters: (Click below to select)")
        self.integrators_board.print_msg("Integrators: (Click below to select)")
        self.fixed_step_size_board.print_msg("(Fixed Step Size)")
        self.euler_board.print_msg("Euler")
        self.euler_cromer_board.print_msg("Euler-Cromer")
        self.rk4_board.print_msg("4th order Runge-Kutta")
        self.leapfrog_board.print_msg("Leapfrog (Verlet)")
        self.adaptive_step_size_board.print_msg("(Adaptive Step Size)")
        self.rkf45_board.print_msg("Runge-Kutta-Fehleberg 4(5)")
        self.dopri_board.print_msg("Dormand-Prince 5(4)")
        self.dverk_board.print_msg("Verner's method 6(5) DVERK")
        self.rkf78_board.print_msg("Runge-Kutta-Fehlberg 7(8)")
        self.ias15_board.print_msg("IAS15")

    @classmethod
    def _create_statsboard(self, grav_sim) -> None:
        self.fps_board = Text_box(
            grav_sim,
            self.STATSBOARD_FONT_SIZE,
            size_x=self.STATSBOARD_SIZE_X,
            size_y=self.STATSBOARD_SIZE_Y,
            font="Manrope",
            text_box_left_top=(10, 0),
        )
        self.obj_count_board = Text_box(
            grav_sim,
            self.STATSBOARD_FONT_SIZE,
            size_x=self.STATSBOARD_SIZE_X,
            size_y=self.STATSBOARD_SIZE_Y,
            font="Manrope",
            text_box_left_top=(10, 23),
        )

        self.simulation_time_board = Text_box(
            grav_sim,
            self.STATSBOARD_FONT_SIZE,
            size_x=self.STATSBOARD_SIZE_X,
            size_y=self.STATSBOARD_SIZE_Y,
            font="Manrope",
            text_box_left_top=(10, 46),
        )
        self.run_time_board = Text_box(
            grav_sim,
            self.STATSBOARD_FONT_SIZE,
            size_x=self.STATSBOARD_SIZE_X,
            size_y=self.STATSBOARD_SIZE_Y,
            font="Manrope",
            text_box_left_top=(10, 69),
        )
        self.total_energy_board = Text_box(
            grav_sim,
            self.STATSBOARD_FONT_SIZE,
            size_x=self.STATSBOARD_SIZE_X,
            size_y=self.STATSBOARD_SIZE_Y,
            font="Manrope",
            text_box_left_top=(10, 92),
        )

        self.parameters_board = Text_box(
            grav_sim,
            self.STATSBOARD_FONT_SIZE,
            size_x=self.STATSBOARD_SIZE_X,
            size_y=self.STATSBOARD_SIZE_Y,
            font="Manrope",
            text_box_left_top=(10, 138),
        )
        self.star_img_scale_board = Text_box(
            grav_sim,
            self.STATSBOARD_FONT_SIZE,
            size_x=self.STATSBOARD_SIZE_X,
            size_y=self.STATSBOARD_SIZE_Y,
            font="Manrope",
            text_box_left_top=(10, 161),
        )
        self.planet_img_scale_board = Text_box(
            grav_sim,
            self.STATSBOARD_FONT_SIZE,
            size_x=self.STATSBOARD_SIZE_X,
            size_y=self.STATSBOARD_SIZE_Y,
            font="Manrope",
            text_box_left_top=(10, 184),
        )
        self.distance_scale_board = Text_box(
            grav_sim,
            self.STATSBOARD_FONT_SIZE,
            size_x=self.STATSBOARD_SIZE_X,
            size_y=self.STATSBOARD_SIZE_Y,
            font="Manrope",
            text_box_left_top=(10, 207),
        )
        self.new_star_mass_scale_board = Text_box(
            grav_sim,
            self.STATSBOARD_FONT_SIZE,
            size_x=self.STATSBOARD_SIZE_X,
            size_y=self.STATSBOARD_SIZE_Y,
            font="Manrope",
            text_box_left_top=(10, 230),
        )
        self.new_star_speed_scale_board = Text_box(
            grav_sim,
            self.STATSBOARD_FONT_SIZE,
            size_x=self.STATSBOARD_SIZE_X,
            size_y=self.STATSBOARD_SIZE_Y,
            font="Manrope",
            text_box_left_top=(10, 253),
        )
        self.dt_board = Text_box(
            grav_sim,
            self.STATSBOARD_FONT_SIZE,
            size_x=self.STATSBOARD_SIZE_X,
            size_y=self.STATSBOARD_SIZE_Y,
            font="Manrope",
            text_box_left_top=(10, 276),
            text_color=self.FIXED_STEP_SIZE_INTEGRATORS_COLOR,
        )
        self.time_speed_board = Text_box(
            grav_sim,
            self.STATSBOARD_FONT_SIZE,
            size_x=self.STATSBOARD_SIZE_X,
            size_y=self.STATSBOARD_SIZE_Y,
            font="Manrope",
            text_box_left_top=(10, 299),
            text_color=self.FIXED_STEP_SIZE_INTEGRATORS_COLOR,
        )
        self.max_iteration_board = Text_box(
            grav_sim,
            self.STATSBOARD_FONT_SIZE,
            size_x=self.STATSBOARD_SIZE_X,
            size_y=self.STATSBOARD_SIZE_Y,
            font="Manrope",
            text_box_left_top=(10, 322),
            text_color=self.ADAPTIVE_STEP_SIZE_INTEGRATORS_COLOR,
        )
        self.min_iteration_board = Text_box(
            grav_sim,
            self.STATSBOARD_FONT_SIZE,
            size_x=self.STATSBOARD_SIZE_X,
            size_y=self.STATSBOARD_SIZE_Y,
            font="Manrope",
            text_box_left_top=(10, 345),
            text_color=self.ADAPTIVE_STEP_SIZE_INTEGRATORS_COLOR,
        )
        self.tolerance_board = Text_box(
            grav_sim,
            self.STATSBOARD_FONT_SIZE,
            size_x=self.STATSBOARD_SIZE_X,
            size_y=self.STATSBOARD_SIZE_Y,
            font="Manrope",
            text_box_left_top=(10, 368),
            text_color=self.ADAPTIVE_STEP_SIZE_INTEGRATORS_COLOR,
        )

        self.integrators_board = Text_box(
            grav_sim,
            self.STATSBOARD_FONT_SIZE,
            size_x=self.STATSBOARD_SIZE_X,
            size_y=self.STATSBOARD_SIZE_Y,
            font="Manrope",
            text_box_left_top=(10, 414),
        )
        self.fixed_step_size_board = Text_box(
            grav_sim,
            self.STATSBOARD_FONT_SIZE,
            size_x=self.STATSBOARD_SIZE_X,
            size_y=self.STATSBOARD_SIZE_Y,
            font="Manrope",
            text_box_left_top=(10, 437),
            text_color=self.FIXED_STEP_SIZE_INTEGRATORS_COLOR,
        )
        self.euler_board = Text_box(
            grav_sim,
            self.STATSBOARD_FONT_SIZE,
            size_x=self.STATSBOARD_SIZE_X,
            size_y=self.STATSBOARD_SIZE_Y,
            font="Manrope",
            text_box_left_top=(10, 460),
        )
        self.euler_cromer_board = Text_box(
            grav_sim,
            self.STATSBOARD_FONT_SIZE,
            size_x=self.STATSBOARD_SIZE_X,
            size_y=self.STATSBOARD_SIZE_Y,
            font="Manrope",
            text_box_left_top=(10, 483),
        )
        self.rk4_board = Text_box(
            grav_sim,
            self.STATSBOARD_FONT_SIZE,
            size_x=self.STATSBOARD_SIZE_X,
            size_y=self.STATSBOARD_SIZE_Y,
            font="Manrope",
            text_box_left_top=(10, 506),
        )
        self.leapfrog_board = Text_box(
            grav_sim,
            self.STATSBOARD_FONT_SIZE,
            size_x=self.STATSBOARD_SIZE_X,
            size_y=self.STATSBOARD_SIZE_Y,
            font="Manrope",
            text_box_left_top=(10, 529),
        )
        self.adaptive_step_size_board = Text_box(
            grav_sim,
            self.STATSBOARD_FONT_SIZE,
            size_x=self.STATSBOARD_SIZE_X,
            size_y=self.STATSBOARD_SIZE_Y,
            font="Manrope",
            text_box_left_top=(10, 575),
            text_color=self.ADAPTIVE_STEP_SIZE_INTEGRATORS_COLOR,
        )
        self.rkf45_board = Text_box(
            grav_sim,
            self.STATSBOARD_FONT_SIZE,
            size_x=self.STATSBOARD_SIZE_X,
            size_y=self.STATSBOARD_SIZE_Y,
            font="Manrope",
            text_box_left_top=(10, 598),
        )
        self.dopri_board = Text_box(
            grav_sim,
            self.STATSBOARD_FONT_SIZE,
            size_x=self.STATSBOARD_SIZE_X,
            size_y=self.STATSBOARD_SIZE_Y,
            font="Manrope",
            text_box_left_top=(10, 621),
        )
        self.dverk_board = Text_box(
            grav_sim,
            self.STATSBOARD_FONT_SIZE,
            size_x=self.STATSBOARD_SIZE_X,
            size_y=self.STATSBOARD_SIZE_Y,
            font="Manrope",
            text_box_left_top=(10, 644),
        )
        self.rkf78_board = Text_box(
            grav_sim,
            self.STATSBOARD_FONT_SIZE,
            size_x=self.STATSBOARD_SIZE_X,
            size_y=self.STATSBOARD_SIZE_Y,
            font="Manrope",
            text_box_left_top=(10, 667),
        )
        self.ias15_board = Text_box(
            grav_sim,
            self.STATSBOARD_FONT_SIZE,
            size_x=self.STATSBOARD_SIZE_X,
            size_y=self.STATSBOARD_SIZE_Y,
            font="Manrope",
            text_box_left_top=(10, 713),
        )

if __name__ == "__main__":
    grav_sim = GravitySimulator()
    asyncio.run(grav_sim.run_prog())
