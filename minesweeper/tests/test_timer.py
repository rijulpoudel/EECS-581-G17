"""
Name: test_timer.py
Function: Verify timer lifecycle against real human and AI model actions.
External sources: OpenAI Codex assisted PR review fixes
Authors: Kodai Nakae
Maintenance: Kodai Nakae
Date Created: 10/10/2026
Date Last Edited: 10/10/2026
"""

import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ai_solver import AISolver
from controller import GameController
from timer import GameTimer


class TimerTests(unittest.TestCase):
    def setUp(self):
        self.controller = GameController(mode="single_player")
        self.game = self.controller.game
        self.timer = GameTimer()

    def test_flags_and_rejected_reveals_do_not_start_timer(self):
        for action, col, row in (("flag", 0, 0), ("reveal", 0, 0), ("reveal", -1, 0)):
            self.controller.submit_action("human", action, col, row)
            self.timer.update(self.game, 1000)
        self.assertIsNone(self.timer.start)
        self.assertEqual(self.timer.elapsed, 0)

    def test_human_first_reveal_starts_and_counts_time(self):
        self.controller.submit_action("human", "reveal", 0, 0)
        self.timer.update(self.game, 1000)
        self.timer.update(self.game, 3500)
        self.assertEqual(self.timer.start, 1000)
        self.assertEqual(self.timer.elapsed, 2500)

    def test_ai_first_reveal_starts_before_next_human_action(self):
        AISolver(self.game, rng=random.Random(7)).step()
        self.timer.update(self.game, 1000)
        self.timer.update(self.game, 2500)
        self.assertEqual(self.timer.start, 1000)
        self.assertEqual(self.timer.elapsed, 1500)

    def test_win_and_loss_freeze_timer(self):
        for won in (True, False):
            with self.subTest(won=won):
                self.timer.reset()
                self.game.first_click = False
                self.game.game_over = False
                self.timer.update(self.game, 1000)
                self.game.won = won
                self.game.game_over = True
                self.timer.update(self.game, 3200)
                self.timer.update(self.game, 9000)
                self.assertEqual(self.timer.elapsed, 2200)
                self.assertTrue(self.timer.stopped)

    def test_first_reveal_that_ends_game_freezes_at_zero(self):
        self.game.first_click = False
        self.game.game_over = True
        self.timer.update(self.game, 1000)
        self.timer.update(self.game, 2000)
        self.assertEqual(self.timer.elapsed, 0)
        self.assertTrue(self.timer.stopped)

    def test_restart_resets_timer_and_follows_new_game(self):
        self.controller.submit_action("human", "reveal", 0, 0)
        self.timer.update(self.game, 1000)
        self.timer.update(self.game, 2000)
        self.controller.new_game()
        self.timer.reset()
        self.timer.update(self.controller.game, 5000)
        self.assertIsNot(self.controller.game, self.game)
        self.assertIsNone(self.timer.start)
        self.assertEqual(self.timer.elapsed, 0)
        self.assertFalse(self.timer.stopped)


if __name__ == "__main__":
    unittest.main()
