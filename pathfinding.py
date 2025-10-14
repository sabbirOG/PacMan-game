from collections import deque
import heapq
from typing import Callable, Dict, Iterable, List, Optional, Set, Tuple

Grid = List[str]
Coord = Tuple[int, int]


def in_bounds(grid: Grid, node: Coord) -> bool:
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    r, c = node
    return 0 <= r < rows and 0 <= c < cols


def passable(grid: Grid, node: Coord) -> bool:
    r, c = node
    return grid[r][c] != '#'


def neighbors4(grid: Grid, node: Coord) -> Iterable[Coord]:
    r, c = node
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nxt = (r + dr, c + dc)
        if in_bounds(grid, nxt) and passable(grid, nxt):
            yield nxt


def reconstruct_path(came_from: Dict[Coord, Optional[Coord]], start: Coord, goal: Coord) -> List[Coord]:
    if goal not in came_from:
        return []
    cur: Optional[Coord] = goal
    path: List[Coord] = []
    while cur is not None and cur != start:
        path.append(cur)
        cur = came_from.get(cur)
    path.reverse()
    return path


def bfs(grid: Grid, start: Coord, goal: Coord) -> List[Coord]:
    if start == goal:
        return []
    q: deque[Coord] = deque([start])
    came_from: Dict[Coord, Optional[Coord]] = {start: None}
    while q:
        cur = q.popleft()
        if cur == goal:
            break
        for nxt in neighbors4(grid, cur):
            if nxt not in came_from:
                came_from[nxt] = cur
                q.append(nxt)
    return reconstruct_path(came_from, start, goal)


def dfs(grid: Grid, start: Coord, goal: Coord) -> List[Coord]:
    if start == goal:
        return []
    stack: List[Coord] = [start]
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
            if nxt not in visited and nxt not in came_from:
                came_from[nxt] = cur
                stack.append(nxt)
    return reconstruct_path(came_from, start, goal)


def manhattan(a: Coord, b: Coord) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(grid: Grid, start: Coord, goal: Coord, heuristic: Callable[[Coord, Coord], int] = manhattan) -> List[Coord]:
    if start == goal:
        return []
    open_heap: List[Tuple[int, Coord]] = []
    heapq.heappush(open_heap, (0, start))
    came_from: Dict[Coord, Optional[Coord]] = {start: None}
    g_score: Dict[Coord, int] = {start: 0}
    while open_heap:
        _, cur = heapq.heappop(open_heap)
        if cur == goal:
            break
        for nxt in neighbors4(grid, cur):
            tentative = g_score[cur] + 1
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


