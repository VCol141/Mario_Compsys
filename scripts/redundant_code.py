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
