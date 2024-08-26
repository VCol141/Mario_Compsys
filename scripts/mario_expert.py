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
        act_freq: int = 1,
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

        if actions == [-1]:
            for i in range(WindowEvent.RELEASE_ARROW_UP, WindowEvent.RELEASE_BUTTON_START):
                self.pyboy.send_input(i)
                return

        if delay < 5 and delay > 0:
            delay = 5
        
        for action in actions:
            self.pyboy.send_input(action)

        if (delay == 0):
            return
        
        for _ in range(delay):
            self.pyboy.tick()

        for action in actions:
            self.pyboy.send_input(action + 8)

        for _ in range(5):
            self.pyboy.tick()


class Enviroment:
    def __init__(self, enviroment):
        self.controller = enviroment
        self.game_area = enviroment.game_area

        self.mario_x = 0
        self.mario_y = 0

        self.bad_guy_pos = [[0]]
    

    def find_mario(self):

        [mario_y, mario_x] = np.where(self.game_area() == 1)

        if mario_x.size > 0 and mario_y.size > 0:
            self.mario_x = (np.max(mario_x) + np.min(mario_x)) / 2
            self.mario_y = (np.max(mario_y) + np.min(mario_y)) / 2
        
        return self.mario_x, self.mario_y

    

    def find_bad_guy(self, id):
        badx, bady = np.where(self.game_area() == id)

        if badx.size == 0:
            return

        self.bad_guy_pos = [0 for y in range(badx.size)]

        for index in range(badx.size):
            self.bad_guy_pos[index] = np.array((badx[index], bady[index]))
        
        return self.bad_guy_pos

    

    def find_wall(self):
        delay = 12
        is_wall = False

        initial_sweep = np.array(np.where(self.game_area()[:, int(self.mario_x + 1.5)] == 10))

        if initial_sweep.size == 0 or np.array(np.where(self.game_area()[int(self.mario_y),:] == 10)).size == 0:
            return (is_wall, 0)
        
        array = np.min(initial_sweep)

        wall_height = 1.5 + (self.mario_y - array)

        if (wall_height > 0):
            is_wall = True

        delay = int(((11-5)/(4-3)) * wall_height)
        
        return (is_wall, delay)
    
    def find_tunnel(self):
        is_tunnel = False
        delay = 12

        initial_sweep = np.array(np.where(self.game_area()[:, int(self.mario_x + 1.5)] == 14))


        if initial_sweep.size == 0:
            return (False, 0)
        
        array = np.min(initial_sweep)

        wall_height = 2 + (self.mario_y - array)

        if (wall_height > 0):
            is_tunnel = True

        delay = int(((11-5)/(4-3)) * wall_height)
        
        return (is_tunnel, delay)
    

    def find_hole(self):
        is_hole = False

        initial_sweep = np.array(np.where(self.game_area()[range(14,16),:] == 0))

        # print(self.game_area()[range(8, 16), :])

        if initial_sweep.size <= 1:
            return(False, 0)
        
        hole = initial_sweep[1]

        if abs(self.mario_x - hole[0]) <= 3:
            is_hole = True

        return(is_hole, 10)
    
    def find_drop(self):

        if np.array(np.where(self.game_area()[range(14,16),:] == 0)).size <= 1:
            return(0, 0)
        
        move = 0
        delay = 5
        check_y = round(self.mario_y + 0.5)
        check_x = round(self.mario_x + 1)

        mock_game_area = self.game_area()

        while check_x < 20:

            if check_y >= 16:
                move  = 2
                delay = 12
                break

            current_block = self.game_area()[check_y][check_x]

            if current_block == 0:
                mock_game_area[check_y][check_x] = 99
            elif current_block == 10 or current_block == 14 or current_block == 12:
                break
            
            check_y += 1

        if (check_y - self.mario_y) > 7 and move == 0:
            move = 1
            delay = 50
            for delay in range(5):
                self.controller.pyboy.tick()

        return (move, delay)


    def find_special_blocks(self):
        goombx, goomby = np.where(self.game_area() == 13)

        if goombx.size == 0:
            return

        self.goomba_pos = [0 for y in range(goombx.size)]

        for index in range(goombx.size):
            self.goomba_pos[index] = np.array((goombx[index], goomby[index]))
        
        return self.goomba_pos
    

    def bad_guy_coming(self, id):
        is_bad = False
        check_y = round(self.mario_y + 0.5)
        check_x = round(self.mario_x + 1)

        mock_game_area = self.game_area()

        if np.array(self.find_bad_guy(15)).size <= 1:
            return is_bad

        while check_x < 20:

            if check_y >= 16:
                return is_bad
            
            current_block = self.game_area()[check_y][check_x]

            if current_block == 0:
                mock_game_area[check_y][check_x] = 99
            elif current_block == 14 or current_block == 10:
                check_y -= 1
                check_x -= 2
            elif current_block == id:
                is_bad = True
                mock_game_area[check_y][check_x] = 999
                break
            
            check_x += 1
        
        return is_bad
    

    def path_to_special(self):
        check_y = round(self.mario_y + 0.5)
        is_block = False
        is_above = False

        blocks = self.find_special_blocks()

        if np.array(blocks).size == 0:
            return

        block = blocks[0]
        block_x, block_y = block

        mock_game_area = self.game_area()

        while not is_block:
            
            if round(self.mario_x) < block_x:
                check_x = round(self.mario_x + 1)
                go_left = False
            elif round(self.mario_x) > block_x:
                check_x = round(self.mario_x - 1)
                go_left = True
            else:
                is_above = True

            current_block = self.game_area()[check_y][check_x]

            if current_block == 0:

                mock_game_area()[check_y][check_x] = 99

            elif current_block == 14 or current_block == 10:
                if self.game_area()[check_y - 1][check_x] == 0:
                    check_x
                
            

            if go_left and (block_y != self.mario_y):
                check_x -= 1
            elif (block_y != self.mario_y):
                check_x += 1
            elif (self.mario_y > block_y):
                print("none")


class Actions:
    def __init__(self, enviroment, positions):
        self.controller = enviroment
        self.game_area = enviroment.game_area
        self.positions = positions
    

    def move_normally(self):
        [is_wall, wall_delay] = self.positions.find_wall()
        [is_tunnel, tunnel_delay] = self.positions.find_tunnel()
        [move, drop_delay] = self.positions.find_drop()


        if is_wall:
            self.controller.run_action([WindowEvent.PRESS_BUTTON_A, WindowEvent.PRESS_ARROW_RIGHT], wall_delay)
        elif is_tunnel:
            self.controller.run_action([WindowEvent.PRESS_BUTTON_A, WindowEvent.PRESS_ARROW_RIGHT], tunnel_delay)
        elif move == 1:
            self.controller.run_action([WindowEvent.RELEASE_ARROW_RIGHT], drop_delay)
        elif move == 2:
            self.controller.run_action([WindowEvent.PRESS_BUTTON_A, WindowEvent.PRESS_ARROW_RIGHT], drop_delay)
        else:
            self.controller.run_action([WindowEvent.PRESS_ARROW_RIGHT], 0)
    

    def kill_goomb(self):

        # Get the positions of mario and any goomba
        [mario_x, mario_y] = self.positions.find_mario()
        goombas = self.positions.find_bad_guy(15)

        # Return false if no goomba
        if self.positions.bad_guy_coming(15) is False:
            return False
        
        self.controller.run_action([WindowEvent.RELEASE_ARROW_RIGHT], 0)
        
        # If there are goomba get the x and y position of the first goomba
        [goomb_y, goomb_x] = np.array(goombas[0])

        if abs(mario_x - goomb_x) < 2:
            self.controller.run_action([WindowEvent.PRESS_BUTTON_A, 5])

            for tick in range(15):
                self.controller.pyboy.tick()
            return True
        elif abs(mario_y - goomb_y) < 2:
            return True
    

    def go_to_block(self):
        [mario_x, mario_y] = self.positions.find_mario()

        # print(self.game_area())
    
        if np.array(self.positions.find_special_blocks()).size <= 1:
            return

        is_smallest = 1000

        for blocks in self.positions.find_special_blocks():
            diffx = mario_x - blocks[1]
            diffy = mario_y - blocks[0]

            if mt.sqrt(mt.pow(diffx,2) + mt.pow(diffy, 2)) < is_smallest:
                diff_x = mario_x - blocks[1]
                diff_y = mario_y - blocks[0]
                is_smallest = mt.sqrt(mt.pow(diffx,2) + mt.pow(diffy, 2))

        if diff_y < 0:
            return
        elif diff_x < -0.5:
            self.controller.run_action([WindowEvent.PRESS_ARROW_RIGHT], 5)
        elif diff_x > -0.5:
            self.controller.run_action([WindowEvent.PRESS_ARROW_LEFT], 5)
        else:
            self.controller.run_action([WindowEvent.PRESS_BUTTON_A], 12)
            self.controller.run_action([WindowEvent.PRESS_ARROW_RIGHT, WindowEvent.PRESS_BUTTON_A], 15)


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
        self.where = Enviroment(enviroment=self.environment)
        self.actions = Actions(enviroment=self.environment, positions=self.where)

        self.video = None

        self.where.find_mario()

        pygame.init()
        # self.screen = pygame.display.set_mode((640, 480))
        # pygame.display.set_caption('Mario Expert')
    

    def choose_action(self):
        global goomba_in_scene
        state = self.environment.game_state()
        frame = self.environment.grab_frame()
        game_area = self.environment.game_area()

        # Implement your code here to choose the best action
        # time.sleep(0.1)

        output_action = ([0], 0)

        goomb = self.where.find_goomb(15)

        print(goomb)

        return output_action


    def step(self):
        """
        Modify this function as required to implement the Mario Expert agent's logic.

        This is just a very basic example
        """

        self.environment.pyboy.tick()
        self.where.find_mario()

        kg = self.actions.kill_goomb()

        if kg is False:
            self.actions.move_normally()

        print(self.environment.game_area())
            

        



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
