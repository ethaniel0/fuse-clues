from abc import ABC, abstractmethod
from dataclasses import dataclass
import re
from typing import override
import simpleeval
import random

@dataclass
class Action(ABC):
    @abstractmethod
    def execute(self, ctx: dict) -> dict[str, any]:
        pass

@dataclass
class SetValueAction(Action):
    value: any

    @override
    def execute(self, ctx: dict):
        return {'value': self.value}
    
@dataclass
class SetValueEvalAction(Action):
    eval_str: str

    @override
    def execute(self, ctx: dict):
        def simple_read_file(filename):
            # get real path with respect to ctx['path'] as root, to prevent reading arbitrary files outside of the game directory
            from engine.config_tools import get_real_path
            path = get_real_path(filename, ctx['path'])
            try:
                with open(path, 'r') as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading file {path}: {e}")
                return ''
            
        val = simpleeval.simple_eval(self.eval_str, names={
            'ctx': {*ctx},
        }, functions={
            'chr': chr,
            'len': len,
            'ord': ord,
            'max': max,
            'min': min,
            'read_file': simple_read_file,
            'randint': random.randint,
            'rand_seed': random.seed,
            **simpleeval.DEFAULT_FUNCTIONS
        })
        return {'value': val}
    

@dataclass
class MapToEntityAction(Action):
    target_path: str

    @override
    def execute(self, ctx: dict):
        return {'map_to': self.target_path}
    
@dataclass
class AllowDenyAction(Action):
    allow: bool

    @override
    def execute(self, ctx: dict):
        return {'allow': self.allow}

@dataclass
class DisplayAsAction(Action):
    allow: bool

    @override
    def execute(self, ctx: dict):
        return {'display': self.allow}

@dataclass
class WriteAttributeAction(Action):
    attribute: str
    value: str

    @override
    def execute(self, ctx: dict):
        ctx["state"][self.attribute] = self.value
        return {}

@dataclass
class ReadWriteContentTextAction(Action):
    content_str: str

    '''
    Note: When used with OffsetCondition, content_str + its corresponding offset must be less than the length of the original file
    '''

    @override
    def execute(self, ctx: dict):
        if ctx['offset'] >= len(self.content_str):
            return {'value': b''}
        return {'value': self.content_str[ctx['offset'] : ctx['offset'] + ctx.get('size', len(self.content_str))]}

@dataclass
class ReadWriteContentFileAction(Action):
    content_filename: str

    @override
    def execute(self, ctx: dict):
        with open(self.content_filename, 'r') as f:
            content = f.read()
        return {'value': content}

@dataclass
class ReadWriteContentEvalAction(Action):
    eval_str: str

    @override
    def execute(self, ctx: dict):
        from engine.config_tools import map_to_path, get_real_path

        game_virt = map_to_path(ctx['path'], "_game.state", "/")
        game_real = get_real_path(game_virt, "/")
        val = simpleeval.simple_eval(self.eval_str, names={
            'size': ctx.get('size', 0),
            'offset': ctx.get('offset', 0),
            'file_content': game_real,
            'data': ctx.get('data', b''),
            'data_str': ctx.get('data', b'').decode(errors='ignore'),
        }, functions={
            'chr': chr,
            'len': len,
            'ord': ord,
            'max': max,
            'min': min,
            'move_board': move_board,
            **simpleeval.DEFAULT_FUNCTIONS
        })
        return {'value': val.encode() if isinstance(val, str) else val}

def move_board(file_path: str, direction: str) -> str:
    print(f"\n=== move_board called ===")
    print(f"raw input:\n{direction}")

    # --- EXTRACT ALL DIRECTIONS ---
    direction = direction.lower()

    # Map WASD → full words
    wasd_map = {
        'w': 'up',
        'a': 'left',
        's': 'down',
        'd': 'right'
    }

    # Replace standalone w/a/s/d with full directions
    direction = re.sub(r'\b([wasd])\b', lambda m: wasd_map[m.group(1)], direction)

    # Extract directions
    tokens = re.findall(r'\b(up|down|left|right)\b', direction)

    if tokens:
        print(f"Detected directions: {tokens}")
    else:
        print("No valid directions found, skipping move")

    # --- READ STATE ---
    try:
        with open(file_path, 'r') as f:
            board = f.read().strip()
    except Exception as e:
        print("Error reading file:", e)
        board = "123456780"  # fallback

    print(f"current board state: {board}")

    # --- VALIDATE ---
    if len(board) != 9 or not all(c.isdigit() for c in board):
        print("Invalid board format, resetting")
        board = "123456780"

    # --- MOVE LOGIC SETUP ---
    moves = {
        'up': (1, 0),
        'down': (-1, 0),
        'left': (0, 1),
        'right': (0, -1)
    }

    grid = list(board)

    # --- APPLY MOVES ONE BY ONE ---
    for d in tokens:
        print(f"\nApplying move: {d}")

        idx = grid.index('0')
        r, c = divmod(idx, 3)

        dr, dc = moves[d]
        nr, nc = r + dr, c + dc

        if 0 <= nr < 3 and 0 <= nc < 3:
            nidx = nr * 3 + nc
            grid[idx], grid[nidx] = grid[nidx], grid[idx]
            print(f"Board after move {d}: {''.join(grid)}")
        else:
            print(f"Move {d} invalid (out of bounds), skipping")

    board = ''.join(grid)
    print(f"\nfinal board state: {board}")

    # --- WRITE BACK STATE ---
    try:
        with open(file_path, 'w') as f:
            f.write(board)
    except Exception as e:
        print("Error writing file:", e)

    # --- CHECK SOLVED ---
    solved = (board == "123456780")

    # --- RENDER ---
    def fmt(c):
        return ' ' if c == '0' else c

    rows = [board[i:i+3] for i in range(0, 9, 3)]
    sep = "+---+---+---+"

    def render_row(row):
        return "| " + " | ".join(fmt(c) for c in row) + " |"

    if solved:
        return (
            "SESSION RECOVERED\n\n"
            f"{sep}\n{render_row(rows[0])}\n"
            f"{sep}\n{render_row(rows[1])}\n"
            f"{sep}\n{render_row(rows[2])}\n"
            f"{sep}\n\n"
            "authentication restored\n"
            "access granted!\n\n"
        )
    else:
        return (
            "SESSION RECOVERY PUZZLE — ACTIVE\n\n"
            f"{sep}\n{render_row(rows[0])}\n"
            f"{sep}\n{render_row(rows[1])}\n"
            f"{sep}\n{render_row(rows[2])}\n"
            f"{sep}\n\n"
            "Enter directions to play:\n"
        )

# def move_board(file_path: str, direction: str) -> str:
#     print(f"\n=== move_board called ===")
#     print(f"raw input:\n{direction}")

#     # --- EXTRACT ALL DIRECTIONS ---
#     direction = direction.lower()
#     tokens = re.findall(r'\b(up|down|left|right)\b', direction)

#     if tokens:
#         print(f"Detected directions: {tokens}")
#     else:
#         print("No valid directions found, skipping move")

#     # --- READ STATE ---
#     try:
#         with open(file_path, 'r') as f:
#             board = f.read().strip()
#     except Exception as e:
#         print("Error reading file:", e)
#         board = "123456780"  # fallback

#     print(f"current board state: {board}")

#     # --- VALIDATE ---
#     if len(board) != 9 or not all(c.isdigit() for c in board):
#         print("Invalid board format, resetting")
#         board = "123456780"

#     # --- MOVE LOGIC SETUP ---
#     moves = {
#         'up': (-1, 0),
#         'down': (1, 0),
#         'left': (0, -1),
#         'right': (0, 1)
#     }

#     grid = list(board)

#     # --- APPLY MOVES ONE BY ONE ---
#     for d in tokens:
#         print(f"\nApplying move: {d}")

#         idx = grid.index('0')
#         r, c = divmod(idx, 3)

#         dr, dc = moves[d]
#         nr, nc = r + dr, c + dc

#         if 0 <= nr < 3 and 0 <= nc < 3:
#             nidx = nr * 3 + nc
#             grid[idx], grid[nidx] = grid[nidx], grid[idx]
#             print(f"Board after move {d}: {''.join(grid)}")
#         else:
#             print(f"Move {d} invalid (out of bounds), skipping")

#     board = ''.join(grid)
#     print(f"\nfinal board state: {board}")

#     # --- WRITE BACK STATE ---
#     try:
#         with open(file_path, 'w') as f:
#             f.write(board)
#     except Exception as e:
#         print("Error writing file:", e)

#     # --- CHECK SOLVED ---
#     solved = (board == "123456780")

#     # --- RENDER ---
#     def fmt(c):
#         return ' ' if c == '0' else c

#     rows = [board[i:i+3] for i in range(0, 9, 3)]
#     sep = "+---+---+---+"

#     def render_row(row):
#         return "| " + " | ".join(fmt(c) for c in row) + " |"

#     if solved:
#         return (
#             "SESSION RECOVERED\n\n"
#             f"{sep}\n{render_row(rows[0])}\n"
#             f"{sep}\n{render_row(rows[1])}\n"
#             f"{sep}\n{render_row(rows[2])}\n"
#             f"{sep}\n\n"
#             "authentication restored\n"
#             "access granted!\n\n"
#         )
#     else:
#         return (
#             "SESSION RECOVERY PUZZLE — ACTIVE\n\n"
#             f"{sep}\n{render_row(rows[0])}\n"
#             f"{sep}\n{render_row(rows[1])}\n"
#             f"{sep}\n{render_row(rows[2])}\n"
#             f"{sep}\n\n"
#             "Enter a direction to play, you can enter multiple directions at once!\n"
#         )
