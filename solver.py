from collections import Counter
import time
import pyautogui
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
import pytesseract
import os


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
    time.sleep(3) # use this time to switch to sudoku.com
    for row in range(9):
        for col in range(9):
            x = start_x + col * cell_size
            y = start_y + row * cell_size
            pyautogui.click(x, y)
            pyautogui.typewrite(str(board[row][col]))



# enter puzzle here
# puzzle = "803007000000603701710000023080540000050000000671000845037004950500800067000005002"
# board = [[int(puzzle[i*9 + j]) for j in range(9)] for i in range(9)]


def capture_sudoku_board_debug_resized(start_x, start_y, cell_size, save_dir="debug_cells"):
    """
    Capture Sudoku board with preprocessing to improve OCR accuracy.
    
    start_x, start_y: top-left corner of the grid
    cell_size: width/height of each cell in pixels
    save_dir: folder to save debug cell images
    """
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    board = [[0 for _ in range(9)] for _ in range(9)]
    padding = 5  # crop slightly inside the cell

    for row in range(9):
        for col in range(9):
            x = start_x + col * cell_size
            y = start_y + row * cell_size
            
            # Screenshot region (left, top, width, height)
            bbox = (x + padding, y + padding, cell_size - 2*padding, cell_size - 2*padding)
            cell_img = pyautogui.screenshot(region=bbox)
            
            # Convert to grayscale
            cell_img = cell_img.convert('L')
            
            # Resize to make OCR more accurate
            resize_factor = 2  # can increase if needed
            cell_img = cell_img.resize((cell_img.width * resize_factor, cell_img.height * resize_factor), Image.Resampling.LANCZOS)
            
            # Enhance contrast
            cell_img = ImageEnhance.Contrast(cell_img).enhance(2.0)
            
            # Threshold to black and white
            cell_img = cell_img.filter(ImageFilter.SHARPEN)
            cell_img = cell_img.point(lambda p: 0 if p < 140 else 255, '1')
            
            # OCR
            text = pytesseract.image_to_string(
                cell_img,
                config='--psm 6 -c tessedit_char_whitelist=123456789'
            ).strip()
            
            # Save raw cell image
            cell_path = os.path.join(save_dir, f"cell_{row}_{col}.png")
            cell_img.save(cell_path)
            
            # Get character bounding boxes
            boxes = pytesseract.image_to_boxes(
                cell_img,
                config='--psm 10 -c tessedit_char_whitelist=123456789'
            )
            
            # Draw boxes on a copy of the image
            debug_img = cell_img.convert("RGB")
            draw = ImageDraw.Draw(debug_img)
            img_height = cell_img.height

            for line in boxes.splitlines():
                char, x1, y1, x2, y2, _ = line.split()
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                
                # Convert Tesseract y-coordinates (origin bottom-left) to top-left for PIL
                y1_new = img_height - y2
                y2_new = img_height - y1
                
                # Draw rectangle on cell image
                draw.rectangle([x1, y1_new, x2, y2_new], outline="red", width=1)
                
                # Convert to screen coordinates
                screen_x1 = x + padding + x1 // resize_factor
                screen_y1 = y + padding + y1_new // resize_factor
                screen_x2 = x + padding + x2 // resize_factor
                screen_y2 = y + padding + y2_new // resize_factor
                
                # print(f"Cell ({row},{col}) detected '{char}' at screen pixels: ({screen_x1},{screen_y1}) -> ({screen_x2},{screen_y2})")
            
            # Save debug image with boxes
            debug_img.save(os.path.join(save_dir, f"cell_{row}_{col}_boxed.png"))

            # Store number in board
            board[row][col] = int(text) if text.isdigit() else 0

    return board


def main():
    print("Gathering Board Data...")
    board = capture_sudoku_board_debug_resized(start_x=685, start_y=220, cell_size=55)
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