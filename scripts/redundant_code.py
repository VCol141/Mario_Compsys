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
    # Set flag
    is_hole = False

    # Find if there is a hole at the bottom of the map
    initial_sweep = np.array(np.where(self.game_area()[range(14,16),:] == 0))

    # If no hole exit
    if initial_sweep.size <= 1:
        return(is_hole, 0)
        
    # Get the first coordinate
    hole = initial_sweep[1]

    # If the hole position is less than 3 blocks, set hole to high
    if abs(self.mario_x - hole[0]) <= 3:
        is_hole = True

    # Return flag and delay
    return(is_hole, 10)