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