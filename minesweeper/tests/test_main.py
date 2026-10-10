"""
Name: test_main.py
Function: Exercise the real Pygame event loop with deterministic events and ticks.
External sources: OpenAI Codex assisted PR review fixes
Authors: Kodai Nakae
Maintenance: Kodai Nakae
Date Created: 10/10/2026
Date Last Edited: 10/10/2026
"""

import os
import random
import runpy
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pygame
import board
import timer


class EventLoopTests(unittest.TestCase):
    def key(self, key, unicode=""):
        return pygame.event.Event(pygame.KEYDOWN, key=key, unicode=unicode)

    def click(self, button=1, pos=(50, 50)):
        return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=button, pos=pos)

    def run_game(self, steps):
        """Each callable verifies the previous frame before emitting new events."""
        instances = {}
        ticks = [0]
        original_board, original_timer = board.Board, timer.GameTimer

        def make_board(controller):
            instances["board"] = original_board(controller)
            return instances["board"]

        def make_timer():
            instances["timer"] = original_timer()
            return instances["timer"]

        setup = [self.key(pygame.K_1, "1"), self.key(pygame.K_0, "0"), self.key(pygame.K_RETURN)]
        batches = iter([lambda _: setup, *steps, lambda _: [pygame.event.Event(pygame.QUIT)]])

        def events():
            ticks[0] += 400
            return next(batches)(instances)

        previous_dir = Path.cwd()
        random_state = random.getstate()
        try:
            os.chdir(Path(__file__).resolve().parents[1])
            random.seed(7)
            with patch.object(board, "Board", side_effect=make_board), \
                    patch.object(timer, "GameTimer", side_effect=make_timer), \
                    patch.object(pygame.event, "get", side_effect=events), \
                    patch.object(pygame.time, "get_ticks", side_effect=lambda: ticks[0]), \
                    patch.object(pygame.time, "Clock", return_value=Mock()):
                return runpy.run_path("main.py")
        finally:
            pygame.quit()
            random.setstate(random_state)
            os.chdir(previous_dir)

    def test_ai_first_reveal_escape_and_restart(self):
        starts = []

        def before_ai(state):
            self.assertIsNone(state["timer"].start)
            return [self.key(pygame.K_e), self.key(pygame.K_SPACE)]

        def after_ai(state):
            self.assertIsNotNone(state["timer"].start)
            starts.append(state["timer"].start)
            return [self.key(pygame.K_ESCAPE)]

        def after_escape(state):
            self.assertEqual(state["timer"].start, starts[0])
            self.assertGreater(state["timer"].elapsed, 0)
            return [self.key(pygame.K_r)]

        def after_restart(state):
            self.assertTrue(state["board"].game.first_click)
            self.assertIsNone(state["timer"].start)
            self.assertEqual(state["timer"].elapsed, 0)
            return []

        result = self.run_game([
            lambda _: [self.click(3), self.click(pos=(0, 0))],
            before_ai, after_ai, after_escape, after_restart,
        ])
        self.assertEqual(result["ai_mode"], "off")
        self.assertIsNone(result["ai_solver"])

    def test_autoplay_first_reveal_is_timed(self):
        def after_auto(state):
            self.assertFalse(state["board"].game.first_click)
            self.assertIsNotNone(state["timer"].start)
            return [self.key(pygame.K_ESCAPE)]

        result = self.run_game([
            lambda _: [self.key(pygame.K_m), self.key(pygame.K_a)],
            lambda _: [], after_auto,
        ])
        self.assertFalse(result["auto_play"])
        self.assertGreater(result["timer"].elapsed, 0)

    def test_alternating_turns_ignore_wrong_player_and_restart(self):
        def after_human(state):
            controller = state["board"].controller
            self.assertEqual(controller.mode, "human_vs_ai")
            self.assertEqual(controller.active_player, "computer")
            self.assertEqual(controller.move_count, 1)
            # Wrong-player click must not postpone the scheduled computer move.
            return [self.click(3, (100, 100))]

        def after_computer(state):
            controller = state["board"].controller
            self.assertEqual(controller.active_player, "human")
            self.assertEqual(controller.move_count, 2)
            return [self.key(pygame.K_r)]

        def after_restart(state):
            controller = state["board"].controller
            self.assertEqual(controller.mode, "human_vs_ai")
            self.assertEqual(controller.move_count, 0)
            self.assertTrue(controller.game.first_click)
            return [self.key(pygame.K_ESCAPE)]

        result = self.run_game([
            lambda _: [self.key(pygame.K_t), self.click(3)],
            after_human, after_computer, after_restart,
        ])
        self.assertEqual(result["board"].controller.mode, "single_player")
        self.assertIsNone(result["timer"].start)

    def test_terminal_human_move_freezes_time(self):
        elapsed = []

        def hit_mine(state):
            col, row = sorted(state["board"].game.mines)[0]
            return [self.click(pos=(25 + col * 50 + 10, 25 + row * 50 + 10))]

        def after_loss(state):
            self.assertTrue(state["board"].game.game_over)
            self.assertFalse(state["board"].game.won)
            self.assertTrue(state["timer"].stopped)
            elapsed.append(state["timer"].elapsed)
            return []

        result = self.run_game([lambda _: [self.click()], hit_mine, after_loss])
        self.assertGreater(elapsed[0], 0)
        self.assertEqual(result["timer"].elapsed, elapsed[0])

    def test_autoplay_terminal_reveal_freezes_hidden_time(self):
        elapsed = []

        def prepare_loss(state):
            # The real solver must reveal the only available covered cell.
            game = state["board"].game
            game.first_click = False
            game.mines = {(9, 9)}
            game.num_mines = 1
            game.revealed = {(col, row) for row in range(10) for col in range(10)
                             if (col, row) != (9, 9)}
            game.calculate_adjacent()
            state["timer"].update(game, 800)
            return [self.key(pygame.K_e), self.key(pygame.K_a)]

        def after_loss(state):
            self.assertTrue(state["board"].game.game_over)
            self.assertTrue(state["timer"].stopped)
            elapsed.append(state["timer"].elapsed)
            return [self.key(pygame.K_ESCAPE)]

        result = self.run_game([prepare_loss, lambda _: [], after_loss])
        self.assertEqual(result["ai_mode"], "off")
        self.assertEqual(result["timer"].elapsed, elapsed[0])


if __name__ == "__main__":
    unittest.main()
