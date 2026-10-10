"""
Name: main.py
Function: Start Minesweeper, draw the board, and handle player and computer turns.
Inputs: Number of mines, game mode, keyboard and mouse events
Outputs: Pygame window, win and loss status
External sources: pygame documentation for reference, VScode Copilot;
                  OpenAI Codex assisted PR review fixes; sound integration
                  assisted by Hermes Agent (Nous Research), 10/10/2026
Authors: Mo Osby, Drew Franke, Vrishank Kulkarni, Alex Lanter
Maintenance: Kodai Nakae, Rijul Poudel
Date Created: 09/12/2026
Date Last Edited: 10/10/2026
"""

import pygame
from board import Board
from ai_solver import AISolver
from controller import GameController
from solver import choose_move
from timer import GameTimer
from sound import SoundManager

pygame.init()

screen = pygame.display.set_mode((650, 650))
font = pygame.font.Font("assets/ThaleahFat.ttf", 32)
small_font = pygame.font.Font("assets/ThaleahFat.ttf", 16)


def draw_input_screen(user_input, error):
    # Display the input screen for the number of mines.
    # Original function written with help from VSCode Copilot.
    screen.fill("white")

    # Title.
    title_text = font.render("Minesweeper", True, "black")
    screen.blit(
        title_text,
        (650 // 2 - title_text.get_width() // 2, 200)
    )

    # Instructions.
    instructions_text = small_font.render(
        "Select number of mines (10-20):", True, "black"
    )
    screen.blit(
        instructions_text,
        (650 // 2 - instructions_text.get_width() // 2, 270)
    )

    # Input box.
    input_box = pygame.Rect(275, 320, 100, 40)
    pygame.draw.rect(screen, "lightgray", input_box)
    pygame.draw.rect(screen, "black", input_box, 2)

    typed = font.render(user_input, True, "black")
    screen.blit(typed, (input_box.x + 10, input_box.y + 10))

    # Hint.
    hint = small_font.render("Press Enter to start", True, "gray")
    screen.blit(
        hint,
        (650 // 2 - hint.get_width() // 2, 380)
    )

    # Error handling.
    if error:
        error_text = small_font.render(error, True, "red")
        screen.blit(
            error_text,
            (650 // 2 - error_text.get_width() // 2, 420)
        )

    pygame.display.flip()


def play_ai_step(game, step):
    """Sound for an AISolver.step() move.

    AISolver mutates the game directly and returns no result string, so the
    outcome is inferred from the game state after the step.
    """
    if step is None:
        return
    if game.game_over:
        sound.play_result(step[0], "won" if game.won else "lost")
    else:
        sound.play_result(step[0], "changed")


user_input = ""
error = ""
at_start = True

# Game setup screen.
while at_start:
    draw_input_screen(user_input, error)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if user_input.isdigit() and 10 <= int(user_input) <= 20:
                    num_mines = int(user_input)
                    at_start = False
                else:
                    error = "Please enter a number between 10 and 20."
                    user_input = ""

            elif event.key == pygame.K_BACKSPACE:
                user_input = user_input[:-1]
                error = ""

            elif event.unicode.isdigit() and len(user_input) < 2:
                user_input += event.unicode
                error = ""


# Create the board using the inherited game.
sound = SoundManager()
sound.start_music()
board = Board(GameController(num_mines=num_mines, rows=10, cols=10, mode="single_player"))

running = True

# AI configuration.
ai_mode = "off"
auto_play = False
ai_solver = None

clock = pygame.time.Clock()
last_ai_tick = 0

# Track the whole session; AI selection only affects timer visibility.
timer = GameTimer()
computer_paused = False


while running:
    # Main game event loop.
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        # AI KEYBOARD CONTROLS
        if event.type == pygame.KEYDOWN:

            # E selects Easy AI; M selects Medium AI.
            if event.key in (pygame.K_e, pygame.K_m) and board.controller.mode == "single_player":
                ai_mode = (
                    "easy" if event.key == pygame.K_e else "medium"
                )

                # Both AI difficulties operate on the existing board.
                ai_solver = AISolver(board.game, ai_mode)
                auto_play = False

            # A toggles automatic AI gameplay.
            elif event.key == pygame.K_a and ai_solver is not None:
                auto_play = not auto_play
                last_ai_tick = pygame.time.get_ticks()

            # SPACE executes one AI action.
            elif event.key == pygame.K_SPACE and ai_solver is not None:
                play_ai_step(board.game, ai_solver.step())

            # ESC disables AI gameplay.
            elif event.key == pygame.K_ESCAPE:
                auto_play = False
                ai_mode = "off"
                ai_solver = None
                if board.controller.mode != "single_player":
                    board.controller.new_game("single_player")
                    timer.reset()
                computer_paused = False

            # R restarts this mode; T starts a fresh alternating-turn game.
            elif event.key in (pygame.K_r, pygame.K_t):
                mode = "human_vs_ai" if event.key == pygame.K_t else None
                board.controller.new_game(mode)
                timer.reset()
                auto_play = False
                ai_mode = "off"
                ai_solver = None
                computer_paused = False
                last_ai_tick = pygame.time.get_ticks()

            # S toggles sound on and off.
            elif event.key == pygame.K_s:
                sound.toggle_mute()

        # ORIGINAL MANUAL GAMEPLAY
        if event.type == pygame.MOUSEBUTTONDOWN:

            # Left click reveals a cell.
            if event.button == 1:
                result = board.handle_click(*event.pos)

            # Right click toggles a flag.
            elif event.button == 3:
                result = board.place_flag(*event.pos)
            else:
                result = "no_change"

            if result != "no_change":
                sound.play_result("reveal" if event.button == 1 else "flag", result)

            if result == "changed" and board.controller.active_player == "computer":
                last_ai_tick = pygame.time.get_ticks()

        # Observe every action, including AI steps and terminal events.
        timer.update(board.game, pygame.time.get_ticks())

    # AUTOMATIC AI EXECUTION
    # Run one AI move every 300 milliseconds.
    # This keeps the interface responsive and the moves visible.
    now = pygame.time.get_ticks()

    if auto_play and ai_solver is not None and now - last_ai_tick >= 300:

        step = ai_solver.step()
        play_ai_step(board.game, step)

        # Stop autoplay if no move remains or the game finishes.
        if step is None or board.game.game_over:
            auto_play = False

        last_ai_tick = now

    # Alternating mode uses visible snapshots and submits every AI action
    # through the controller, so turn ownership and outcomes stay consistent.
    if (board.controller.active_player == "computer" and not computer_paused
            and not board.game.game_over and now - last_ai_tick >= 300):
        try:
            move = choose_move(board.game.get_visible_board(), board.game.num_mines)
            if move is None:
                computer_paused = True
            else:
                result = board.controller.submit_action("computer", *move)
                sound.play_result(move[0], result)
                if result == "no_change":
                    computer_paused = True
        except ValueError:
            computer_paused = True
        last_ai_tick = now

    timer.update(board.game, pygame.time.get_ticks())

    # Draw the game board.
    screen.fill("white")
    board.draw(screen)

    # Display game status.
    if board.game.game_over:
        if board.controller.mode == "human_vs_ai":
            status_text = font.render(f"Winner: {board.controller.winner.title()}", True, "green")
        elif board.game.won:
            status_text = font.render("Victory!", True, "green")
        else:
            status_text = font.render("Game Over!", True, "red")
    elif computer_paused:
        status_text = font.render("AI paused - R: Restart", True, "black")
    elif board.controller.mode == "human_vs_ai":
        status_text = font.render(f"Turn: {board.controller.active_player.title()}", True, "black")
    else:
        status_text = font.render("Playing", True, "black")

    screen.blit(
        status_text,
        (650 // 2 - status_text.get_width() // 2, 550)
    )

    # AI control instructions.
    help_text = small_font.render(
        "E/M: AI  Space: Step  A: Auto  Esc: Single  R: Restart  T: Turns  S: Sound",
        True,
        "black"
    )
    screen.blit(help_text, (25, 585))

    # Show the currently selected AI mode.
    mode_text = small_font.render(
        ("Mode: Human vs AI" if board.controller.mode == "human_vs_ai"
         else f"AI: {ai_mode.title()}" + (" (auto)" if auto_play else "")),
        True,
        "black"
    )
    screen.blit(mode_text, (330, 615))

    # Show the timer in Single Play only.
    if board.controller.mode == "single_player" and ai_mode == "off":
        timer_text = small_font.render(f"Time: {timer.elapsed // 1000}s", True, "black")
        screen.blit(timer_text, (25, 615))


    pygame.display.flip()
    clock.tick(60)

pygame.quit()
