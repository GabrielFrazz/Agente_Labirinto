from __future__ import annotations

from collections import deque

_VALID_CHARS = frozenset({"#", " ", "A", "B", "C"})


class Maze:

    def __init__(self, filepath: str):
        self.filepath = filepath
        with open(filepath, "r", encoding="utf-8") as f:
            raw_lines = f.readlines()

        lines = [line.rstrip("\n\r") for line in raw_lines]

        while lines and lines[-1] == "":
            lines.pop()

        if not lines:
            raise ValueError("Arquivo de labirinto está vazio.")

        max_width = max(len(line) for line in lines)
        grid: list[list[str]] = []
        for line in lines:
            row = list(line.ljust(max_width))
            grid.append(row)

        self.grid = grid
        self.rows = len(grid)
        self.cols = max_width

        starts: list[tuple[int, int]] = []
        goals: list[tuple[int, int]] = []
        collects: list[tuple[int, int]] = []

        for r in range(self.rows):
            for c in range(self.cols):
                ch = self.grid[r][c]
                if ch not in _VALID_CHARS:
                    raise ValueError(
                        f"Caractere inválido '{ch}' encontrado na posição ({r}, {c})."
                    )
                if ch == "A":
                    starts.append((r, c))
                elif ch == "B":
                    goals.append((r, c))
                elif ch == "C":
                    collects.append((r, c))

        if len(starts) != 1:
            raise ValueError(
                f"O labirinto deve conter exatamente um 'A' (início). Encontrados: {len(starts)}."
            )
        if len(goals) != 1:
            raise ValueError(
                f"O labirinto deve conter exatamente um 'B' (objetivo). Encontrados: {len(goals)}."
            )

        self.start: tuple[int, int] = starts[0]
        self.goal: tuple[int, int] = goals[0]
        self.collect: list[tuple[int, int]] = collects  # ordem de leitura

        if not self._bfs_connected(self.start, self.goal):
            raise ValueError(
                "Não existe caminho entre 'A' e 'B' no labirinto."
            )

    def is_free(self, r: int, c: int) -> bool:
        if r < 0 or r >= self.rows or c < 0 or c >= self.cols:
            return False
        return self.grid[r][c] != "#"

    def neighbors(self, r: int, c: int) -> list[tuple[int, int]]:
        result: list[tuple[int, int]] = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if self.is_free(nr, nc):
                result.append((nr, nc))
        return result

    def cell(self, r: int, c: int) -> str:
        return self.grid[r][c]

    def __str__(self) -> str:
        return "\n".join("".join(row) for row in self.grid)

    def _bfs_connected(self, src: tuple[int, int], dst: tuple[int, int]) -> bool:
        visited: set[tuple[int, int]] = {src}
        queue: deque[tuple[int, int]] = deque([src])
        while queue:
            r, c = queue.popleft()
            if (r, c) == dst:
                return True
            for nr, nc in self.neighbors(r, c):
                if (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
        return False


class MazeView:
    def __init__(self, rows: int, cols: int, start: tuple[int, int]):
        self.rows = rows
        self.cols = cols
        self.grid: list[list[str]] = [["?" for _ in range(cols)] for _ in range(rows)]
        self.start: tuple[int, int] = start
        self.goal: tuple[int, int] | None = None
        self.collect: list[tuple[int, int]] = []

        self.grid[start[0]][start[1]] = "A"

    def reveal(self, r: int, c: int, char: str) -> None:
        self.grid[r][c] = char
        if char == "B":
            self.goal = (r, c)
        elif char == "C":
            if (r, c) not in self.collect:
                self.collect.append((r, c))

    def is_free(self, r: int, c: int) -> bool:
        if r < 0 or r >= self.rows or c < 0 or c >= self.cols:
            return False
        return self.grid[r][c] != "#"

    def neighbors(self, r: int, c: int) -> list[tuple[int, int]]:
        result: list[tuple[int, int]] = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if self.is_free(nr, nc):
                result.append((nr, nc))
        return result
