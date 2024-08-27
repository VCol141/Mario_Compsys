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

        # if actions input is '-1' release all buttons 
        if actions == [-1]:
            for i in range(WindowEvent.RELEASE_ARROW_UP, WindowEvent.RELEASE_BUTTON_START):
                self.pyboy.send_input(i)
                return
            
        # If delay is less than 5 (but not 0) then round up to 5 (as function is unreliable if below that delay)
        if delay < 5 and delay > 0:
            delay = 5
        
        # Run all actions
        for action in actions:
            self.pyboy.send_input(action)

        # If no delay before turning off, return straight away
        if (delay == 0):
            return
        
        # Delay
        for _ in range(delay):
            self.pyboy.tick()
        
        # Release all button presses
        for action in actions:
            self.pyboy.send_input(action + 8)

        #delay in order for pyboy to recognise button presses
        for _ in range(5):
            self.pyboy.tick()


# Function that has functions to find blocks in the game_area()
class Enviroment:
    def __init__(self, enviroment):
        # Initiate all variables
        self.controller = enviroment
        self.game_area = enviroment.game_area

        self.mario_x = 0
        self.mario_y = 0
    

    def find_mario(self):

        # get y and x positions of mario
        [mario_y, mario_x] = np.where(self.game_area() == 1)

        # calculate the average position
        if mario_x.size > 0 and mario_y.size > 0:
            self.mario_x = (np.max(mario_x) + np.min(mario_x)) / 2
            self.mario_y = (np.max(mario_y) + np.min(mario_y)) / 2
        
        # Return the positions
        return self.mario_x, self.mario_y


    def find_bad_guy(self, id):
        # Get positions of bad guys
        badx, bady = np.where(self.game_area() == id)

        # If not bad guys return -1
        if badx.size == 0:
            return -1
        
        # create an empty array
        self.bad_guy_pos = [0 for y in range(badx.size)]

        # reconfigure the indexes into another array
        for index in range(badx.size):
            self.bad_guy_pos[index] = np.array((badx[index], bady[index]))
        
        # Return positions of bad guy positions
        return self.bad_guy_pos


    def find_wall_tunnel(self, id):
        # Sets standard delay and flag
        delay = 12
        is_wall = False

        # If mario is out of bounds (died or no longer in view) exit
        if (self.mario_x + 1.5) >= 20:
            return (is_wall, delay)
        
        # Find if there's a wall in front of mario
        initial_sweep = np.array(np.where(self.game_area()[:, int(self.mario_x + 1.5)] == id))

        # If there is no wall in front return
        if initial_sweep.size == 0 or np.array(np.where(self.game_area()[int(self.mario_y + 0.5),:] == id)).size == 0:
            return (is_wall, 0)
        
        # Get the smallest index in sweep
        array = np.min(initial_sweep)

        # Calculate the wall height
        wall_height = 1.5 + (self.mario_y - array)

        # if there is a wall set flag to true
        if (wall_height > 0):
            is_wall = True
        
        # Calculate delay time as a function of wall height
        delay = int(((11-5)/(4-3)) * wall_height)
        
        # Return flag and delay calculation
        return (is_wall, delay)
    

    def find_drop(self):
        # If there is no hole, then no need to worry about drop so exit as 0
        if np.array(np.where(self.game_area()[range(14,16),:] == 0)).size <= 1:
            return(0, 0)
        
        # Set flags and get starting position
        move = 0
        delay = 5
        check_y = round(self.mario_y + 0.5)
        check_x = round(self.mario_x + 1)

        # create copy of game area for debugging and testing
        mock_game_area = self.game_area()

        # Loop through
        while check_x < 20:

            # If y axis exceeds boundary, set flag to 2 (as there is a hole, so need to jup over), and delay to 20
            if check_y >= 16:
                move  = 2
                delay = 20
                break

            # Tet current block
            current_block = self.game_area()[check_y][check_x]

            # Check what block is
            if current_block == 0:
                # set to 99 for testing purposes
                mock_game_area[check_y][check_x] = 99
            elif current_block == 10 or current_block == 14 or current_block == 12:
                # Break once it hits a surface
                break

            # Incrament y downwards
            check_y += 1
        
        # If the height is greater than 7, and move is 0, then change move to 1 (as it just a drop to another floor)
        if (check_y - self.mario_y) > 7 and move == 0:
            move = 1
            delay = 50

            # Delay in order for mario to just go over ledge
            for delay in range(5):
                self.controller.pyboy.tick()

        # Return move flag and delay
        return (move, delay)


    def find_special_blocks(self):
        goombx, goomby = np.where(self.game_area() == 13)

        if goombx.size == 0:
            return

        self.goomba_pos = [0 for y in range(goombx.size)]

        for index in range(goombx.size):
            self.goomba_pos[index] = np.array((goombx[index], goomby[index]))
        
        return self.goomba_pos
    

    def Bad_Guys_Ahead(self):

        if 18 in self.game_area():
            return (True, self.find_bad_guy(18))
        
        id = 0
        
        list_of_non_obstacles = [15, 16, 0, 1]
        
        check_y = round(self.mario_y + 0.5)
        check_x = round(self.mario_x)

        in_view = False

        gone_up = False
        gone_down = False

        mock_game_area = self.game_area()
        
        i = 0

        while (check_y < 15 and check_y >= 0) and (check_x < 19 and check_x >= 0):
            mock_game_area[check_y][check_x] = 99

            if self.game_area()[check_y][check_x] in [15, 16, 18]:
                in_view = True
                mock_game_area[check_y][check_x] = 76
                id = self.game_area()[check_y][check_x]
                break
            
            if (self.game_area()[check_y + 1][check_x] in list_of_non_obstacles) and gone_up is False:
                check_y += 1
                gone_down = True
            elif (self.game_area()[check_y - 1][check_x + 1]  in list_of_non_obstacles) and (self.game_area()[check_y][check_x + 1]  in list_of_non_obstacles):
                check_x += 1
            elif (self.game_area()[check_y][check_x + 1] == 0 or self.game_area()[check_y][check_x + 1] == 1 or  self.game_area()[check_y][check_x + 1] == id) and (1 == 0):
                check_x += 1
            elif (self.game_area()[check_y - 1][check_x]  in list_of_non_obstacles) and gone_down is False:
                check_y -= 1
                gone_up = True

            if i > 10:
                break

            i += 1
        
        # print(mock_game_area)
        # print(in_view)
        
        return (in_view, self.find_bad_guy(id))
    

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
        [is_wall, wall_delay] = self.positions.find_wall_tunnel(10)
        [is_tunnel, tunnel_delay] = self.positions.find_wall_tunnel(14)
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
    

    def kill_bad_guy(self):

        # Look ahead to see if there are any bad guys
        [is_bad_guy, bad_guy_pos] = self.positions.Bad_Guys_Ahead()

        # If no bad guy, exit
        if is_bad_guy is False:
            return False
        
        # Release run forward button
        self.controller.run_action([WindowEvent.RELEASE_ARROW_RIGHT], 0)
        
        # If there are goomba get the x and y position of the first bad guy
        [bad_y, bad_x] = bad_guy_pos[0]

        # If bad guy is close, then jump
        if abs(self.positions.mario_x - bad_x) < 2:
            self.controller.run_action([WindowEvent.PRESS_BUTTON_A, 30])
        
        # Return that there is a bad guy to main running function
        return True
    

    def go_to_block(self):
    
        if np.array(self.positions.find_special_blocks()).size <= 1:
            return

        is_smallest = 1000

        for blocks in self.positions.find_special_blocks():
            diffx = self.positions.mario_x - blocks[1]
            diffy = self.positions.mario_y - blocks[0]

            if mt.sqrt(mt.pow(diffx,2) + mt.pow(diffy, 2)) < is_smallest:
                diff_x = self.positions.mario_x - blocks[1]
                diff_y = self.positions.mario_y - blocks[0]
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

    def step(self):
        """
        Modify this function as required to implement the Mario Expert agent's logic.

        This is just a very basic example
        """

        self.environment.pyboy.tick()
        self.where.find_mario()

        # if self.environment.game_area().size not 320:
        #     return

        kg = self.actions.kill_bad_guy()
        # if kg is False: kg = self.actions.kill_bad_guy(16)
        # if kg is False: kg = self.actions.kill_bad_guy(18)
        if kg is False: self.actions.move_normally()


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
