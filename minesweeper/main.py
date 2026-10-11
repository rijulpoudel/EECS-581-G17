"""
Name: main.py
Function: Start Minesweeper, draw the board, and handle player and computer turns.
Inputs: Number of mines, game mode, keyboard and mouse events
Outputs: Pygame window, win and loss status
External sources: pygame documentation for reference, VScode Copilot;
                  OpenAI Codex assisted PR review fixes; sound integration
                  assisted by Hermes Agent (Nous Research), 10/10/2026
Authors: Mo Osby, Drew Franke, Vrishank Kulkarni, Alex Lanter
Maintenance: Kodai Nakae, Mariska Rai, Rijul Poudel
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

mode_names = {
    "human_vs_ai": "Human vs. computer",
    "ai_only": "Computer solves alone",
}
mode_buttons = {
    "human_vs_ai": pygame.Rect(100, 435, 450, 50),
    "ai_only": pygame.Rect(100, 500, 450, 50),
}


def draw_input_screen(user_input, error, selected_mode):
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

    # Mode buttons on the setup screen. Single-player remains the default
    # when no mode is selected, preserving the inherited behavior.
    for mode, button in mode_buttons.items():
        color = "lightblue" if mode == selected_mode else "lightgray"
        pygame.draw.rect(screen, color, button)
        pygame.draw.rect(screen, "black", button, 2)
        label = mode_names[mode] + (" [T]" if mode == "human_vs_ai" else " [A]")
        text = small_font.render(label, True, "black")
        screen.blit(text, (650 // 2 - text.get_width() // 2, button.y + 16))

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
selected_mode = "single_player"

# Game setup screen.
while at_start:
    draw_input_screen(user_input, error, selected_mode)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_t:
                selected_mode = "human_vs_ai"
                error = ""
            elif event.key == pygame.K_a:
                selected_mode = "ai_only"
                error = ""
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

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for mode, button in mode_buttons.items():
                if button.collidepoint(event.pos):
                    selected_mode = mode

# Create the board using the inherited game.
sound = SoundManager()
sound.start_music()
board = Board(GameController(
    num_mines=num_mines,
    rows=10,
    cols=10,
    mode=selected_mode,
))

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


def start_mode(mode):
    """Start a fresh game while preserving the selected AI difficulty."""
    global ai_mode, ai_solver, auto_play, computer_paused, last_ai_tick
    selected_ai = ai_mode
    board.controller.new_game(mode)
    timer.reset()
    ai_solver = (
        AISolver(board.game, selected_ai)
        if selected_ai in ("easy", "medium", "hard") else None
    )
    auto_play = False
    computer_paused = False
    last_ai_tick = pygame.time.get_ticks()


while running:
    # Main game event loop.
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        # AI KEYBOARD CONTROLS
        if event.type == pygame.KEYDOWN:

            # A starts AI-only mode. T starts human-vs-AI turns.
            if event.key == pygame.K_a:
                start_mode("ai_only")
                continue

            # E/M/H select the AI difficulty. In an AI mode, restart that
            # mode so the new difficulty is applied immediately.
            if event.key in (pygame.K_e, pygame.K_m, pygame.K_h):
                ai_mode = {
                    pygame.K_e: "easy",
                    pygame.K_m: "medium",
                    pygame.K_h: "hard",
                }[event.key]
                if board.controller.mode == "single_player":
                    ai_solver = AISolver(board.game, ai_mode)
                    auto_play = False
                else:
                    start_mode(board.controller.mode)

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

            # R restarts the current mode; T starts human-vs-AI turns.
            elif event.key == pygame.K_t:
                start_mode("human_vs_ai")
            elif event.key == pygame.K_r:
                if board.controller.mode == "single_player":
                    board.controller.new_game()
                    timer.reset()
                    auto_play = False
                    ai_mode = "off"
                    ai_solver = None
                    computer_paused = False
                    last_ai_tick = pygame.time.get_ticks()
                else:
                    start_mode(board.controller.mode)

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
            if ai_mode in ("easy", "medium", "hard"):
                if ai_solver is None or ai_solver.game is not board.game:
                    ai_solver = AISolver(board.game, ai_mode)
                action = ai_solver.choose_action()
                move = (
                    (action[0], action[1][0], action[1][1])
                    if action is not None else None
                )
            else:
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
        if board.controller.mode == "human_vs_ai" and board.controller.winner:
            status_text = font.render(
                f"Winner: {board.controller.winner.title()}", True, "green"
            )
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

    # AI control instructions. Split across two centered lines so the
    # controls stay inside the 650-pixel window.
    controls_top = small_font.render(
        "E/M/H: AI Assist    A: AI Only    T: AI Turns",
        True,
        "black"
    )
    controls_bottom = small_font.render(
        "Space: Step    Esc: Single    R: Restart    S: Sound",
        True,
        "black"
    )
    screen.blit(controls_top, controls_top.get_rect(center=(325, 590)))
    screen.blit(controls_bottom, controls_bottom.get_rect(center=(325, 610)))

    # Show the currently selected AI mode.
    selected_ai_label = ai_mode.title() if ai_mode != "off" else "Default"
    if board.controller.mode == "human_vs_ai":
        mode_label = f"Mode: AI Turns ({selected_ai_label})"
    elif board.controller.mode == "ai_only":
        mode_label = f"Mode: AI Only ({selected_ai_label})"
    else:
        mode_label = f"Mode: Single Player ({selected_ai_label} Assist)"
    mode_text = small_font.render(mode_label, True, "black")
    screen.blit(mode_text, (330, 635))

    # Show the timer in Single Play only.
    if board.controller.mode == "single_player" and ai_mode == "off":
        timer_text = small_font.render(f"Time: {timer.elapsed // 1000}s", True, "black")
        screen.blit(timer_text, (25, 635))


    pygame.display.flip()
    clock.tick(60)

pygame.quit()
