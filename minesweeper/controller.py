"""
Name: Controller.py
Function: Manage turn and outcome rules for human-vs-AI and AI-solver logic
External sources: ChatGPT Astra
Authors: Anh Hoang
Date Created: 10/07/2026
"""

from minesweeper import Minesweeper


class GameController:
    def __init__(self, num_mines=10, rows=10, cols=10, mode="human_vs_ai"):
        self.game = Minesweeper(num_mines, rows, cols)
        self._reset_turns(mode)

    def new_game(self, mode=None):
        """Reset the board and turns, retaining dimensions and mine count.

        Omit mode to keep the current mode, or select 'single_player'/'human_vs_ai'/'ai_only'.
        """
        self._reset_turns(self.mode if mode is None else mode)
        self.game = Minesweeper(self.game.num_mines, self.game.rows, self.game.cols)

    def _reset_turns(self, mode):
        if mode not in ("single_player", "human_vs_ai", "ai_only"):
            raise ValueError("mode must be 'single_player', 'human_vs_ai', or 'ai_only'")
        self.mode = mode
        self.active_player = "computer" if mode == "ai_only" else "human"
        self.winner = None
        self.move_count = 0

    def submit_action(self, player, action, col, row):
        """Apply one active player's action and return the model's result.
        """
        if self.game.game_over or player != self.active_player:
            return "no_change"

        result = self.game.apply_action(action, col, row)
        if result == "no_change":
            return result

        self.move_count += 1
        if result == "won":
            self.winner = player
            self.active_player = None
        elif result == "lost":
            if self.mode == "human_vs_ai":
                self.winner = "computer" if player == "human" else "human"
            self.active_player = None
        elif self.mode == "human_vs_ai":
            self.active_player = "computer" if player == "human" else "human"
        return result
