"""
Name: timer.py
Function: Track elapsed gameplay time from the first reveal until game over.
Inputs: Current game state and monotonic time in milliseconds
Outputs: Elapsed milliseconds
External sources: OpenAI Codex assisted PR review fixes
Authors: Kodai Nakae
Maintenance: Kodai Nakae
Date Created: 10/10/2026
Date Last Edited: 10/10/2026
"""


class GameTimer:
    """Track the session independently of AI selection and timer visibility."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.start = None
        self.elapsed = 0
        self.stopped = False

    def update(self, game, now):
        # Flags and rejected clicks leave first_click true.
        if self.start is None and not game.first_click:
            self.start = now
        if self.start is not None and not self.stopped:
            self.elapsed = now - self.start
            self.stopped = game.game_over
