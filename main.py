import time
import sys
import random
import select
import termios
import tty
import os
import re
from dataclasses import dataclass
from typing import List, Set, Tuple


@dataclass
class GameConfig:
    SCREEN_WIDTH: int = 100
    SCREEN_HEIGHT: int = 20
    SPEED: float = 40.0  # Pixels per second
    MIN_SPACING: int = 15
    MAX_SPACING: int = 40
    NUM_COLUMNS: int = 4
    GAP_HEIGHT: int = 8
    FPS: int = 60
    FRAME_TIME: float = 1.0 / FPS


@dataclass
class PlayerConfig:
    START_X: int = 20
    GRAVITY: float = 20.0
    JUMP_STRENGTH: float = -10.0
    CHARACTER: str = "\033[33m(0)>\033[0m"


@dataclass
class Colors:
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    RESET = "\033[0m"


# Game elements
COLUMN_CHAR = f"{Colors.GREEN}H{Colors.RESET}"
BORDER_CHAR = f"{Colors.BLUE}─{Colors.RESET}"
BORDER_VERTICAL = f"{Colors.BLUE}│{Colors.RESET}"
HIGHSCORE_FILE = "highscore.txt"


class GameState:
    def __init__(self):
        self.config = GameConfig()
        self.player_config = PlayerConfig()
        self.player_y = self.config.SCREEN_HEIGHT // 2
        self.player_velocity = 0.0
        self.score = 0
        self.highscore = 0
        self.game_over = False
        self.passed_columns: Set[int] = set()
        self.columns: List[List[float]] = []
        self.player_visible_length = strip_ansi(self.player_config.CHARACTER)

        self._init_columns()
        self._load_highscore()

    def _init_columns(self) -> None:
        current_x = self.config.SCREEN_WIDTH
        for _ in range(self.config.NUM_COLUMNS):
            gap_start = random.randint(
                1, self.config.SCREEN_HEIGHT - self.config.GAP_HEIGHT - 1)
            self.columns.append([current_x, gap_start])
            current_x += random.randint(self.config.MIN_SPACING,
                                        self.config.MAX_SPACING)

    def _load_highscore(self) -> None:
        try:
            if os.path.exists(HIGHSCORE_FILE):
                with open(HIGHSCORE_FILE, 'r') as f:
                    self.highscore = int(f.read().strip())
        except:
            self.highscore = 0

    def save_highscore(self) -> None:
        if self.score > self.highscore:
            self.highscore = self.score
            try:
                with open(HIGHSCORE_FILE, 'w') as f:
                    f.write(str(self.highscore))
            except:
                pass

    def reset(self) -> None:
        self.player_y = self.config.SCREEN_HEIGHT // 2
        self.player_velocity = 0
        self.score = 0
        self.game_over = False
        self.passed_columns.clear()
        self.columns.clear()
        self._init_columns()


def strip_ansi(text: str) -> int:
    """Remove ANSI escape codes from text and return the visible length."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return len(ansi_escape.sub('', text))


class InputHandler:
    def __init__(self):
        self.old_settings = termios.tcgetattr(sys.stdin)

    def init_keyboard(self) -> None:
        tty.setcbreak(sys.stdin.fileno())

    def restore_keyboard(self) -> None:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)

    def check_keyboard(self, game_state: GameState) -> None:
        if select.select([sys.stdin], [], [], 0)[0] != []:
            key = sys.stdin.read(1)
            if key == ' ':  # Space bar
                if game_state.game_over:
                    game_state.reset()
                else:
                    game_state.player_velocity = game_state.player_config.JUMP_STRENGTH
            # Clear remaining input
            while select.select([sys.stdin], [], [], 0)[0] != []:
                sys.stdin.read(1)


class Renderer:
    @staticmethod
    def generate_frame(game_state: GameState) -> str:
        if game_state.game_over:
            return Renderer._generate_game_over_screen(game_state)

        output = (f"{Colors.BRIGHT_GREEN}Score: {game_state.score}{Colors.RESET} | "
                  f"{Colors.BRIGHT_YELLOW}Highscore: {game_state.highscore}{Colors.RESET}\n")
        output += BORDER_CHAR * (game_state.config.SCREEN_WIDTH + 2) + "\n"

        for i in range(game_state.config.SCREEN_HEIGHT):
            output += BORDER_VERTICAL
            j = 0
            while j < game_state.config.SCREEN_WIDTH:
                if i == int(game_state.player_y) and j == game_state.player_config.START_X:
                    output += game_state.player_config.CHARACTER
                    j += game_state.player_visible_length
                    continue

                column_here = False
                for col_x, gap_start in game_state.columns:
                    if int(col_x) == j:
                        if gap_start <= i < gap_start + game_state.config.GAP_HEIGHT:
                            output += " "
                        else:
                            output += COLUMN_CHAR
                        column_here = True
                        break
                if not column_here:
                    output += " "
                j += 1
            output += BORDER_VERTICAL + "\n"
        output += BORDER_CHAR * (game_state.config.SCREEN_WIDTH + 2) + "\n"
        return output

    @staticmethod
    def _generate_game_over_screen(game_state: GameState) -> str:
        output = (f"{Colors.BRIGHT_RED}Game Over - Score: {game_state.score}{Colors.RESET} | "
                  f"{Colors.BRIGHT_YELLOW}Highscore: {game_state.highscore}{Colors.RESET}\n")
        output += BORDER_CHAR * (game_state.config.SCREEN_WIDTH + 2) + "\n"

        game_over_msg = f"{Colors.BRIGHT_RED}GAME OVER - Press SPACE to restart{Colors.RESET}"
        visible_msg_length = strip_ansi(game_over_msg)
        padding = (game_state.config.SCREEN_WIDTH - visible_msg_length) // 2

        for i in range(game_state.config.SCREEN_HEIGHT):
            output += BORDER_VERTICAL
            if i == game_state.config.SCREEN_HEIGHT // 2:
                output += " " * padding + game_over_msg + " " * (
                    game_state.config.SCREEN_WIDTH - padding - visible_msg_length)
            else:
                output += " " * game_state.config.SCREEN_WIDTH
            output += BORDER_VERTICAL + "\n"
        output += BORDER_CHAR * (game_state.config.SCREEN_WIDTH + 2) + "\n"
        return output


def main():
    game_state = GameState()
    input_handler = InputHandler()
    renderer = Renderer()

    try:
        input_handler.init_keyboard()
        print('\033[2J\033[H', end='')  # Clear screen and move to top

        last_time = time.time()
        while True:
            current_time = time.time()
            delta_time = current_time - last_time
            last_time = current_time

            input_handler.check_keyboard(game_state)
            update_game_state(game_state, delta_time)
            frame = renderer.generate_frame(game_state)
            output_frame(frame)
            time.sleep(game_state.config.FRAME_TIME)

    finally:
        input_handler.restore_keyboard()


def update_game_state(game_state: GameState, delta_time: float) -> None:
    if game_state.game_over:
        return

    # Update player physics
    game_state.player_velocity += game_state.player_config.GRAVITY * delta_time
    game_state.player_y += game_state.player_velocity * delta_time

    # Boundary checks
    if game_state.player_y >= game_state.config.SCREEN_HEIGHT - 1:
        game_state.player_y = game_state.config.SCREEN_HEIGHT - 1
        game_state.game_over = True
    elif game_state.player_y < 0:
        game_state.player_y = 0
        game_state.player_velocity = 0

    # Update columns
    update_columns(game_state, delta_time)
    check_collisions(game_state)


def update_columns(game_state: GameState, delta_time: float) -> None:
    for i in range(len(game_state.columns)):
        game_state.columns[i][0] -= game_state.config.SPEED * delta_time
        if game_state.columns[i][0] < 0:
            rightmost = max(col[0] for col in game_state.columns)
            new_position = max(
                rightmost + random.randint(
                    game_state.config.MIN_SPACING,
                    game_state.config.MAX_SPACING
                ),
                game_state.config.SCREEN_WIDTH
            )
            new_gap = random.randint(
                1,
                game_state.config.SCREEN_HEIGHT - game_state.config.GAP_HEIGHT - 1
            )
            game_state.columns[i] = [new_position, new_gap]
            game_state.passed_columns.discard(i)


def check_collisions(game_state: GameState) -> None:
    player_y_int = int(game_state.player_y)

    for i, (col_x, gap_start) in enumerate(game_state.columns):
        if i not in game_state.passed_columns and col_x < game_state.player_config.START_X:
            if gap_start <= player_y_int < gap_start + game_state.config.GAP_HEIGHT:
                game_state.passed_columns.add(i)
                game_state.score += 1

        if any(int(col_x) == game_state.player_config.START_X + offset
               for offset in range(game_state.player_visible_length)) and \
           not (gap_start <= player_y_int < gap_start + game_state.config.GAP_HEIGHT):
            game_state.game_over = True
            game_state.save_highscore()


def output_frame(frame: str) -> None:
    sys.stdout.write('\033[H')  # Move to top of screen
    sys.stdout.write('\033[2J')  # Clear entire screen
    sys.stdout.write(frame)
    sys.stdout.flush()


if __name__ == "__main__":
    main()
