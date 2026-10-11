"""
Name: test_ai_solver.py
Function: Verify the Hard 1-2-1 deduction fires only where it is valid.
Inputs: None
Outputs: None
External sources: none (original test code)
Authors: Rijul Poudel
Date Created: 10/11/2026
"""

import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai_solver import AISolver
from minesweeper import Minesweeper


def pattern_game(mine_row, clue_row, reveal_row=None):
    """A board holding a horizontal 1-2-1: clues at clue_row, mines at mine_row."""
    game = Minesweeper(2, 8, 8)
    game.mines = {(1, mine_row), (3, mine_row)}
    game.first_click = False
    game.calculate_adjacent()
    game.revealed.update({(1, clue_row), (2, clue_row), (3, clue_row)})
    if reveal_row is not None:
        game.revealed.update({(1, reveal_row), (2, reveal_row), (3, reveal_row)})
    return game


class HardPatternTests(unittest.TestCase):
    def test_flags_outer_cells_then_opens_middle(self):
        game = pattern_game(3, 2, reveal_row=1)  # opposite side known
        ai = AISolver(game, "hard")
        self.assertEqual(ai._one_two_one_action(), ("flag", (1, 3)))
        game.flags.add((1, 3))
        self.assertEqual(ai._one_two_one_action(), ("flag", (3, 3)))
        game.flags.add((3, 3))
        self.assertEqual(ai._one_two_one_action(), ("reveal", (2, 3)))

    def test_pattern_at_board_edge(self):
        game = pattern_game(1, 0)  # no opposite side exists
        self.assertEqual(AISolver(game, "hard")._one_two_one_action(), ("flag", (1, 1)))

    def test_interior_pattern_is_not_guessed(self):
        game = pattern_game(3, 2)  # hidden on both sides: two solutions fit
        self.assertIsNone(AISolver(game, "hard")._one_two_one_action())

    def test_flag_cap_falls_back_to_the_safe_reveal(self):
        game = pattern_game(3, 2, reveal_row=1)
        game.flags.update({(7, 7), (7, 6)})  # cap = num_mines = 2
        self.assertEqual(AISolver(game, "hard")._one_two_one_action(), ("reveal", (2, 3)))


if __name__ == "__main__":
    unittest.main()
