"""Pac-Man style AI game with DFS/BFS/A* ghost behaviors and simple UI.

Core concepts
- Grid world from LEVEL where '#' are walls, '.' pellets, 'P' player, 'G' ghosts, 'S' special ghosts.
- Player moves with arrow keys, shoots with 'z'. Ghosts move via selected pathfinding.
- States: menu, playing, paused, game_over. Win by eating all pellets; lose by running out of lives.
"""

import time
import threading
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Callable
import tkinter as tk
import math

from pathfinding import bfs, dfs, astar


Coord = Tuple[int, int]


# Basic level map: '#' walls, '.' pellets, ' ' empty, 'P' player spawn, 'G' ghost spawn, 'S' special ghost
LEVEL: List[str] = [
    "####################",
    "#P.....#G.....#...S#",
    "#.###..#..##..#..#.#",
    "#...#..#..G...#..#.#",
    "#.#.#..###..###..#.#",
    "#.#.#....G......##.#",
    "#.#.####.##.####.#.#",
    "#......G.......#...#",
    "#.####.######..#.###",
    "#....#........S#...#",
    "#.#..#.######..#.###",
    "#.#..#......#..#...#",
    "#.#..#.##.G.#..#.###",
    "#....#..S....#..G.P#",
    "####################",
]


# Rendering scale (tile size in pixels). Smaller number -> smaller window.
TILE = 48
ROWS = len(LEVEL)
COLS = len(LEVEL[0])
WIDTH = COLS * TILE
HEIGHT = ROWS * TILE


class Difficulty:
    EASY = 'easy'      # DFS
    MEDIUM = 'medium'  # BFS
    HARD = 'hard'      # A*


DIFF_ALGO: Dict[str, Callable] = {
    Difficulty.EASY: dfs,
    Difficulty.MEDIUM: bfs,
    Difficulty.HARD: astar,
}


@dataclass
class Entity:
    """A movable actor on the grid (player or ghost)."""
    row: int
    col: int
    color: str
    alive: bool = True
    direction: Coord = (0, 0)
    territory: Optional[List[Coord]] = None  # List of coordinates in ghost's territory
    is_special: bool = False  # Special ghost that always chases

    def pos(self) -> Coord:
        return (self.row, self.col)

    def move(self, drow: int, dcol: int, grid: List[str]) -> None:
        """Attempt to move by (drow, dcol) if destination is not a wall."""
        nr, nc = self.row + drow, self.col + dcol
        if 0 <= nr < ROWS and 0 <= nc < COLS and grid[nr][nc] != '#':
            self.row, self.col = nr, nc
            self.direction = (drow, dcol)

    def is_in_territory(self, pos: Coord) -> bool:
        """Check if a position is within this ghost's territory"""
        if self.is_special:
            return True  # Special ghosts always chase
        if not self.territory:
            return True  # If no territory defined, always chase
        return pos in self.territory


@dataclass
class Beam:
    """A short laser-like projectile from player or ghost."""
    row: int
    col: int
    drow: int
    dcol: int
    color: str
    owner: str  # 'player' or 'ghost'
    active: bool = True

    def step(self, grid: List[str]) -> None:
        """Advance the beam one step or deactivate if hitting wall/bounds."""
        if not self.active:
            return
        nr, nc = self.row + self.drow, self.col + self.dcol
        if not (0 <= nr < ROWS and 0 <= nc < COLS) or grid[nr][nc] == '#':
            self.active = False
            return
        self.row, self.col = nr, nc


class Game:
    """Main game controller: state, entities, input, updates, and rendering."""
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Pac-Man AI - DFS/BFS/A*")
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg='black')
        self.canvas.pack()

        self.grid: List[str] = LEVEL[:]
        self.pellets: Dict[Coord, bool] = {}
        self.player: Optional[Entity] = None
        self.player_spawn: Optional[Coord] = None
        self.ghosts: List[Entity] = []
        self.beams: List[Beam] = []
        self.difficulty: str = Difficulty.MEDIUM
        self.score: int = 0
        self.lives: int = 5
        self.last_ai_tick: float = 0.0
        self.state: str = 'menu'  # 'menu' | 'playing' | 'paused' | 'game_over'

        # Build initial world and UI
        self._parse_level()
        self._bind_keys()
        self._build_menu_ui()
        self._show_menu()
        self._draw()
        self._game_loop()

    def _parse_level(self) -> None:
        """Scan LEVEL to place player, ghosts, and pellets; clear spawns from grid."""
        ghost_count = 0
        special_ghost_count = 0
        for r, line in enumerate(self.grid):
            for c, ch in enumerate(line):
                if ch == 'P':
                    if self.player is None:
                        # First player spawn encountered becomes the spawn point
                        self.player = Entity(r, c, color='yellow')
                        self.player_spawn = (r, c)
                        self._set_grid(r, c, ' ')
                    else:
                        # Handle extra 'P' tiles gracefully: convert to pellet
                        self._set_grid(r, c, ' ')
                        self.pellets[(r, c)] = True
                elif ch == 'G':
                    # Create regular ghost with territory
                    ghost = Entity(r, c, color='red')
                    ghost.territory = self._define_ghost_territory(r, c, ghost_count)
                    self.ghosts.append(ghost)
                    ghost_count += 1
                    self._set_grid(r, c, ' ')
                elif ch == 'S':
                    # Create special ghost that always chases
                    special_ghost = Entity(r, c, color='purple', is_special=True)
                    self.ghosts.append(special_ghost)
                    special_ghost_count += 1
                    self._set_grid(r, c, ' ')
                if ch == '.':
                    # Place pellets on dot tiles only
                    self.pellets[(r, c)] = True

    def _define_ghost_territory(self, start_r: int, start_c: int, ghost_id: int) -> List[Coord]:
        """Define territory for ghost based on its index; defaults to area around spawn."""
        territories = [
            # Ghost 0: Top-right area
            [(r, c) for r in range(1, 8) for c in range(10, 19)],
            # Ghost 1: Middle area  
            [(r, c) for r in range(5, 12) for c in range(1, 19)],
            # Ghost 2: Bottom-left area
            [(r, c) for r in range(10, 14) for c in range(1, 10)],
            # Ghost 3: Bottom-right area
            [(r, c) for r in range(10, 14) for c in range(10, 19)]
        ]
        
        if ghost_id < len(territories):
            return territories[ghost_id]
        else:
            # Default territory: 5x5 area around spawn
            return [(r, c) for r in range(max(0, start_r-2), min(ROWS, start_r+3)) 
                   for c in range(max(0, start_c-2), min(COLS, start_c+3))]

    def _set_grid(self, r: int, c: int, ch: str) -> None:
        """Set a single character in the grid string row."""
        row = list(self.grid[r])
        row[c] = ch
        self.grid[r] = ''.join(row)

    def _bind_keys(self) -> None:
        """Register keyboard controls for movement, shooting, difficulty, and pause."""
        self.root.bind('<Up>', lambda e: self._move_player(-1, 0))
        self.root.bind('<Down>', lambda e: self._move_player(1, 0))
        self.root.bind('<Left>', lambda e: self._move_player(0, -1))
        self.root.bind('<Right>', lambda e: self._move_player(0, 1))
        self.root.bind('z', lambda e: self._fire_player())
        self.root.bind('1', lambda e: self._set_difficulty(Difficulty.EASY))
        self.root.bind('2', lambda e: self._set_difficulty(Difficulty.MEDIUM))
        self.root.bind('3', lambda e: self._set_difficulty(Difficulty.HARD))
        self.root.bind('<Escape>', lambda e: self._toggle_pause())
        # Start the game with Enter when on the menu
        self.root.bind('<Return>', lambda e: self._start_game() if self.state == 'menu' else None)

    def _toggle_pause(self) -> None:
        """Toggle pause state and corresponding overlay."""
        if self.state == 'playing':
            self.state = 'paused'
            self._show_pause()
        elif self.state == 'paused':
            self.state = 'playing'
            self._hide_pause()
        elif self.state == 'menu':
            # no-op in menu
            pass

    def _build_menu_ui(self) -> None:
        """Create menu, pause, and game-over overlays."""
        self.menu_var = tk.StringVar(value=self.difficulty)
        self.menu_frame = tk.Frame(self.root, bg='black')
        self.menu_title = tk.Label(self.menu_frame, text='Pac-Man AI', fg='yellow', bg='black', font=('Arial', 16, 'bold'))
        self.menu_title.pack(pady=10)
        self.diff_label = tk.Label(self.menu_frame, text='Select Difficulty', fg='white', bg='black', font=('Arial', 12))
        self.diff_label.pack(pady=5)
        self.diff_easy = tk.Radiobutton(self.menu_frame, text='Easy (DFS)', variable=self.menu_var, value=Difficulty.EASY, fg='white', bg='black', selectcolor='gray', activebackground='black')
        self.diff_med = tk.Radiobutton(self.menu_frame, text='Medium (BFS)', variable=self.menu_var, value=Difficulty.MEDIUM, fg='white', bg='black', selectcolor='gray', activebackground='black')
        self.diff_hard = tk.Radiobutton(self.menu_frame, text='Hard (A*)', variable=self.menu_var, value=Difficulty.HARD, fg='white', bg='black', selectcolor='gray', activebackground='black')
        self.diff_easy.pack(anchor='w', padx=10)
        self.diff_med.pack(anchor='w', padx=10)
        self.diff_hard.pack(anchor='w', padx=10)
        self.start_btn = tk.Button(self.menu_frame, text='Start Game', command=self._start_game, padx=10, pady=5, bg='blue', fg='white', activebackground='darkblue')
        self.quit_btn = tk.Button(self.menu_frame, text='Quit', command=self.root.destroy, padx=10, pady=5, bg='gray', fg='white', activebackground='darkgray')
        self.start_btn.pack(pady=(10, 5))
        self.quit_btn.pack()

        # Pause overlay
        self.pause_frame = tk.Frame(self.root, bg='black')
        self.pause_label = tk.Label(self.pause_frame, text='Paused', fg='yellow', bg='black', font=('Arial', 14, 'bold'))
        self.pause_label.pack(pady=10)
        self.resume_btn = tk.Button(self.pause_frame, text='Resume', command=self._resume_from_pause, padx=10, pady=5, bg='blue', fg='white', activebackground='darkblue')
        self.to_menu_btn = tk.Button(self.pause_frame, text='Quit to Menu', command=self._quit_to_menu, padx=10, pady=5, bg='gray', fg='white', activebackground='darkgray')
        self.resume_btn.pack(pady=(5, 5))
        self.to_menu_btn.pack()

        # Game over overlay
        self.game_over_frame = tk.Frame(self.root, bg='black')
        self.game_over_label = tk.Label(self.game_over_frame, text='Game Over', fg='red', bg='black', font=('Arial', 18, 'bold'))
        self.game_over_label.pack(pady=10)
        self.final_score_label = tk.Label(self.game_over_frame, text='', fg='white', bg='black', font=('Arial', 12))
        self.final_score_label.pack(pady=5)
        self.restart_btn = tk.Button(self.game_over_frame, text='Restart', command=self._restart_game, padx=10, pady=5, bg='blue', fg='white', activebackground='darkblue')
        self.menu_btn = tk.Button(self.game_over_frame, text='Main Menu', command=self._quit_to_menu, padx=10, pady=5, bg='gray', fg='white', activebackground='darkgray')
        self.restart_btn.pack(pady=(5, 5))
        self.menu_btn.pack()


    def _start_game(self) -> None:
        """Start a new game from menu with selected difficulty."""
        self.difficulty = self.menu_var.get()
        self._hide_menu()
        self._reset_level()
        self.lives = 5  # Reset lives to 5
        # Ensure default overlay label
        self.game_over_label.config(text='Game Over')
        self.state = 'playing'

    def _resume_from_pause(self) -> None:
        """Resume gameplay from pause overlay."""
        self.state = 'playing'
        self._hide_pause()

    def _quit_to_menu(self) -> None:
        """Return to main menu from pause or game-over screens."""
        self.state = 'menu'
        self._hide_pause()
        self._hide_game_over()
        self._show_menu()

    def _restart_game(self) -> None:
        """Restart gameplay from game-over screen."""
        self._hide_game_over()
        self._reset_level()
        self.lives = 5
        # Ensure default overlay label
        self.game_over_label.config(text='Game Over')
        self.state = 'playing'

    def _show_game_over(self) -> None:
        """Display game-over (or win) overlay with final score."""
        self.final_score_label.config(text=f'Final Score: {self.score}')
        self.game_over_frame.place(x=WIDTH//2 - 100, y=HEIGHT//2 - 80, width=200, height=160)
        self.game_over_frame.lift()

    def _hide_game_over(self) -> None:
        self.game_over_frame.place_forget()

    def _show_menu(self) -> None:
        # Center menu over canvas
        self.menu_frame.place(x=WIDTH//2 - 140, y=HEIGHT//2 - 120, width=280, height=240)
        self.menu_frame.lift()  # Bring to front

    def _hide_menu(self) -> None:
        self.menu_frame.place_forget()

    def _show_pause(self) -> None:
        self.pause_frame.place(x=WIDTH//2 - 120, y=HEIGHT//2 - 90, width=240, height=180)
        self.pause_frame.lift()  # Bring to front

    def _hide_pause(self) -> None:
        self.pause_frame.place_forget()

    def _reset_level(self) -> None:
        # Reinitialize game world to the starting state
        self.grid = LEVEL[:]
        self.pellets = {}
        self.player = None
        self.player_spawn = None
        self.ghosts = []
        self.beams = []
        self.score = 0
        self.lives = 5
        self._parse_level()

    def _set_difficulty(self, d: str) -> None:
        # Allow difficulty change only in menu or paused
        if self.state in ('menu', 'paused'):
            self.difficulty = d
            if hasattr(self, 'menu_var'):
                self.menu_var.set(d)

    def _move_player(self, dr: int, dc: int) -> None:
        """Move player by (dr, dc), eat pellet, update score, and check win."""
        if self.state != 'playing':
            return
        if not self.player or not self.player.alive:
            return
        self.player.move(dr, dc, self.grid)
        # Eat pellet if exists
        pos = self.player.pos()
        if pos in self.pellets and self.pellets[pos]:
            self.pellets[pos] = False
            self.score += 10
            # Check win condition
            if self._check_win():
                self._handle_win()

    def _fire_player(self) -> None:
        """Fire a short beam in the player's current (or default) direction."""
        if self.state != 'playing':
            return
        if not self.player:
            return
        drow, dcol = self.player.direction
        if drow == 0 and dcol == 0:
            drow, dcol = (0, 1)
        br, bc = self.player.row, self.player.col
        beam = Beam(br, bc, drow, dcol, color='yellow', owner='player')
        self.beams.append(beam)

    def _ghost_fire(self, ghost: Entity) -> None:
        """Have a ghost fire a beam along its current direction if moving."""
        drow, dcol = ghost.direction
        if drow == 0 and dcol == 0:
            return
        beam = Beam(ghost.row, ghost.col, drow, dcol, color='cyan', owner='ghost')
        self.beams.append(beam)

    def _game_loop(self) -> None:
        """Heartbeat: update AI and beams at ~30 FPS with ~5 Hz AI ticks."""
        now = time.time()
        if self.state == 'playing':
            if now - self.last_ai_tick > 0.2:  # AI tick ~5 Hz
                self._update_ai()
                self.last_ai_tick = now
            self._update_beams()
            self._check_collisions()
        self._draw()
        self.root.after(33, self._game_loop)  # ~30 FPS

    def _update_ai(self) -> None:
        """Update each ghost: pathfind toward player or patrol; handle firing cadence."""
        if not self.player:
            return
        algo = DIFF_ALGO.get(self.difficulty, bfs)
        target = self.player.pos()
        
        for ghost in self.ghosts:
            if not ghost.alive:
                continue
            
            # Special ghosts always chase, regular ghosts only chase in territory
            should_chase = ghost.is_special or ghost.is_in_territory(target)
            
            if should_chase:
                # Use pathfinding to chase Pac-Man
                path: List[Coord] = algo(self.grid, ghost.pos(), target)
                if path and len(path) > 0:
                    nr, nc = path[0]
                    drow = nr - ghost.row
                    dcol = nc - ghost.col
                    ghost.move(drow, dcol, self.grid)
                else:
                    # If no path found, try to move towards target directly
                    self._move_towards_target(ghost, target)
                
                # Distance-gated, probabilistic firing (less aggressive overall)
                gr, gc = ghost.pos()
                pr, pc = target
                dist = abs(gr - pr) + abs(gc - pc)
                if dist <= 6:
                    import random
                    if ghost.is_special:
                        fire_p = 0.25  # 25% chance per AI tick in range
                    elif self.difficulty == Difficulty.HARD:
                        fire_p = 0.20
                    elif self.difficulty == Difficulty.MEDIUM:
                        fire_p = 0.12
                    else:  # EASY
                        fire_p = 0.08
                    if random.random() < fire_p:
                        self._ghost_fire(ghost)
            else:
                # When not in territory, move randomly or patrol
                self._patrol_ghost(ghost)

    def _update_beams(self) -> None:
        """Advance active beams and drop inactive ones."""
        for beam in self.beams:
            if beam.active:
                beam.step(self.grid)
        # remove inactive
        self.beams = [b for b in self.beams if b.active]

    def _check_collisions(self) -> None:
        """Resolve beam hits and ghost-player contact; also re-check win."""
        if not self.player:
            return
        # Beam vs Ghost / Player
        for beam in list(self.beams):
            if not beam.active:
                continue
            if beam.owner == 'player':
                for ghost in self.ghosts:
                    if ghost.alive and (ghost.row, ghost.col) == (beam.row, beam.col):
                        ghost.alive = False
                        beam.active = False
                        self._schedule_ghost_respawn(ghost)
                        self.score += 100  # Bonus for hitting ghost
                        break
            else:  # ghost beam
                if self.player.alive and (self.player.row, self.player.col) == (beam.row, beam.col):
                    # Player hit by ghost beam -> lose life
                    self._lose_life()
                    beam.active = False

        # Ghost touch player -> lose life
        for ghost in self.ghosts:
            if ghost.alive and self.player.alive and ghost.pos() == self.player.pos():
                self._lose_life()

        # If all pellets are eaten due to ghost-player collision side effects, still win
        if self.state == 'playing' and self._check_win():
            self._handle_win()

    def _lose_life(self) -> None:
        """Decrement lives and respawn player or end game."""
        if self.lives > 0:
            self.lives -= 1
            if self.lives <= 0:
                self.state = 'game_over'
                self._show_game_over()
            else:
                # Reset player position to starting position
                if self.player:
                    # Use remembered spawn if available
                    if self.player_spawn is not None:
                        self.player.row, self.player.col = self.player_spawn
                        self.player.direction = (0, 0)

    def _move_towards_target(self, ghost: Entity, target: Coord) -> None:
        """Move a ghost one step in the general direction of target if possible."""
        tr, tc = target
        gr, gc = ghost.pos()
        
        # Calculate direction to target
        dr = 0
        dc = 0
        if tr > gr:
            dr = 1
        elif tr < gr:
            dr = -1
        if tc > gc:
            dc = 1
        elif tc < gc:
            dc = -1
        
        # Try to move in the calculated direction
        ghost.move(dr, dc, self.grid)

    def _patrol_ghost(self, ghost: Entity) -> None:
        """Patrol within territory by occasionally picking a random valid direction."""
        import random
        
        # Slightly lower patrol change rates to make pursuit less erratic
        if self.difficulty == Difficulty.EASY:
            patrol_chance = 0.18
        elif self.difficulty == Difficulty.MEDIUM:
            patrol_chance = 0.28
        else:  # HARD
            patrol_chance = 0.38
        
        # Try to move in a random direction
        if random.random() < patrol_chance:
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Up, Down, Left, Right
            random.shuffle(directions)  # Randomize order
            
            # Try each direction until one works
            for drow, dcol in directions:
                # Check if this move would keep ghost in their territory
                new_pos = (ghost.row + drow, ghost.col + dcol)
                if ghost.is_in_territory(new_pos):
                    # Try to move in this direction
                    old_pos = ghost.pos()
                    ghost.move(drow, dcol, self.grid)
                    # If movement was successful, break
                    if ghost.pos() != old_pos:
                        break
                else:
                    # If not in territory, try the move anyway (might be at edge)
                    old_pos = ghost.pos()
                    ghost.move(drow, dcol, self.grid)
                    if ghost.pos() != old_pos:
                        break

    def _schedule_ghost_respawn(self, ghost: Entity) -> None:
        """Revive a defeated ghost after a short delay on a background thread."""
        def revive():
            if ghost.is_special:
                time.sleep(3.0)  # 3 seconds for special ghosts
            else:
                time.sleep(4.0)  # 4 seconds for regular ghosts
            ghost.alive = True
        threading.Thread(target=revive, daemon=True).start()

    def _draw(self) -> None:
        """Render the grid, pellets, entities, beams, hearts, and UI overlays."""
        self.canvas.delete('all')
        # Draw grid
        for r in range(ROWS):
            for c in range(COLS):
                x0 = c * TILE
                y0 = r * TILE
                x1 = x0 + TILE
                y1 = y0 + TILE
                ch = self.grid[r][c]
                if ch == '#':
                    # Vivid walls with subtle outline
                    self.canvas.create_rectangle(x0, y0, x1, y1, fill='#0b2a6b', outline='#14408f')
                else:
                    self.canvas.create_rectangle(x0, y0, x1, y1, fill='black', outline='#0a0a0a')
                # pellets
                if self.pellets.get((r, c), False):
                    self.canvas.create_oval(x0 + TILE//2 - 2, y0 + TILE//2 - 2, x0 + TILE//2 + 2, y0 + TILE//2 + 2, fill='#ffd700', outline='')


        # Draw entities
        if self.player and self.player.alive:
            self._draw_pacman(self.player.col, self.player.row, direction=self.player.direction)
        for ghost in self.ghosts:
            if ghost.alive:
                # All regular ghosts are the same red color
                if ghost.is_special:
                    ghost_color = '#800080'  # Purple for special ghosts only
                else:
                    ghost_color = '#ff0000'  # Red for all regular ghosts
                self._draw_ghost(ghost.col, ghost.row, direction=ghost.direction, ghost_color=ghost_color)
            else:
                # Draw faint respawn marker
                if ghost.is_special:
                    self._draw_ghost(ghost.col, ghost.row, direction=(0, 0), ghost_color='#330033', pupil_color='#222222')
                else:
                    self._draw_ghost(ghost.col, ghost.row, direction=(0, 0), ghost_color='#551111', pupil_color='#222222')

        # Draw beams
        for beam in self.beams:
            bx = beam.col * TILE + TILE//2
            by = beam.row * TILE + TILE//2
            length = TILE // 2
            thickness = 4
            dx = beam.dcol
            dy = beam.drow
            if dx != 0:
                x0 = bx - (length if dx < 0 else 0)
                x1 = bx + (length if dx > 0 else 0)
                y0 = by - thickness//2
                y1 = by + thickness//2
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=beam.color, outline='')
            elif dy != 0:
                y0 = by - (length if dy < 0 else 0)
                y1 = by + (length if dy > 0 else 0)
                x0 = bx - thickness//2
                x1 = bx + thickness//2
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=beam.color, outline='')

        # Draw hearts at top-left corner
        self._draw_hearts()

        # UI overlay
        self.canvas.create_text(8, HEIGHT - 10, anchor='w', fill='#e6e6e6',
                                 text=f"Score: {self.score}   [1]DFS  [2]BFS  [3]A*   Difficulty: {self.difficulty.upper()}   [Esc] Pause")

        # Menu hint overlay when in menu
        if self.state == 'menu':
            self.canvas.create_text(WIDTH//2, HEIGHT//2 + 150, anchor='n', fill='#bbbbbb',
                                     text='Use 1/2/3 to choose algorithm. Click Start to play.', font=('Segoe UI', 10))
        elif self.state == 'paused':
            # Dim the background
            self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill='#000000', outline='', stipple='gray50')
            self.canvas.create_text(WIDTH//2, HEIGHT//2 - 120, fill='white', text='Game Paused', font=('Segoe UI', 16, 'bold'))
        elif self.state == 'game_over' and self.game_over_label.cget('text') == 'You Win!':
            # Dim background slightly for win as well
            self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill='#000000', outline='', stipple='gray25')

    def _draw_circle(self, grid_c: int, grid_r: int, fill: str) -> None:
        """Draw a filled circle inside a tile (helper)."""
        x0 = grid_c * TILE + 2
        y0 = grid_r * TILE + 2
        x1 = x0 + TILE - 4
        y1 = y0 + TILE - 4
        self.canvas.create_oval(x0, y0, x1, y1, fill=fill, outline='')

    def _draw_pacman(self, grid_c: int, grid_r: int, direction: Coord) -> None:
        """Draw animated Pac-Man with mouth angle based on time and direction."""
        x0 = grid_c * TILE + 2
        y0 = grid_r * TILE + 2
        x1 = x0 + TILE - 4
        y1 = y0 + TILE - 4
        # Mouth animation oscillates between 10 and 45 degrees
        t = time.time()
        mouth = 10 + (math.sin(t * 8) * 0.5 + 0.5) * 35
        drow, dcol = direction
        # Determine facing angle
        if drow == 0 and dcol == 0:
            angle = 0
        elif dcol == 1:
            angle = 0    # right
        elif dcol == -1:
            angle = 180  # left
        elif drow == -1:
            angle = 90   # up
        else:
            angle = 270  # down
        start = angle + mouth
        extent = 360 - mouth * 2
        self.canvas.create_arc(x0, y0, x1, y1, start=start, extent=extent, fill='yellow', outline='', style=tk.PIESLICE)

    def _draw_ghost(self, grid_c: int, grid_r: int, direction: Coord, ghost_color: str = '#ff3b3b', pupil_color: str = '#3b8bff') -> None:
        """Draw a stylized ghost with eyes that drift toward movement direction."""
        x = grid_c * TILE
        y = grid_r * TILE
        pad = 2
        x0 = x + pad
        y0 = y + pad
        x1 = x + TILE - pad
        y1 = y + TILE - pad
        # Body (rounded top via oval, bottom with frills)
        body_top = self.canvas.create_oval(x0, y0, x1, y1 - 6, fill=ghost_color, outline='')
        body_rect = self.canvas.create_rectangle(x0, (y0 + y1)//2, x1, y1 - 2, fill=ghost_color, outline='')
        frill_w = (x1 - x0) // 4
        for i in range(4):
            fx0 = x0 + i * frill_w
            fx1 = fx0 + frill_w
            self.canvas.create_oval(fx0, y1 - 8, fx1, y1, fill=ghost_color, outline='')
        # Eyes
        eye_w = 6
        eye_h = 8
        eye_offset_x = 6
        eye_offset_y = 6
        left_eye_x0 = x0 + eye_offset_x
        left_eye_y0 = y0 + eye_offset_y
        right_eye_x0 = x1 - eye_offset_x - eye_w
        right_eye_y0 = y0 + eye_offset_y
        self.canvas.create_oval(left_eye_x0, left_eye_y0, left_eye_x0 + eye_w, left_eye_y0 + eye_h, fill='white', outline='')
        self.canvas.create_oval(right_eye_x0, right_eye_y0, right_eye_x0 + eye_w, right_eye_y0 + eye_h, fill='white', outline='')
        # Pupils drift toward movement direction
        px = 0
        py = 0
        if direction[1] > 0:
            px = 2
        elif direction[1] < 0:
            px = -2
        if direction[0] > 0:
            py = 2
        elif direction[0] < 0:
            py = -2
        self.canvas.create_oval(left_eye_x0 + 2 + px, left_eye_y0 + 3 + py, left_eye_x0 + 2 + px + 3, left_eye_y0 + 3 + py + 3, fill=pupil_color, outline='')
        self.canvas.create_oval(right_eye_x0 + 2 + px, right_eye_y0 + 3 + py, right_eye_x0 + 2 + px + 3, right_eye_y0 + 3 + py + 3, fill=pupil_color, outline='')

    def _draw_hearts(self) -> None:
        # Draw hearts at top-left corner (only during gameplay)
        if self.state != 'playing':
            return
        
        heart_size = 20
        heart_spacing = 25
        start_x = 10
        start_y = 10
        
        for i in range(5):
            x = start_x + i * heart_spacing
            y = start_y
            
            if i < self.lives:
                # Full heart (red)
                self.canvas.create_text(x, y, text='♥', fill='red', font=('Arial', heart_size, 'bold'))
            else:
                # Empty heart (gray)
                self.canvas.create_text(x, y, text='♡', fill='#444444', font=('Arial', heart_size, 'bold'))

    def _check_win(self) -> bool:
        # Win when all pellets are eaten
        return not any(self.pellets.values()) if self.pellets else False

    def _handle_win(self) -> None:
        # Stop gameplay and show win overlay using existing frame
        self.state = 'game_over'
        self.final_score_label.config(text=f'Final Score: {self.score}')
        self.game_over_label.config(text='You Win!')
        self._show_game_over()



def main() -> None:
    root = tk.Tk()
    Game(root)
    root.mainloop()


if __name__ == '__main__':
    main()


