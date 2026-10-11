# EECS-581 Group 17 Project 2

A 10x10 version of the classic puzzle game Minesweeper, extended with an AI solver (easy / medium / hard), a game timer, and sound effects with music.

## Setup Instructions

1. Ensure Python 3.13 is installed.
2. Clone the repository and `cd EECS-581-G17`.
3. Create the virtual environment: `python3.13 -m venv .venv`, then activate it with `source .venv/bin/activate` (Windows: `.venv\Scripts\activate`).
4. Install pygame: `pip install pygame`.
5. `cd minesweeper` and start the game with `python main.py`.
6. Run the tests from `minesweeper/` with `python -m unittest discover -s tests`.

## Controls

- Setup screen: pick a mode — Single Player (default), Human vs. AI (`T`), AI Only (`A`) — then type a mine count (10-20) and press Enter.
- Left click uncovers a cell; right click toggles a flag.
- In game: `E` / `M` / `H` = Easy / Medium / Hard AI assist · `Space` = one AI step · `A` = AI-only mode · `T` = human-vs-AI turns · `R` = restart · `Esc` = single player · `S` = sound on/off.
- The timer runs in single-player with AI assistance off.

## Documentation

Everything is in [documentation/](documentation/):

- [System Architecture](documentation/SystemArchitecture.md) — components, data flow, key data structures, diagrams
- [Sound and music](documentation/CustomFeature_Sound.md) — the custom addition, with UML class and sequence diagrams
- [Game timer](documentation/Timer.md) — second enhancement, with a UML sequence diagram
- [Person hours](documentation/person-hours.md) — estimation methodology and day-by-day actuals
