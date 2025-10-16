"""Grid pathfinding helpers and algorithms used by the Pac-Man AI game.

Provided algorithms
- bfs: Breadth-First Search (shortest path in unweighted grids)
- dfs: Depth-First Search (exploratory, not optimal)
- astar: A* Search (optimal with heuristic, faster toward goal)
"""

from collections import deque  # Efficient FIFO queue for BFS
import heapq  # Priority queue for A*
from typing import Callable, Dict, Iterable, List, Optional, Set, Tuple

Grid = List[str]
Coord = Tuple[int, int]


def in_bounds(grid: Grid, node: Coord) -> bool:
    """Check node is within grid bounds."""
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    r, c = node
    return 0 <= r < rows and 0 <= c < cols


def passable(grid: Grid, node: Coord) -> bool:
    """Check node is not a wall ('#')."""
    r, c = node
    return grid[r][c] != '#'


def neighbors4(grid: Grid, node: Coord) -> Iterable[Coord]:
    """Yield 4-neighborhood passable neighbors (up, down, left, right)."""
    r, c = node
    # Explore in cardinal directions only
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nxt = (r + dr, c + dc)
        if in_bounds(grid, nxt) and passable(grid, nxt):
            yield nxt


def reconstruct_path(came_from: Dict[Coord, Optional[Coord]], start: Coord, goal: Coord) -> List[Coord]:
    """Reconstruct path from start to goal (excluding start)."""
    # If we never reached the goal, there's no path
    if goal not in came_from:
        return []
    cur: Optional[Coord] = goal
    path: List[Coord] = []
    # Walk backward from goal to start via parents
    while cur is not None and cur != start:
        path.append(cur)
        cur = came_from.get(cur)
    path.reverse()
    return path


def bfs(grid: Grid, start: Coord, goal: Coord) -> List[Coord]:
    """Breadth-first search for shortest path in unweighted grid."""
    # Trivial case: already there
    if start == goal:
        return []
    q: deque[Coord] = deque([start])  # Frontier
    came_from: Dict[Coord, Optional[Coord]] = {start: None}  # Parent pointers
    while q:
        cur = q.popleft()  # FIFO ensures level-order exploration
        if cur == goal:
            break
        for nxt in neighbors4(grid, cur):
            # First time we see a node is the shortest way to get there
            if nxt not in came_from:
                came_from[nxt] = cur
                q.append(nxt)
    return reconstruct_path(came_from, start, goal)


def dfs(grid: Grid, start: Coord, goal: Coord) -> List[Coord]:
    """Depth-first search; not optimal but simple and fast for exploration."""
    if start == goal:
        return []
    stack: List[Coord] = [start]  # LIFO stack for DFS
    came_from: Dict[Coord, Optional[Coord]] = {start: None}
    visited: Set[Coord] = set()
    while stack:
        cur = stack.pop()
        if cur in visited:
            continue
        visited.add(cur)
        if cur == goal:
            break
        for nxt in neighbors4(grid, cur):
            # Push unseen neighbors; DFS dives deeper first
            if nxt not in visited and nxt not in came_from:
                came_from[nxt] = cur
                stack.append(nxt)
    return reconstruct_path(came_from, start, goal)


def manhattan(a: Coord, b: Coord) -> int:
    """Manhattan distance heuristic for 4-neighborhood grids."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(grid: Grid, start: Coord, goal: Coord, heuristic: Callable[[Coord, Coord], int] = manhattan) -> List[Coord]:
    """A* search with admissible heuristic for optimal paths in grids."""
    if start == goal:
        return []
    open_heap: List[Tuple[int, Coord]] = []  # (f_score, node)
    heapq.heappush(open_heap, (0, start))
    came_from: Dict[Coord, Optional[Coord]] = {start: None}
    g_score: Dict[Coord, int] = {start: 0}  # Cost from start to node
    while open_heap:
        # Pop the node with lowest estimated total cost f = g + h
        _, cur = heapq.heappop(open_heap)
        if cur == goal:
            break
        for nxt in neighbors4(grid, cur):
            tentative = g_score[cur] + 1  # Uniform edge cost of 1 per move
            # Found a better path to neighbor
            if tentative < g_score.get(nxt, 1_000_000_000):
                came_from[nxt] = cur
                g_score[nxt] = tentative
                f = tentative + heuristic(nxt, goal)
                heapq.heappush(open_heap, (f, nxt))
    return reconstruct_path(came_from, start, goal)


ALGORITHMS: Dict[str, Callable[[Grid, Coord, Coord], List[Coord]]] = {
    'dfs': dfs,
    'bfs': bfs,
    'astar': astar,
}


