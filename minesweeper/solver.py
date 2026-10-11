"""
Name: Controller.py
Function: Compute the move for AI solver
External sources: ChatGPT Astra
Authors: Anh Hoang
Date Created: 10/07/2026
"""

import random


def choose_move(visible_board, num_mines, *, rng=None, rejected_moves=()):
    """Choose the AI's next move

    Inputs:
        visible_board: Rows of numbers 0-8, 'covered', or 'flagged'.
        num_mines: The total mine count shown to the player.
        rng: Optional random generator for repeatable tests.
        rejected_moves: Moves to skip. Clear this when the board changes.

    Return an ('action', col, row) tuple or None if no move remains

    Method to choose cell: certainty first, then a fixed priority, then random guessing
    """
    cells, constraints = _read_board(visible_board, num_mines)
    safe, mines = _deduce(constraints) #find cells where the content can be proved
    covered = [cell for cell, value in cells.items() if value == "covered"]
    flagged = [cell for cell, value in cells.items() if value == "flagged"]
    rejected = set(rejected_moves)

    # Deterministic choices follow matrix order: top to bottom, left to right.
    for action, candidates in (
        ("reveal", [cell for cell in covered if cell in safe]),
        ("unflag", [cell for cell in flagged if cell in safe]),
        ("flag", [cell for cell in covered if cell in mines]
         if len(flagged) < num_mines else []),
    ):
        for col, row in candidates:
            move = (action, col, row)
            if move not in rejected:
                return move
    rng = random if rng is None else rng
    guesses = [("reveal", col, row) for col, row in covered
               if (col, row) not in mines and ("reveal", col, row) not in rejected]
    if guesses:
        return rng.choice(guesses)

    # Never unflag a proved mine. An uncertain flag may be hiding a safe cell.
    removals = [("unflag", col, row) for col, row in flagged
                if (col, row) not in mines and ("unflag", col, row) not in rejected]
    return rng.choice(removals) if removals else None


def _read_board(board, num_mines):
    if type(num_mines) is not int or num_mines < 0:
        raise ValueError("num_mines must be a nonnegative integer")
    rows = len(board)
    cols = len(board[0]) if rows else 0
    cells = {}
    for row, values in enumerate(board):
        if len(values) != cols:
            raise ValueError("visible board must be rectangular")
        for col, value in enumerate(values):
            if not ((type(value) is int and 0 <= value <= 8)
                    or (isinstance(value, str) and value in ("covered", "flagged"))):
                raise ValueError("cells must be 0-8, 'covered', or 'flagged'")
            cells[(col, row)] = value

    unknown = {cell for cell, value in cells.items() if type(value) is not int}
    if num_mines > len(unknown):
        raise ValueError("mine count exceeds the number of hidden cells")
    constraints = [(unknown, num_mines)]
    for (col, row), value in cells.items():
        if type(value) is not int:
            continue
        neighbors = {(x, y)
                     for y in range(max(0, row - 1), min(rows, row + 2))
                     for x in range(max(0, col - 1), min(cols, col + 2))
                     if (x, y) in unknown}
        constraints.append((neighbors, value))
    return cells, constraints


def _deduce(constraints):
    """Propagate certain safe/mine cells until no new facts can be proved."""
    safe, mines = set(), set()
    while True:
        previous_count = len(safe) + len(mines)
        for cells, count in constraints:
            remaining = cells - safe - mines
            remaining_mines = count - len(cells & mines)
            if not 0 <= remaining_mines <= len(remaining):
                raise ValueError("visible clues contradict the mine count or each other")
            if remaining_mines == 0:
                safe.update(remaining)
            elif remaining_mines == len(remaining):
                mines.update(remaining)
        if len(safe) + len(mines) == previous_count:
            return safe, mines
