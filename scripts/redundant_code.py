def bad_guy_coming(self, id):
    check_y = round(self.mario_y + 0.5)
    check_x = round(self.mario_x + 1)

    mock_game_area = self.game_area()

    if np.array(self.find_bad_guy(id)).size <= 1:
        return False

    while check_x < 20 and check_y >= 16:

        current_block = self.game_area()[check_y][check_x]

        if current_block == 0:
            mock_game_area[check_y][check_x] = 99
        elif current_block == 14 or current_block == 10:
            check_y -= 1
            check_x -= 2
        elif current_block == id:
            mock_game_area[check_y][check_x] = 999
            return True

        check_x += 1

    return False


def find_tunnel(self):
    # Sets standard delay and flag
    is_tunnel = False
    delay = 12

    if (self.mario_x + 1.5 >= 20):
        return (is_tunnel, 0)

    initial_sweep = np.array(
        np.where(self.game_area()[:, int(self.mario_x + 1.5)] == 14))

    if initial_sweep.size == 0:
        return (False, 0)

    array = np.min(initial_sweep)

    wall_height = 2 + (self.mario_y - array)

    if (wall_height > 0):
        is_tunnel = True

    delay = int(((11-5)/(4-3)) * wall_height)

    return (is_tunnel, delay)


def find_hole(self):
    # Set flag
    is_hole = False

    # Find if there is a hole at the bottom of the map
    initial_sweep = np.array(np.where(self.game_area()[range(14, 16), :] == 0))

    # If no hole exit
    if initial_sweep.size <= 1:
        return (is_hole, 0)

    # Get the first coordinate
    hole = initial_sweep[1]

    # If the hole position is less than 3 blocks, set hole to high
    if abs(self.mario_x - hole[0]) <= 3:
        is_hole = True

    # Return flag and delay
    return (is_hole, 10)


def go_to_block(self):

    if np.array(self.positions.find_special_blocks()).size <= 1:
        return False

    is_smallest = 1000

    for blocks in self.positions.find_special_blocks():
        diffx = self.positions.mario_x - blocks[1]
        diffy = self.positions.mario_y - blocks[0]

        if mt.sqrt(mt.pow(diffx, 2) + mt.pow(diffy, 2)) < is_smallest:
            diff_x = self.positions.mario_x - blocks[1]
            diff_y = self.positions.mario_y - blocks[0]
            is_smallest = mt.sqrt(mt.pow(diffx, 2) + mt.pow(diffy, 2))

    if diff_y < 0:
        return False

    # Release run forward button
    self.controller.run_action([WindowEvent.RELEASE_ARROW_RIGHT], 0)

    if diff_x < -0.5:
        self.controller.run_action([WindowEvent.PRESS_ARROW_RIGHT], 5)
    elif diff_x > -0.5:
        self.controller.run_action([WindowEvent.PRESS_ARROW_LEFT], 5)
    else:
        self.controller.run_action([WindowEvent.PRESS_BUTTON_A], 12)
        # self.controller.run_action([WindowEvent.PRESS_ARROW_RIGHT, WindowEvent.PRESS_BUTTON_A], 15)

    return True


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


def find_special_blocks(self):
    goombx, goomby = np.where(self.game_area() == 13)

    if goombx.size == 0:
        return

    self.goomba_pos = [0 for y in range(goombx.size)]

    for index in range(goombx.size):
        self.goomba_pos[index] = np.array((goombx[index], goomby[index]))

    return self.goomba_pos


def new_bad_guy(self):

    if 18 in self.game_area():
        bad_guy_pos = self.find_bad_guy(18)
        bad_guy_pos_2 = bad_guy_pos[0]

        if abs(self.mario_x - bad_guy_pos_2[1]) < 2:
            return (True, 1, True)
        else:
            return (True, 1, False)

    blocks = self.find_bad_guy(15)

    if not blocks:
        blocks = self.find_bad_guy(16)
    else:
        test_block = self.find_bad_guy(16)

        if not test_block and not blocks:
            return (False, 0, False)
        elif not test_block:
            print("no adatives")
        else:
            blocks.append(test_block)

    block_found = []
    smallest_dist = 999

    if not blocks:
        return (False, 0, False)

    for block in blocks:
        current_min = mt.sqrt(
            mt.pow(abs(self.mario_x - block[1]), 2) + mt.pow(self.mario_y - block[0], 2))

        if (current_min < smallest_dist):
            smallest_dist = current_min
            block_found = block

    if len(block_found) <= 0:
        return (False, 0, 0)

    # Set of numbers that won't be considered obstacles
    list_of_non_obstacles = [0, 1]

    # Get starting position
    check_y = block_found[0]
    check_x = block_found[1]

    # Set flag
    in_view = False
    direction = 0
    turn = 0
    directly_above = True
    jumps = False

    # Mock game area for testimng
    mock_game_area = self.game_area()

    # Value to limit iterations
    i = 0

    while (check_y < 15 and check_y >= 0) and (check_x < 19 and check_x >= 0):
        # Set current block to 99 for debuggin purposes
        mock_game_area[check_y][check_x] = 99

        if self.game_area()[check_y][check_x] == 1:
            in_view = True
            break

        if (self.game_area()[check_y + 1][check_x] in list_of_non_obstacles):
            check_y += 1
            direction = 0
        else:
            directly_above = False
            if ((self.mario_x - check_x > 0) or direction == 1) and self.game_area()[check_y][check_x + 1] in list_of_non_obstacles:
                check_x += 1
                direction = 1
            elif ((self.mario_x - check_x < 0) or direction == 2) and self.game_area()[check_y][check_x - 1] in list_of_non_obstacles:
                check_x -= 1
                direction = 2
            else:
                break

        # If out of loops break
        if i > 20:
            break

        i += 1

    # Return flag and position
    return (i < 10 if in_view else False, direction if i > 2 else 2, abs(self.mario_x - block_found[1]) < 2)


def new_kill_guy(self):

    if not (18 or 16 or 15 in self.game_area()):
        return False

    [is_block, direction, is_above] = self.positions.new_bad_guy()

    if (is_block is False):
        return False

    # Release run forward button
    self.controller.run_action(
        [WindowEvent.RELEASE_ARROW_LEFT, WindowEvent.RELEASE_ARROW_RIGHT], 0)

    new_g = self.game_area()[range(int(self.positions.mario_y - 5 if self.positions.mario_y > 5 else self.positions.mario_y),
                                   int(self.positions.mario_y + 1))][:, range(int(self.positions.mario_x), int(self.positions.mario_x + 2))]

    if 10 in new_g:
        self.controller.run_action([WindowEvent.PRESS_ARROW_RIGHT], 5)
    elif direction == 0 and not is_above:
        self.controller.run_action([WindowEvent.PRESS_ARROW_LEFT], 15)
        print("Going Back")
    elif (direction == 1 or direction == 2) and is_above:
        self.controller.run_action([WindowEvent.PRESS_BUTTON_A], 30)
        for i in range(8):
            self.controller.pyboy.tick()

    return True
