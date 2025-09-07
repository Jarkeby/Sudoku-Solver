from collections import Counter
import time
import pyautogui
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract

# create empty arrays for storing possible locations of each number
open_spots_rc = [[] for _ in range(9)] # this one uses (row, column) formatting
open_spots_grid = [[] for _ in range(9)] # this one uses (grid, spot in grid) formatting
# example of grid locations for both entire board and individual grids
'''
 0 | 1 | 2 
---|---|---
 3 | 4 | 5
---|---|---
 6 | 7 | 8
'''

def print_board(board):
    for row in range(9):
        for col in range(9):
            if ((col+1) % 3 == 0) and col != 8:
                if board[row][col] == 0:
                    print(".", end=" | ")
                else:
                    print(board[row][col], end=" | ")
            else:
                if board[row][col] == 0:
                    print(".", end=" ")
                else:
                    print(board[row][col], end=" ")
        print()
        if (row+1) % 3 == 0 and row != 8:
            print("------|-------|------")

def is_valid(board, row, col, num):
    # checks if in row or column
    if num in board[row]:
        return False
    if any(board[i][col] == num for i in range(9)):
        return False

    # checks grid
    start_row, start_col = (row // 3) * 3, (col // 3) * 3
    if any(board[r][c] == num for r in range(start_row, start_row + 3)
                          for c in range(start_col, start_col + 3)):
        return False
    
    add_valid_spots(row, col, num)
    return True

def add_valid_spots(row, col ,num):
    open_spots_rc[num-1].append((row,col))

    grid = (col // 3) + 3*(row // 3) # finds grid in main board
    grid_loc = (col % 3) + 3*(row % 3) # finds location in the grid
    open_spots_grid[num-1].append((grid,grid_loc))

def get_spot_from_grid(grid, grid_loc):
    # using the grid we get the upper left point in grid (spot 0)
    row = 3*(grid // 3)
    col = 3*(grid % 3)
    # using the grid_loc we add to existing spot to get exact location
    row += (grid_loc // 3)
    col += (grid_loc % 3)

    return (row,col)

def get_grid_from_spot(row, col):
    grid = (col // 3) + 3*(row // 3) 
    grid_loc = (col % 3) + 3*(row % 3)
    return (grid,grid_loc)

# use for debugging
def print_open_spots():
    print("-------ROW COL-------")
    for i in range(9):
        print((i+1), ":", open_spots_rc[i])
    print()
    print("---------GRID--------")
    for i in range(9):
        print((i+1), ":", open_spots_grid[i])

def place_number(num, positions, rc_list, grid_list, board):
    # places number and removes it from list for fill spots function
    for row, col in positions:
        if is_valid(board, row, col, num):
            a, b = get_grid_from_spot(row, col)
            board[row][col] = num
            rc_list[num-1].remove((row, col))
            grid_list[num-1].remove((a, b))

def fill_spots(board):
    for i in range(9):
        num = i+1

        # fills in only row positions for numbers if any
        first_value_rc = Counter(r for r, _ in open_spots_rc[i])
        unique_rows = [(r, c) for r, c in open_spots_rc[i] if first_value_rc[r] == 1]
        place_number(num, unique_rows, open_spots_rc, open_spots_grid, board)

        # fills in only col positions for numbers if any
        second_value_rc = Counter(c for _, c in open_spots_rc[i])
        unique_cols = [(r, c) for r, c in open_spots_rc[i] if second_value_rc[c] == 1]
        place_number(num, unique_cols, open_spots_rc, open_spots_grid, board)

        # fills in only grid positions for numbers if any
        first_value_grid = Counter(g for g, _ in open_spots_grid[i])
        unique_grids = [(g, l) for g, l in open_spots_grid[i] if first_value_grid[g] == 1]
        for grid, loc in unique_grids:
            row, col = get_grid_from_spot(grid, loc)
            board[row][col] = num
            open_spots_grid[i].remove((grid, loc))
            open_spots_rc[i].remove((row, col))

def clear_open_spots():
    for i in range(9):
        open_spots_rc[i].clear()
        open_spots_grid[i].clear()

def check_valid(board):
    clear_open_spots()
    # checks valid numbers for each empty spot in board
    for row, col in [(r, c) for r in range(9) for c in range(9) if board[r][c] == 0]:
        for num in range(1,10):
            is_valid(board, row, col, num)

def get_count(board):
    # gets count of all num in board
    # once all sum adds to 405, board is complete
    return sum(sum(row) for row in board)

def type_solution(board, start_x, start_y, cell_size):
    for row in range(9):
        for col in range(9):
            x = start_x + col * cell_size
            y = start_y + row * cell_size
            pyautogui.click(x, y)
            pyautogui.write(str(board[row][col]), interval=0)

# enter puzzle here 
# puzzle = "803007000000603701710000023080540000050000000671000845037004950500800067000005002"
# board = [[int(puzzle[i*9 + j]) for j in range(9)] for i in range(9)]

def capture_sudoku_board(start_x, start_y, cell_size):
    # captures board from sudoku.com    
    board = [[0 for _ in range(9)] for _ in range(9)]
    padding = 5 

    for row in range(9):
        for col in range(9):
            x = start_x + col * cell_size
            y = start_y + row * cell_size
            
            # gets screenshot of the specific grid box
            bbox = (x + padding, y + padding, cell_size - 2*padding, cell_size - 2*padding)
            cell_img = pyautogui.screenshot(region=bbox)
            
            # enhance image to make number tracking easier
            cell_img = cell_img.convert('L')
            resize_factor = 2  
            cell_img = cell_img.resize((cell_img.width * resize_factor, cell_img.height * resize_factor), Image.Resampling.LANCZOS)
            cell_img = ImageEnhance.Contrast(cell_img).enhance(2.0)
            cell_img = cell_img.filter(ImageFilter.SHARPEN)
            cell_img = cell_img.point(lambda p: 0 if p < 140 else 255, '1')
            
            # convert image to number and add to board array
            text = pytesseract.image_to_string(
                cell_img,
                config='--psm 6 -c tessedit_char_whitelist=123456789'
            ).strip()
            board[row][col] = int(text) if text.isdigit() else 0

    return board


def main():
    print("Gathering Board Data...")
    board = capture_sudoku_board(start_x=685, start_y=220, cell_size=55)
    print_board(board)
    print("Solving...")

    timeout = 3
    start_time = time.time()

    # while loop to fill spaces
    solved = True
    while get_count(board) != 405:
        # ends loop if couldnt solve in time 
        if time.time() - start_time > timeout:
            solved = False
            print("----ERROR/FAILURE----")
            print_board(board)
            return
       
        check_valid(board)
        fill_spots(board)
        
    print("-------FINISHED------")   
    print_board(board)
    if solved: 
        type_solution(board, start_x=700, start_y=240, cell_size=55)

main()



# CREATE A METHOD TO MAKE NOTES TO SOLVE HARDER LEVELS
'''
    checks if a number can only go into two different spots in grid
    if there are two numbers that can only go into those same two spots in grid, lock those spots
    now if there is another number that could possibly go there, it wont be added to possible spots because it is locked by the other two

'''
# CANT SOLVE MASTER AND EXTREME