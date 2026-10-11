"""
Name: minesweeper.py
Function: Class to hold the logic for minesweeper game. Includes Mine placement, adjacency detection, space revealing, detect game over, etc.
Inputs: None
Outputs: None
External sources: VScode Copilot
Authors: Drew Franke, Alex Lanter, Mo Osby
Maintenance: Anh Hoang
Date Created: 09/13/2026
Date Last Edited: 10/06/2026
"""
import random

class Minesweeper:
    def __init__(self, num_mines, rows, cols):
        self.num_mines = num_mines
        self.mines = set()
        self.revealed = set()
        self.flags = set()
        self.first_click = True
        self.rows = rows
        self.cols = cols
        self.adjacent_mines = {} #Dictionary to track adjacent mines per cell
        self.game_over = False  # Track if the game is over
        self.won = False  # Track if the player has won
        self.exploded_mine = None 


    def place_mines(self, safe_col, safe_row):
        #place mines randomly on the board, ensuring that the first clicked cell and its neighbors (3x3) are safe
        #function is orginal with some help from assistive inline suggestions (VScode Copilot)
        safe_cell = set()
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                x, y = safe_col + i, safe_row + j
                if 0 <= x < self.cols and 0 <= y < self.rows:
                    safe_cell.add((x, y))

        all_cells = [(x, y) for x in range(self.cols) for y in range(self.rows) if (x, y) not in safe_cell]
        self.mines = set(random.sample(all_cells, self.num_mines))
        self.first_click = False
        self.calculate_adjacent()

    def calculate_adjacent(self): #Copilot assisted for counting adjacent logic.
        for col in range(self.cols):
            for row in range(self.rows):
                if (col, row) in self.mines: #Look at every cell, if it's a mine skip
                    continue

                count = 0 #start count at 0
                for i in [-1, 0, 1]:
                    for j in [-1, 0, 1]:
                        if i == 0 and j == 0: #Look at 3x3 around cell, skip cell itself
                            continue
                        x, y = col + i, row + j #grid space calculated from center plus offset in the 3x3
                        if 0 <= x < self.cols and 0 <= y < self.rows and (x, y) in self.mines: #if space inbounds and there's a mine increase count
                            count += 1

                self.adjacent_mines[(col, row)] = count #add found count to dictionary

    def apply_action(self, action, col, row):
        """Apply a reveal, flag, or unflag at the exact location of (col, row) for AI solver or multi-turn play

        Return 'no_change', 'changed', 'won', or 'lost'. Flag placement
        never toggles an existing flag. Rejected actions preserve state.
        """
        if not isinstance(action, str) or action not in ("reveal", "flag", "unflag"):
            return "no_change"
        # Booleans are not board coordinates, despite being int subclasses.
        if type(col) is not int or type(row) is not int:
            return "no_change"
        if not (0 <= col < self.cols and 0 <= row < self.rows):
            return "no_change"
        if self.game_over:
            return "no_change"

        cell = (col, row)
        if cell in self.revealed:
            return "no_change"

        if action == "flag":
            if cell in self.flags or len(self.flags) >= self.num_mines:
                return "no_change"
            self.flags.add(cell)
            return "changed"

        if action == "unflag":
            if cell not in self.flags:
                return "no_change"
            self.flags.remove(cell)
            return "changed"

        if cell in self.flags:
            return "no_change"
        if self.first_click:
            self.place_mines(col, row)
        self.reveal_cell(col, row)
        if self.game_over:
            return "won" if self.won else "lost"
        return "changed"

    def reveal_cell(self, col, row): #Copilot assisted for recursion
        if (col, row) in self.flags:
            return True
        if (col, row) in self.revealed: 
            return True
        if (col, row) in self.mines:
            # self.revealed.add((col, row))  # Reveal the mine cell 
            self.exploded_mine = ((col, row))
            self.game_over = True  # Set game over flag   
            return False  # Game over
        if (col, row) not in self.revealed:
            self.revealed.add((col, row))
        if self.adjacent_mines.get((col, row), 0) == 0: #Get number of adjacent mines for space, keep going if it's 0
            for i in [-1, 0, 1]: 
                for j in [-1, 0, 1]:
                    if i == 0 and j == 0: #Check 3x3 grid around cell, skip cell itself
                        continue
                    x, y = col + i, row + j #Get current cell inside 3x3 area being checked
                    if 0 <= x < self.cols and 0 <= y < self.rows: #If space is inbounds
                        self.reveal_cell(x, y) #Reveal it (which won't work if it's a mine or already revealed)
        #Win logic if the # of cells remaining is equal to num on mines
        safe_cells = (self.rows * self.cols) - self.num_mines
        if len(self.revealed) == safe_cells:
            self.game_over = True
            self.won = True
        return True

    def get_visible_board(self):
        """ Return a board of visible information so computer or AI can process """
        matrix = []
        #iterate through all the cell. if cell is visible, add to the matrix
        for row in range(self.rows):
            visible_row = []
            for col in range(self.cols):
                cell = (col, row)
                if cell in self.revealed:
                    value = self.adjacent_mines[cell]
                elif cell in self.flags:
                    value = "flagged"
                else:
                    value = "covered"
                visible_row.append(value)
            matrix.append(visible_row)

        return matrix
