
"""
Name: ai_solver.py
Function: Choose and apply one Easy, Medium, or Hard move for the game AI.
Inputs: A Minesweeper instance exposing rows, cols, revealed, flags,
        adjacent_mines, first_click, place_mines, reveal_cell and game_over.
Outputs: choose_action() returns (action, (column, row)) or None without
         changing state; step() applies that move and returns the same tuple.
External sources: Easy/Medium logic by Shayaan (PR #19); Hard 1-2-1 pattern
         and refactor by Mariska Rai (PR #22); deduction guard and this
         prologue by Rijul Poudel with AI assistance (Hermes Agent), 10/11/2026.
         All rules implement the EECS 581 Project 2 assignment specification.
Authors: Shayaan, Mariska Rai, Rijul Poudel
Date Created: 10/09/2026
Date Last Edited: 10/11/2026

Only revealed clue values and visible covered/flagged status guide deduction.
The solver never inspects game.mines to decide which cell to select.
"""

import random


class AISolver:
    """Perform one Easy, Medium, or Hard action per step on the game."""

    def __init__(self, game, difficulty="easy", rng=None):
        if difficulty.lower() not in ("easy", "medium", "hard"):
            raise ValueError("Difficulty must be 'easy', 'medium', or 'hard'")
        self.game = game
        self.difficulty = difficulty.lower()
        self.rng = rng if rng is not None else random.Random()

    def covered_neighbors(self, cell):
        """Return adjacent cells that are neither revealed nor flagged."""
        col, row = cell
        return [
            (x, y)
            for y in range(max(0, row - 1), min(self.game.rows, row + 2))
            for x in range(max(0, col - 1), min(self.game.cols, col + 2))
            if (x, y) != cell
            and (x, y) not in self.game.revealed
            and (x, y) not in self.game.flags
        ]

    def flagged_neighbors(self, cell):
        """Count neighboring flags without consulting hidden mine positions."""
        col, row = cell
        return sum(
            (x, y) in self.game.flags
            for y in range(max(0, row - 1), min(self.game.rows, row + 2))
            for x in range(max(0, col - 1), min(self.game.cols, col + 2))
            if (x, y) != cell
        )

    def available_cells(self):
        """All eligible Easy-mode guesses, in stable coordinate order."""
        return [
            (col, row)
            for row in range(self.game.rows)
            for col in range(self.game.cols)
            if (col, row) not in self.game.revealed
            and (col, row) not in self.game.flags
        ]

    def _reveal(self, cell):
        # Initialize mines on the first move using the game's existing logic.
        if self.game.first_click:
            self.game.place_mines(*cell)

        self.game.reveal_cell(*cell)
        return ("reveal", cell)

    def _flag(self, cell):
        # Respect the game's maximum allowed number of flags.
        if len(self.game.flags) >= self.game.num_mines:
            return None

        self.game.flags.add(cell)
        return ("flag", cell)

    def _one_two_one_action(self):
        """Return a move from a visible horizontal or vertical 1-2-1 pattern."""
        revealed = self.game.revealed
        clues = self.game.adjacent_mines

        # Check both orientations and both sides of each clue sequence.
        for horizontal in (True, False):
            for row in range(self.game.rows):
                for col in range(self.game.cols):
                    if horizontal:
                        cells = [(col + i, row) for i in range(3)]
                    else:
                        cells = [(col, row + i) for i in range(3)]

                    if any(
                        x < 0 or x >= self.game.cols or y < 0 or y >= self.game.rows
                        for x, y in cells
                    ):
                        continue
                    if any(cell not in revealed for cell in cells):
                        continue
                    if [clues.get(cell) for cell in cells] != [1, 2, 1]:
                        continue

                    for side in (-1, 1):
                        if horizontal:
                            hidden = [(col + i, row + side) for i in range(3)]
                            opposite = [(col + i, row - side) for i in range(3)]
                        else:
                            hidden = [(col + side, row + i) for i in range(3)]
                            opposite = [(col - side, row + i) for i in range(3)]

                        if any(
                            x < 0 or x >= self.game.cols or y < 0 or y >= self.game.rows
                            for x, y in hidden
                        ):
                            continue
                        if any(
                            cell in revealed for cell in hidden
                        ):
                            continue
                        if hidden[1] in self.game.flags:
                            continue

                        # The deduction only holds when the other side of the
                        # pattern is known (revealed or off the board). With
                        # hidden cells on both sides the constraint has two
                        # solutions, so flagging would be a guess.
                        # ponytail: guards the classic one-sided pattern; a full
                        # hidden-neighborhood check would be stricter.
                        if any(
                            0 <= x < self.game.cols and 0 <= y < self.game.rows
                            and (x, y) not in revealed
                            for x, y in opposite
                        ):
                            continue

                        # Flag each outer cell first, then reveal the safe
                        # middle cell once both mines are marked. Respect the
                        # flag cap so a full flag supply cannot stall the AI.
                        under_cap = len(self.game.flags) < self.game.num_mines
                        if hidden[0] not in self.game.flags and under_cap:
                            return ("flag", hidden[0])
                        if hidden[2] not in self.game.flags and under_cap:
                            return ("flag", hidden[2])
                        return ("reveal", hidden[1])

        return None

    def choose_action(self):
        """Choose one move without changing the game state.

        A clue with N mines and F adjacent flags has N-F mines remaining.
        If all U unflagged covered neighbors are mines (U == N-F), flag one.
        If no mines remain (N == F), reveal one of the U neighbors.
        Inconsistent flags (F > N) produce no logical deduction.
        """

        if self.game.game_over:
            return None

        if self.difficulty == "hard":
            pattern_action = self._one_two_one_action()
            if pattern_action is not None:
                return pattern_action

        if self.difficulty in ("medium", "hard"):
            clues = sorted(self.game.revealed)

            # Check revealed numbers for guaranteed mines.
            for cell in clues:
                number = self.game.adjacent_mines.get(cell, 0)
                unknown = self.covered_neighbors(cell)
                flagged = self.flagged_neighbors(cell)

                # Number of mines not yet accounted for by existing flags.
                remaining = number - flagged

                # If every remaining covered neighbor must be a mine,
                # flag one of those neighbors.
                if unknown and remaining > 0 and remaining == len(unknown):
                    if len(self.game.flags) < self.game.num_mines:
                        return ("flag", unknown[0])

            # Check revealed numbers for guaranteed safe neighbors.
            for cell in clues:
                number = self.game.adjacent_mines.get(cell, 0)
                unknown = self.covered_neighbors(cell)
                flagged = self.flagged_neighbors(cell)

                # If all mines indicated by this number are already
                # flagged, the other covered neighbors are safe.
                if unknown and flagged == number:
                    return ("reveal", unknown[0])

        # Choose randomly from covered cells that are not flagged.
        options = self.available_cells()

        # Stop when no eligible move is available.
        if not options:
            return None

        return ("reveal", self.rng.choice(options))

    def step(self):
        """Choose and apply one Easy or Medium move."""
        action = self.choose_action()
        if action is None:
            return None

        name, cell = action
        if name == "flag":
            self._flag(cell)
        else:
            self._reveal(cell)
        return action
