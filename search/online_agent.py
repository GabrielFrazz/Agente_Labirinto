from __future__ import annotations

import time
import copy
from collections import deque

from core.maze import MazeView
from search.classical import astar, manhattan


class OnlineAgent:

    def __init__(self, real_maze):
        self.real_maze = real_maze
        self.view = MazeView(real_maze.rows, real_maze.cols, real_maze.start)
        self.pos = real_maze.start
        self.path_taken: list[tuple[int, int]] = [self.pos]
        self.total_moves: int = 0
        self.replannings: int = 0
        self.cells_revealed: set[tuple[int, int]] = set()
        self.cells_revisited: int = 0
        self.plan: list[tuple[int, int]] = []


    def perceive(self) -> None:
        r, c = self.pos
        for dr, dc in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.real_maze.rows and 0 <= nc < self.real_maze.cols:
                real_char = self.real_maze.grid[nr][nc]
                self.view.reveal(nr, nc, real_char)
                self.cells_revealed.add((nr, nc))

    def replan(self) -> bool:
        self.replannings += 1

        if self.view.goal is not None:
            result = astar(self.view, self.pos, self.view.goal)
            if result["success"]:
                # result['path'] includes start; strip it
                self.plan = result["path"][1:]
                return True
            return False

        target = self._find_exploration_target()
        if target is None:
            return False

        result = astar(self.view, self.pos, target)
        if result["success"]:
            self.plan = result["path"][1:]
            return True
        return False

    def _find_exploration_target(self) -> tuple[int, int] | None:
        visited: set[tuple[int, int]] = {self.pos}
        queue: deque[tuple[int, int]] = deque([self.pos])

        while queue:
            r, c = queue.popleft()

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.view.rows and 0 <= nc < self.view.cols:
                    if self.view.grid[nr][nc] == "?":
                        return (r, c)

            for neighbor in self.view.neighbors(r, c):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return None

    def step(self) -> str:
        self.perceive()

        need_replan = False
        if not self.plan:
            need_replan = True
        else:
            next_pos = self.plan[0]
            nr, nc = next_pos
            if not self.view.is_free(nr, nc):
                need_replan = True

        if need_replan:
            if not self.replan():
                return "stuck"

        if not self.plan:
            return "stuck"

        next_pos = self.plan.pop(0)
        self.pos = next_pos

        self.total_moves += 1
        if self.pos in self.path_taken:
            self.cells_revisited += 1
        self.path_taken.append(self.pos)

        if self.view.goal is not None and self.pos == self.view.goal:
            return "goal"

        return "continue"

    def run(self, max_steps: int = 10000) -> dict:
        t0 = time.perf_counter()
        success = False

        for _ in range(max_steps):
            status = self.step()
            if status == "goal":
                success = True
                break
            if status == "stuck":
                break

        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        return {
            "success": success,
            "total_moves": self.total_moves,
            "cost_real": self.total_moves,
            "cells_revealed": len(self.cells_revealed),
            "cells_revisited": self.cells_revisited,
            "replannings": self.replannings,
            "path_taken": list(self.path_taken),
            "time_ms": elapsed_ms,
            "offline_optimal": None,
            "online_ratio": None,
        }

    def get_snapshot(self) -> list[list[str]]:
        grid_copy = copy.deepcopy(self.view.grid)
        r, c = self.pos
        grid_copy[r][c] = "*"
        return grid_copy


def compute_online_ratio(online_result: dict, real_maze) -> dict:
    offline = astar(real_maze, real_maze.start, real_maze.goal)

    if offline["success"]:
        offline_optimal = offline["cost"]
        cost_real = online_result["cost_real"]
        online_result["offline_optimal"] = offline_optimal
        if offline_optimal > 0:
            online_result["online_ratio"] = cost_real / offline_optimal
        else:
            online_result["online_ratio"] = 1.0 if cost_real == 0 else None
    else:
        online_result["offline_optimal"] = None
        online_result["online_ratio"] = None

    return online_result
