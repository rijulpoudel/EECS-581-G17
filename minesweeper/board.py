"""
Name: Board.py
Function: board class for minesweeper game that displays the board and handles clicking/flags.
Inputs: None
Outputs: None
External sources: pygame documentation for reference, VScode Copilot
Authors: Mo Osby, Drew Franke, Alex Lanter, Vrishank Kulkarni, Davina Love
Maintenance: Anh Hoang
Date Created: 09/12/2026
Date last Edited: 10/06/2026
"""
import pygame
from controller import GameController

class Board:
    def __init__(self, controller: GameController):
        self.controller = controller
        self.tile_size = 50

        self.x = 25
        self.y = 25

        self.font = pygame.font.Font("assets/ThaleahFat.ttf", 32)
        #Load in asset files
        self.loadAssets()

    @property
    def game(self):
        return self.controller.game

    @property
    def rows(self):
        return self.game.rows

    @property
    def cols(self):
        return self.game.cols

    def handle_click(self, mouse_x, mouse_y):
        #handle left clicks to reveal cell
        #function is orginal with some help from assistive inline suggestions (VScode Copilot)
        #convert mouse click position to board coordinates
        col = (mouse_x - self.x) // self.tile_size
        row = (mouse_y - self.y) // self.tile_size

        return self.controller.submit_action("human", "reveal", col, row)

    def place_flag(self, mouse_x, mouse_y):
        # convert mouse click position to board coordinates
        col = (mouse_x - self.x) // self.tile_size
        row = (mouse_y - self.y) // self.tile_size

        # Human right-click toggles; an AI "flag" request only places a flag.
        action = "unflag" if (col, row) in self.game.flags else "flag"
        return self.controller.submit_action("human", action, col, row)


    #Import Assets
    def loadAssets(self):

        #Store all assets
        self.tiles = {}
        self.events = {}

        # List of event sprite names
        events = {"unknown" : "TileUnknown",
                  "empty": "TileEmpty",
                  "flag": "TileFlag",
                  "mine": "TileMine",
                  "explosion": "TileExploded"}
        #List of numbered tiles

        tile_range = range(1,9)

        # Load and resize numbered tiles
        #Copilot assisted syntax
        for i in tile_range:
            self.tiles[i] = pygame.image.load(f"assets/Tile{i}.png").convert_alpha()
            self.tiles[i] = pygame.transform.scale(self.tiles[i], (self.tile_size, self.tile_size))

        # Load and resize event sprites
        for event, i in events.items():
            self.events[event] = pygame.image.load(f"assets/{i}.png").convert_alpha()
            self.events[event] = pygame.transform.scale(self.events[event], (self.tile_size, self.tile_size))

    def draw(self, screen):
        #Copilot assisted for drawing details
        # Draw column labels A-J
        for col in range(self.cols):
            label = chr(ord('A') + col) #Label to give is A's unicode plus column number
            text = self.font.render(label, True, "black")
            text_rect = text.get_rect(
                center=(
                    self.x + col * self.tile_size + self.tile_size // 2,
                    self.y - 15
                )
            )
            screen.blit(text, text_rect)

        # Draw row labels 1-10
        for row in range(self.rows):
            label = str(1 + row) #Label to give is 1 + row number
            text = self.font.render(label, True, "black")
            text_rect = text.get_rect(
                center=(
                    self.x - 15,
                    self.y + row * self.tile_size + self.tile_size // 2
                )
            )
            screen.blit(text, text_rect)



        #Draw board onto the screen
        for row in range(self.rows):
            for col in range(self.cols):
                x = self.x + col * self.tile_size
                y = self.y + row * self.tile_size

                #Change tiles based on the event after click
                if self.game.game_over and (col, row) == self.game.exploded_mine:
                    event = self.events["explosion"]
                elif (col, row) in self.game.flags:
                    event = self.events["flag"]
                elif (col, row) in self.game.revealed:
                    event = self.events["empty"]
                elif self.game.game_over and (col, row) in self.game.mines:
                    event = self.events["mine"]
                else:
                    event = self.events["unknown"]

                screen.blit(event, (x,y))

                pygame.draw.rect(
                    screen,
                    "black",
                    (x, y, self.tile_size, self.tile_size), 2
                )

                #Draw number adjacent mines (unless=0)
                #Copilot assisted for drawing details
                if (col, row) in self.game.revealed and (col, row) not in self.game.mines:
                    count = self.game.adjacent_mines.get((col, row), 0) #Get mine number
                    if count > 0:
                        text = self.font.render(str(count), True, "black") #Draw the number of mines to middle of tile
                        text_rect = text.get_rect(center=(x + self.tile_size // 2, y + self.tile_size // 2))
                        screen.blit(text, text_rect)
