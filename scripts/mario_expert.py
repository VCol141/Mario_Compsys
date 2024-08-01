"""
This the primary class for the Mario Expert agent. It contains the logic for the Mario Expert agent to play the game and choose actions.

Your goal is to implement the functions and methods required to enable choose_action to select the best action for the agent to take.

Original Mario Manual: https://www.thegameisafootarcade.com/wp-content/uploads/2017/04/Super-Mario-Land-Game-Manual.pdf
"""

import json
import logging
import random

import cv2
from mario_environment import MarioEnvironment
from pyboy.utils import WindowEvent

import pygame
from pygame.locals import *

import numpy as np
import math as mt

from scipy.signal import correlate2d

mario_x_global = 0
mario_y_global = 0
goomba_in_scene = 0

class MarioController(MarioEnvironment):
    """
    The MarioController class represents a controller for the Mario game environment.

    You can build upon this class all you want to implement your Mario Expert agent.

    Args:
        act_freq (int): The frequency at which actions are performed. Defaults to 10.
        emulation_speed (int): The speed of the game emulation. Defaults to 0.
        headless (bool): Whether to run the game in headless mode. Defaults to False.
    """

    def __init__(
        self,
        act_freq: int = 10,
        emulation_speed: int = 1,
        headless: bool = False,
    ) -> None:
        super().__init__(
            act_freq=act_freq,
            emulation_speed=emulation_speed,
            headless=headless,
        )

        self.act_freq = act_freq

        # Example of valid actions based purely on the buttons you can press
        valid_actions: list[WindowEvent] = [
            WindowEvent.PRESS_ARROW_DOWN,
            WindowEvent.PRESS_ARROW_LEFT,
            WindowEvent.PRESS_ARROW_RIGHT,
            WindowEvent.PRESS_ARROW_UP,
            WindowEvent.PRESS_BUTTON_A,
            WindowEvent.PRESS_BUTTON_B,
        ]

        button_actions: list[WindowEvent] = [
            WindowEvent.QUIT,                       #  0
            WindowEvent.PRESS_ARROW_UP,             #  1
            WindowEvent.PRESS_ARROW_DOWN,           #  2
            WindowEvent.PRESS_ARROW_RIGHT,          #  3
            WindowEvent.PRESS_ARROW_LEFT,           #  4
            WindowEvent.PRESS_BUTTON_A,             #  5
            WindowEvent.PRESS_BUTTON_B,             #  6
            WindowEvent.PRESS_BUTTON_SELECT,        #  7
            WindowEvent.PRESS_BUTTON_START,         #  8
        ]

        release_button: list[WindowEvent] = [
            WindowEvent.RELEASE_ARROW_DOWN,
            WindowEvent.RELEASE_ARROW_LEFT,
            WindowEvent.RELEASE_ARROW_RIGHT,
            WindowEvent.RELEASE_ARROW_UP,
            WindowEvent.RELEASE_BUTTON_A,
            WindowEvent.RELEASE_BUTTON_B,
        ]

        self.valid_actions = valid_actions
        self.release_button = release_button
        self.buttton_actions = button_actions

    def run_action(self, actions=[0], delay=5) -> None:
        """
        This is a very basic example of how this function could be implemented

        As part of this assignment your job is to modify this function to better suit your needs

        You can change the action type to whatever you want or need just remember the base control of the game is pushing buttons
        """

        # Simply toggles the buttons being on or off for a duration of act_freq

        if delay < 5:
            delay = 5
        
        for action in actions:
            self.pyboy.send_input(action)
        
        for _ in range(delay):
            self.pyboy.tick()

        for action in actions:
            self.pyboy.send_input(action + 8)

        for _ in range(5):
            self.pyboy.tick()


class MarioExpert:
    """
    The MarioExpert class represents an expert agent for playing the Mario game.

    Edit this class to implement the logic for the Mario Expert agent to play the game.

    Do NOT edit the input parameters for the __init__ method.

    Args:
        results_path (str): The path to save the results and video of the gameplay.
        headless (bool, optional): Whether to run the game in headless mode. Defaults to False.
    """

    def __init__(self, results_path: str, headless=False):
        self.results_path = results_path

        self.environment = MarioController(headless=headless)

        self.video = None

        pygame.init()
        # self.screen = pygame.display.set_mode((640, 480))
        # pygame.display.set_caption('Mario Expert')
    

    def find_mario(self):
        global mario_x_global, mario_y_global

        game_area = self.environment.game_area()

        [mario_y, mario_x] = np.where(game_area == 1)

        if mario_x.size > 0 and mario_y.size > 0:
            mario_x_global = (np.max(mario_x) + np.min(mario_x)) / 2
            mario_y_global = (np.max(mario_y) + np.min(mario_y)) / 2
            return mario_x_global, mario_y_global
        
        return (-1, -1)
        

    def find_goomb(self):
        global mario_x_global, mario_y_global, goomba_in_scene

        game_area = self.environment.game_area()
        is_goomb = np.array(np.where(game_area[1:int(mario_y_global + 1.5), int(mario_x_global):int(mario_x_global+5)] == 15)).size > 0 or np.array(np.where(game_area[1:int(mario_y_global - 0.5), int(mario_x_global):20] == 15)).size > 0
        delay = 10

        initial_sweep = np.array(np.where(game_area[int(mario_y_global + 0.5) , :] == 15))

        # if initial_sweep.size == 0 or np.array(np.where(game_area[int(mario_y_global+0.5), range(0,int(mario_y_global + 0.5))])).size == 0:
        #     return (False, 0)
        
        # array = np.min(initial_sweep)

        print(game_area[1:int(mario_y_global - 1.5), int(mario_x_global):20])

        if is_goomb ==  True:
            goomba_in_scene = 3

        return(is_goomb, delay)


        
    def find_wall(self):
        global mario_x_global, mario_y_global

        game_area = self.environment.game_area()
        is_wall = False
        delay = 12

        initial_sweep = np.array(np.where(game_area[:, int(mario_x_global + 1.5)] == 10))

        if initial_sweep.size == 0 or np.array(np.where(game_area[int(mario_y_global),:] == 10)).size == 0:
            return (False, 0)
        
        array = np.min(initial_sweep)

        wall_height = 1.5 + (mario_y_global - array)

        if (wall_height > 0):
            is_wall = True

        delay = int(((11-5)/(4-3)) * wall_height)
        
        return (is_wall, delay)
    
    def find_tunnel(self):
        global mario_x_global, mario_y_global

        game_area = self.environment.game_area()
        is_tunnel = False
        delay = 12

        initial_sweep = np.array(np.where(game_area[:, int(mario_x_global + 1.5)] == 14))


        if initial_sweep.size == 0:
            return (False, 0)
        
        array = np.min(initial_sweep)

        wall_height = 2 + (mario_y_global - array)

        if (wall_height > 0):
            is_tunnel = True

        delay = int(((11-5)/(4-3)) * wall_height)
        
        return (is_tunnel, delay)
    


    def choose_action(self):
        global last, jump, goomba_in_scene
        state = self.environment.game_state()
        frame = self.environment.grab_frame()
        game_area = self.environment.game_area()

        # Implement your code here to choose the best action
        # time.sleep(0.1)

        output_action = ([0], 0)


        [mario_x, mario_y] = self.find_mario()
        [is_goomb, goomb_delay] = self.find_goomb()

        [is_wall, wall_delay] = self.find_wall()
        [is_tunnel, tunnel_delay] = self.find_tunnel()

        if (is_goomb == False and goomba_in_scene == False):
            output_action = ([self.environment.buttton_actions.index(WindowEvent.PRESS_ARROW_RIGHT)], 10)
        if (is_wall):
            output_action = ([self.environment.buttton_actions.index(WindowEvent.PRESS_BUTTON_A), self.environment.buttton_actions.index(WindowEvent.PRESS_ARROW_RIGHT)], wall_delay)
        if (is_tunnel):
            output_action = ([self.environment.buttton_actions.index(WindowEvent.PRESS_BUTTON_A), self.environment.buttton_actions.index(WindowEvent.PRESS_ARROW_RIGHT)], tunnel_delay)
        if (is_goomb == True or goomba_in_scene != 0):
            output_action = ([self.environment.buttton_actions.index(WindowEvent.PRESS_BUTTON_A)], goomb_delay)
            goomba_in_scene -= 1

            if goomba_in_scene < 0:
                goomba_in_scene = 0

        return output_action


    def step(self):
        """
        Modify this function as required to implement the Mario Expert agent's logic.

        This is just a very basic example
        """

        [action, delay] = self.choose_action()

        self.environment.run_action(action, delay)

        # self.environment.pyboy.tick()


    def play(self):
        """
        Do NOT edit this method.
        """
        self.environment.reset()

        frame = self.environment.grab_frame()
        height, width, _ = frame.shape

        self.start_video(f"{self.results_path}/mario_expert.mp4", width, height)

        while not self.environment.get_game_over():
            frame = self.environment.grab_frame()
            self.video.write(frame)

            self.step()

        final_stats = self.environment.game_state()
        logging.info(f"Final Stats: {final_stats}")

        with open(f"{self.results_path}/results.json", "w", encoding="utf-8") as file:
            json.dump(final_stats, file)

        self.stop_video()

    def start_video(self, video_name, width, height, fps=30):
        """
        Do NOT edit this method.
        """
        self.video = cv2.VideoWriter(
            video_name, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
        )

    def stop_video(self) -> None:
        """
        Do NOT edit this method.
        """
        self.video.release()
