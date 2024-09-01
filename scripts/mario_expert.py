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
            WindowEvent.QUIT,  # 0
            WindowEvent.PRESS_ARROW_UP,  # 1
            WindowEvent.PRESS_ARROW_DOWN,  # 2
            WindowEvent.PRESS_ARROW_RIGHT,  # 3
            WindowEvent.PRESS_ARROW_LEFT,  # 4
            WindowEvent.PRESS_BUTTON_A,  # 5
            WindowEvent.PRESS_BUTTON_B,  # 6
            WindowEvent.PRESS_BUTTON_SELECT,  # 7
            WindowEvent.PRESS_BUTTON_START,  # 8
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

        # delay in order for pyboy to recognise button presses
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

        bad_guy_list = []

        for i in id:
            # Get position of bad guy
            badx, bady = np.where(self.game_area() == i)

            # If no bad guy continue
            if badx.size == 0:
                continue

            # Append bad guy to list
            for index in range(badx.size):
                bad_guy_list.append(np.array((badx[index], bady[index])))

        # Return list of bad guys
        return bad_guy_list

    def find_wall_tunnel(self, id):
        # Sets standard delay and flag
        delay = 12
        is_wall = False

        # If mario is out of bounds (died or no longer in view) exit
        if (self.mario_x + 1.5) >= 20:
            return (is_wall, 0)

        # Find if there's a wall in front of mario
        initial_sweep = np.array(
            np.where(self.game_area()[:, int(self.mario_x + 1.5)] == id))

        # If there is no wall in front return
        if initial_sweep.size == 0 or (id == 10 and np.array(np.where(self.game_area()[int(self.mario_y + 0.5), :] == id)).size == 0):
            return (is_wall, 0)

        # Get the smallest index in sweep
        array = np.min(initial_sweep)

        # Calculate the wall height
        wall_height = (1.5 if id == 10 else 2) + (self.mario_y - array)

        # if there is a wall set flag to true
        if (wall_height > 0):
            is_wall = True

        # Calculate delay time as a function of wall height
        delay = int(((11-5)/(4-3)) * wall_height)

        # Return flag and delay calculation
        return (is_wall, delay)

    def find_drop(self):
        # If there is no hole, then no need to worry about drop so exit as 0
        if np.array(np.where(self.game_area()[range(14, 16), :] == 0)).size <= 1:
            return (0, 0)

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
                move = 2
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

    def Bad_Guys_Ahead(self):

        # If there is jumping bug just pause until close
        if 18 in self.game_area():
            bad_guy_pos = self.find_bad_guy([18])
            return (True, bad_guy_pos[0])

        # Find blocks in the game area
        blocks = self.find_bad_guy([15, 16, 19])

        # Initialize variables
        block_found = []
        smallest_dist = 999

        # If no blocks found, return False
        if not blocks:
            return (False, (0, 0))

        # Find the block with the smallest distance to Mario
        for block in blocks:
            current_min = mt.sqrt(
                mt.pow(abs(self.mario_x - block[1]), 2) + mt.pow(self.mario_y - block[0], 2))

            if (current_min < smallest_dist):
                smallest_dist = current_min
                block_found = block

        # If no block found, return False
        if len(block_found) <= 0:
            return (False, 0, 0)

        # Set of numbers that won't be considered obstacles
        list_of_non_obstacles = [15, 16, 0, 1, 19]

        # Get starting position
        check_y = round(self.mario_y + 0.5)
        check_x = round(self.mario_x)

        # Set flag
        in_view = False
        gone_up = False
        gone_down = False
        gone_side = False

        # Mock game area for testimng
        mock_game_area = self.game_area()

        # Value to limit iterations
        i = 0

        while (check_y < 15 and check_y >= 0) and (check_x < 19 and check_x >= 0):
            # Set current block to 99 for debuggin purposes
            mock_game_area[check_y][check_x] = 99

            # If current block is bad buy set the outputs
            if self.game_area()[check_y][check_x] in [15, 16, 18, 19]:
                in_view = True
                mock_game_area[check_y][check_x] = 76
                id = self.game_area()[check_y][check_x]
                break

            # Check positions around current block and set flags and coordinates as neccesary
            if (self.game_area()[check_y + 1][check_x] in list_of_non_obstacles) and gone_up is False:
                check_y += 1
                i += 1
                gone_down = True

            elif (self.game_area()[check_y - 1][check_x + 1] in list_of_non_obstacles) and (self.game_area()[check_y][check_x + 1] in list_of_non_obstacles):
                if block_found[1] < self.mario_x:
                    check_x -= 1
                else:
                    check_x += 1
                gone_side = True

            elif (self.game_area()[check_y - 1][check_x] in list_of_non_obstacles) and (gone_down is False or gone_side is False):
                check_y -= 1
                gone_up = True

            # If out of loops break
            if i > 10:
                break

            i += 1

        # Return flag and position
        return (in_view, [check_y, check_x])

    def Path_From_special_Block(self):
        # Find blocks in the game area
        blocks = self.find_bad_guy([13])

        # Initialize variables
        block_found = []
        smallest_dist = 999

        # If no blocks found, return False
        if not blocks:
            return (False, 0, 0)

        # Find the block with the smallest distance to Mario
        for block in blocks:
            current_min = mt.sqrt(
                mt.pow(abs(self.mario_x - block[1]), 2) + mt.pow(self.mario_y - block[0], 2))

            if (current_min < smallest_dist) and (self.mario_y > block[0]):
                smallest_dist = current_min
                block_found = block

        # If no block found, return False
        if len(block_found) <= 0:
            return (False, 0, 0)

        # Set of numbers that won't be considered obstacles
        list_of_non_obstacles = [13, 0, 1]

        # Get starting position
        check_y = block_found[0]
        check_x = block_found[1]

        # Set flag
        in_view = False
        direction = 0
        turn = 0
        directly_above = True
        jumps = 0

        # Mock game area for testing
        mock_game_area = self.game_area()

        # Value to limit iterations
        i = 0

        while (check_y < 15 and check_y >= 0) and (check_x < 19 and check_x >= 0):
            # Set current block to 99 for debugging purposes
            mock_game_area[check_y][check_x] = 99

            # Check if Mario is in view
            if self.game_area()[check_y][check_x] == 1:
                in_view = True
                break

            # Check positions around current block and set flags and coordinates as necessary
            if (self.game_area()[check_y + 1][check_x] in list_of_non_obstacles):
                check_y += 1
                direction = 0
            else:
                directly_above = False
                if ((self.mario_x - check_x > 0) or direction == 1) and self.game_area()[check_y][check_x + 1] in list_of_non_obstacles:
                    check_x += 1
                    direction = 1
                    turn = 1
                elif ((self.mario_x - check_x < 0) or direction == 2) and self.game_area()[check_y][check_x - 1] in list_of_non_obstacles:
                    check_x -= 1
                    direction = 2
                    turn = 2
                else:
                    break

            # If out of loops break
            if i > 20:
                break

            i += 1

        # Determine the number of jumps required based on the direction and Mario's position
        if (direction == 0 and not directly_above and turn == 1):
            jumps = 1
        elif (direction == 0 and not directly_above and turn == 2):
            jumps = 2

        # Return flag and position
        return (in_view, direction, jumps)


class Actions:
    def __init__(self, enviroment, positions):
        self.controller = enviroment
        self.game_area = enviroment.game_area
        self.positions = positions

        self.attempts = 0
        self.attemp_flag = False

    def move_normally(self):
        # Find if there is a wall in front of Mario and the delay to overcome it
        [is_wall, wall_delay] = self.positions.find_wall_tunnel(10)
        # Find if there is a tunnel in front of Mario and the delay to go through it
        [is_tunnel, tunnel_delay] = self.positions.find_wall_tunnel(14)
        # Find if there is a drop in front of Mario and the delay to jump over it
        [move, drop_delay] = self.positions.find_drop()

        # If there is a wall, press A and right arrow to overcome it with the calculated delay
        if is_wall:
            self.controller.run_action(
                [WindowEvent.PRESS_BUTTON_A, WindowEvent.PRESS_ARROW_RIGHT], wall_delay)
        # If there is a tunnel, press A and right arrow to go through it with the calculated delay
        elif is_tunnel:
            self.controller.run_action(
                [WindowEvent.PRESS_BUTTON_A, WindowEvent.PRESS_ARROW_RIGHT], tunnel_delay)
        # If there is a drop, release the right arrow to drop down with the calculated delay
        elif move == 1:
            self.controller.run_action(
                [WindowEvent.RELEASE_ARROW_RIGHT], drop_delay)
        # If there is a big drop, press A and right arrow to jump over it with the calculated delay
        elif move == 2:
            self.controller.run_action(
                [WindowEvent.PRESS_BUTTON_A, WindowEvent.PRESS_ARROW_RIGHT], drop_delay)
        # If there are no obstacles, press the right arrow to move normally
        else:
            self.controller.run_action([WindowEvent.PRESS_ARROW_RIGHT], 0)

    def kill_bad_guy(self):

        # Look ahead to see if there are any bad guys
        [is_bad_guy, bad_guy_pos] = self.positions.Bad_Guys_Ahead()

        # If no bad guy, exit
        if is_bad_guy is False:
            return False

        # Release run forward button
        self.controller.run_action(
            [WindowEvent.RELEASE_ARROW_LEFT, WindowEvent.RELEASE_ARROW_RIGHT], 0)

        # If there are goomba get the x and y position of the first bad guy
        [bad_y, bad_x] = bad_guy_pos

        # If bad guy is close, then jump
        new_g = self.game_area()[range(int(self.positions.mario_y - 4 if self.positions.mario_y > 4 else self.positions.mario_y),
                                       int(self.positions.mario_y + 1))][:, range(int(self.positions.mario_x), int(self.positions.mario_x + 2))]

        new_g2 = self.game_area()[range(int(self.positions.mario_y - 4 if self.positions.mario_y > 4 else self.positions.mario_y),
                                        int(self.positions.mario_y))][:, range(int(self.positions.mario_x), int(self.positions.mario_x + 6))]

        if abs(self.positions.mario_x - bad_x) < 2:
            self.controller.run_action([WindowEvent.PRESS_BUTTON_A, 30])
        elif (10 in new_g) or (12 in new_g) or (14 in new_g):
            self.controller.run_action([WindowEvent.PRESS_ARROW_RIGHT], 5)

        self.attemp_flag = False

        # Return that there is a bad guy to main running function
        return True

    def go_block(self):
        # Find if there is a block in front of Mario and the direction and height of the block
        [is_block, direction, is_above] = self.positions.Path_From_special_Block()

        # If there is no block or the block is not a special block, return False
        if (is_block is False) or (not 13 in self.game_area()):
            return False

        # If there is an attempt flag, check if there are remaining attempts
        if self.attemp_flag is True:
            if self.attempts > 0:
                self.attempts -= 1
                return False
            else:
                self.attemp_flag = False

        # Release the run forward button
        self.controller.run_action([WindowEvent.RELEASE_ARROW_RIGHT], 0)

        # Perform actions based on the direction and height of the block
        if direction == 0 and is_above == 0:
            # Jump straight up
            self.controller.run_action([WindowEvent.PRESS_BUTTON_A], 10)
            self.attempts += 2
        elif direction == 0 and is_above == 1:
            # Jump up and move left
            self.controller.run_action(
                [WindowEvent.PRESS_BUTTON_A, WindowEvent.PRESS_ARROW_LEFT], 12)
            self.attempts += 2
        elif direction == 0 and is_above == 2:
            # Jump up and move right
            self.controller.run_action(
                [WindowEvent.PRESS_BUTTON_A, WindowEvent.PRESS_ARROW_RIGHT], 12)
            self.attempts += 2
        elif direction == 1:
            # Move left
            self.controller.run_action([WindowEvent.PRESS_ARROW_LEFT], 0)
        elif direction == 2:
            # Move right
            self.controller.run_action([WindowEvent.PRESS_ARROW_RIGHT], 0)
        else:
            return False

        # If there have been more than 8 attempts, set the attempt flag to True
        if (self.attempts > 8):
            self.attemp_flag = True

        return True


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
        self.actions = Actions(
            enviroment=self.environment, positions=self.where)

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

        # Advance the game by one frame
        self.environment.pyboy.tick()

        # Find the current position of Mario
        self.where.find_mario()

        # Check if there is a bad guy ahead and try to kill it
        kg = self.actions.kill_bad_guy()

        # If there is no bad guy, try to navigate to a special block
        if kg is False:
            kg = self.actions.go_block()
            if kg is True:
                return

        # If there is still no bad guy or special block, move normally
        if kg is False:
            self.actions.move_normally()

    def play(self):
        """
        Do NOT edit this method.
        """
        self.environment.reset()

        frame = self.environment.grab_frame()
        height, width, _ = frame.shape

        self.start_video(
            f"{self.results_path}/mario_expert.mp4", width, height)

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
