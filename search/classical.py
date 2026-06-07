from collections import deque
import heapq
import time


def manhattan(a, b) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def _fail_result(visited: set, expanded: int, elapsed_ms: float,
                 max_frontier: int) -> dict:
    return {
        'sucesso':      False,
        'caminho':         [],
        'custo':         0,
        'passos':        0,
        'expandidos':     expanded,
        'tempo_ms':      elapsed_ms,
        'fronteira_max': max_frontier,
        '_conjunto_explorados': visited,
        'desempenho': 0,
        'formula_desempenho': 'J = - 0.7*Custo - 0.05*Expandidos - 0.20*Tempo - 0.05*Fronteira',
    }


def _success_result(path: list, visited: set, expanded: int,
                    elapsed_ms: float, max_frontier: int) -> dict:
    steps = len(path) - 1
    desempenho = -0.7 * steps - 0.05 * expanded - 0.20 * elapsed_ms - 0.05 * max_frontier
    return {
        'sucesso':      True,
        'caminho':         path,
        'custo':         steps,
        'passos':        steps,
        'expandidos':     expanded,
        'tempo_ms':      elapsed_ms,
        'fronteira_max': max_frontier,
        '_conjunto_explorados': visited,
        'desempenho': desempenho,
        'formula_desempenho': 'J = - 0.7*Custo - 0.05*Expandidos - 0.20*Tempo - 0.05*Fronteira',
    }

def bfs(maze, start, goal) -> dict:
    t0 = time.perf_counter()

    frontier = deque()
    frontier.append((start, [start]))
    visited = {start}
    expanded = 0
    max_frontier = 1

    while frontier:
        max_frontier = max(max_frontier, len(frontier))
        pos, path = frontier.popleft()
        expanded += 1

        if pos == goal:
            elapsed = (time.perf_counter() - t0) * 1000
            return _success_result(path, visited, expanded,
                                   elapsed, max_frontier)

        for neighbour in maze.neighbors(*pos):
            if neighbour not in visited:
                visited.add(neighbour)
                frontier.append((neighbour, path + [neighbour]))

    elapsed = (time.perf_counter() - t0) * 1000
    return _fail_result(visited, expanded, elapsed, max_frontier)

def dfs(maze, start, goal) -> dict:
    t0 = time.perf_counter()

    frontier = [(start, [start])]
    visited: set = set()
    expanded = 0
    max_frontier = 1

    while frontier:
        max_frontier = max(max_frontier, len(frontier))
        pos, path = frontier.pop()

        if pos in visited:
            continue

        visited.add(pos)
        expanded += 1

        if pos == goal:
            elapsed = (time.perf_counter() - t0) * 1000
            return _success_result(path, visited, expanded,
                                   elapsed, max_frontier)

        for neighbour in maze.neighbors(*pos):
            if neighbour not in visited:
                frontier.append((neighbour, path + [neighbour]))

    elapsed = (time.perf_counter() - t0) * 1000
    return _fail_result(visited, expanded, elapsed, max_frontier)


def ucs(maze, start, goal) -> dict:
    t0 = time.perf_counter()

    counter = 0
    frontier: list = []
    heapq.heappush(frontier, (0, counter, start, [start]))
    visited: set = set()
    expanded = 0
    max_frontier = 1

    while frontier:
        max_frontier = max(max_frontier, len(frontier))
        g, _cnt, pos, path = heapq.heappop(frontier)

        if pos in visited:
            continue

        visited.add(pos)
        expanded += 1

        if pos == goal:
            elapsed = (time.perf_counter() - t0) * 1000
            return _success_result(path, visited, expanded,
                                   elapsed, max_frontier)

        for neighbour in maze.neighbors(*pos):
            if neighbour not in visited:
                counter += 1
                new_g = g + 1
                heapq.heappush(frontier,
                               (new_g, counter, neighbour, path + [neighbour]))

    elapsed = (time.perf_counter() - t0) * 1000
    return _fail_result(visited, expanded, elapsed, max_frontier)


def greedy(maze, start, goal) -> dict:
    t0 = time.perf_counter()

    counter = 0
    h0 = manhattan(start, goal)
    frontier: list = []
    heapq.heappush(frontier, (h0, counter, start, [start]))
    visited: set = set()
    expanded = 0
    max_frontier = 1

    while frontier:
        max_frontier = max(max_frontier, len(frontier))
        _h, _cnt, pos, path = heapq.heappop(frontier)

        if pos in visited:
            continue

        visited.add(pos)
        expanded += 1

        if pos == goal:
            elapsed = (time.perf_counter() - t0) * 1000
            return _success_result(path, visited, expanded,
                                   elapsed, max_frontier)

        for neighbour in maze.neighbors(*pos):
            if neighbour not in visited:
                counter += 1
                h = manhattan(neighbour, goal)
                heapq.heappush(frontier,
                               (h, counter, neighbour, path + [neighbour]))

    elapsed = (time.perf_counter() - t0) * 1000
    return _fail_result(visited, expanded, elapsed, max_frontier)


def astar(maze, start, goal) -> dict:
    t0 = time.perf_counter()

    counter = 0
    h0 = manhattan(start, goal)
    g0 = 0
    f0 = g0 + h0
    frontier: list = []
    heapq.heappush(frontier, (f0, g0, counter, start, [start]))
    visited: set = set()
    expanded = 0
    max_frontier = 1

    while frontier:
        max_frontier = max(max_frontier, len(frontier))
        _f, g, _cnt, pos, path = heapq.heappop(frontier)

        if pos in visited:
            continue

        visited.add(pos)
        expanded += 1

        if pos == goal:
            elapsed = (time.perf_counter() - t0) * 1000
            return _success_result(path, visited, expanded,
                                   elapsed, max_frontier)

        for neighbour in maze.neighbors(*pos):
            if neighbour not in visited:
                counter += 1
                new_g = g + 1
                h = manhattan(neighbour, goal)
                f = new_g + h
                heapq.heappush(frontier,
                               (f, new_g, counter, neighbour,
                                path + [neighbour]))

    elapsed = (time.perf_counter() - t0) * 1000
    return _fail_result(visited, expanded, elapsed, max_frontier)

_ALGORITHMS = {
    'bfs':    bfs,
    'dfs':    dfs,
    'ucs':    ucs,
    'greedy': greedy,
    'astar':  astar,
}


def run_algorithm(name: str, maze, start, goal) -> dict:
    fn = _ALGORITHMS.get(name)
    if fn is None:
        raise ValueError(
            f"Unknown algorithm '{name}'. "
            f"Choose from {set(_ALGORITHMS.keys())}."
        )
    return fn(maze, start, goal)
