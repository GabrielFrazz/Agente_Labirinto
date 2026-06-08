import random

def generate_maze_string(width: int, height: int, num_collects: int = 0) -> str:
    if width % 2 == 0: width += 1
    if height % 2 == 0: height += 1

    grid = [['#' for _ in range(width)] for _ in range(height)]

    start_r, start_c = 1, 1
    grid[start_r][start_c] = ' '
    
    stack = [(start_r, start_c)]
    
    while stack:
        r, c = stack[-1]

        neighbors = []
        for dr, dc in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            nr, nc = r + dr, c + dc
            if 0 < nr < height - 1 and 0 < nc < width - 1 and grid[nr][nc] == '#':
                neighbors.append((nr, nc, dr, dc))
                
        if neighbors:
            nr, nc, dr, dc = random.choice(neighbors)
            grid[r + dr//2][c + dc//2] = ' '
            grid[nr][nc] = ' '
            stack.append((nr, nc))
        else:
            stack.pop()

    free_cells = [(r, c) for r in range(1, height-1) for c in range(1, width-1) if grid[r][c] == ' ']
    random.shuffle(free_cells)
    
    if len(free_cells) < 2 + num_collects:
        raise ValueError("Labirinto muito pequeno para tantos pontos de coleta.")

    start_pos = free_cells.pop()
    goal_pos = free_cells.pop()
    
    grid[start_pos[0]][start_pos[1]] = 'A'
    grid[goal_pos[0]][goal_pos[1]] = 'B'

    for _ in range(num_collects):
        c_pos = free_cells.pop()
        grid[c_pos[0]][c_pos[1]] = 'C'

    return '\n'.join(''.join(row) for row in grid)
