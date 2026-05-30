import random
import time
import math

from search.classical import astar


def precompute_distances(maze) -> tuple[dict, list]:
    nodes = [maze.start] + maze.collect + [maze.goal]
    dist = {}

    for n in nodes:
        dist[(n, n)] = 0

    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            result = astar(maze, nodes[i], nodes[j])
            if result["success"]:
                cost = result["cost"]
            else:
                cost = float("inf")
            dist[(nodes[i], nodes[j])] = cost
            dist[(nodes[j], nodes[i])] = cost

    return dist, nodes


def solution_cost(order: list[int], dist: dict, nodes: list) -> float:
    start = nodes[0]
    goal = nodes[-1]
    total = 0.0

    first = nodes[order[0] + 1]
    total += dist[(start, first)]
    if total == float("inf"):
        return float("inf")

    for idx in range(len(order) - 1):
        a = nodes[order[idx] + 1]
        b = nodes[order[idx + 1] + 1]
        seg = dist[(a, b)]
        if seg == float("inf"):
            return float("inf")
        total += seg

    last = nodes[order[-1] + 1]
    total += dist[(last, goal)]
    if total == float("inf"):
        return float("inf")

    return total


def get_neighbors(order: list[int]) -> list[list[int]]:
    neighbors = []
    k = len(order)
    for i in range(k):
        for j in range(i + 1, k):
            neighbor = order[:]
            neighbor[i], neighbor[j] = neighbor[j], neighbor[i]
            neighbors.append(neighbor)
    return neighbors


def hill_climbing(maze, dist, nodes, restarts=30) -> dict:
    t0 = time.perf_counter()

    k = len(nodes) - 2
    global_best_order = None
    global_best_cost = float("inf")
    worst_cost = float("-inf")
    cost_sum = 0.0
    total_iterations = 0
    cost_history = []

    for _restart in range(restarts):
        current_order = list(range(k))
        random.shuffle(current_order)
        current_cost = solution_cost(current_order, dist, nodes)

        while True:
            total_iterations += 1

            if current_cost < global_best_cost:
                global_best_cost = current_cost
                global_best_order = current_order[:]

            cost_history.append(global_best_cost)

            neighbors = get_neighbors(current_order)
            best_neighbor = None
            best_neighbor_cost = current_cost

            for neighbor in neighbors:
                nc = solution_cost(neighbor, dist, nodes)
                if nc < best_neighbor_cost:
                    best_neighbor_cost = nc
                    best_neighbor = neighbor

            if best_neighbor is None:
                break

            current_order = best_neighbor
            current_cost = best_neighbor_cost

        restart_best = current_cost
        if restart_best > worst_cost:
            worst_cost = restart_best
        cost_sum += restart_best

    t1 = time.perf_counter()

    return {
        "best_order": global_best_order,
        "best_cost": global_best_cost,
        "worst_cost": worst_cost,
        "mean_cost": cost_sum / restarts,
        "restarts_done": restarts,
        "iterations": total_iterations,
        "time_ms": (t1 - t0) * 1000.0,
        "cost_history": cost_history,
    }


def simulated_annealing(
    maze, dist, nodes, T0=1000.0, alpha=0.995, max_iter=10000, runs=5
) -> dict:
    t0 = time.perf_counter()

    k = len(nodes) - 2
    global_best_order = None
    global_best_cost = float("inf")
    worst_cost = float("-inf")
    cost_sum = 0.0
    last_run_history = []

    for _run in range(runs):
        # Random initial solution
        current_order = list(range(k))
        random.shuffle(current_order)
        current_cost = solution_cost(current_order, dist, nodes)

        run_best_order = current_order[:]
        run_best_cost = current_cost
        T = T0
        run_history = []

        for _it in range(max_iter):
            i = random.randint(0, k - 1)
            j = random.randint(0, k - 1)
            while j == i:
                j = random.randint(0, k - 1)

            neighbor = current_order[:]
            neighbor[i], neighbor[j] = neighbor[j], neighbor[i]
            neighbor_cost = solution_cost(neighbor, dist, nodes)

            delta = neighbor_cost - current_cost

            if delta < 0:
                current_order = neighbor
                current_cost = neighbor_cost
            else:
                if T > 0:
                    prob = math.exp(-delta / T)
                else:
                    prob = 0.0
                if random.random() < prob:
                    current_order = neighbor
                    current_cost = neighbor_cost

            if current_cost < run_best_cost:
                run_best_cost = current_cost
                run_best_order = current_order[:]

            T *= alpha

            run_history.append(run_best_cost)

        if run_best_cost < global_best_cost:
            global_best_cost = run_best_cost
            global_best_order = run_best_order[:]

        if run_best_cost > worst_cost:
            worst_cost = run_best_cost

        cost_sum += run_best_cost
        last_run_history = run_history

    t1 = time.perf_counter()

    return {
        "best_order": global_best_order,
        "best_cost": global_best_cost,
        "worst_cost": worst_cost,
        "mean_cost": cost_sum / runs,
        "runs_done": runs,
        "time_ms": (t1 - t0) * 1000.0,
        "cost_history": last_run_history,
        "T0": T0,
        "alpha": alpha,
        "max_iter": max_iter,
    }


def reconstruct_full_path(
    order: list[int], nodes: list, maze
) -> list[tuple[int, int]]:
    start = nodes[0]
    goal = nodes[-1]

    waypoints = [start]
    for idx in order:
        waypoints.append(nodes[idx + 1])
    waypoints.append(goal)

    full_path = []

    for i in range(len(waypoints) - 1):
        result = astar(maze, waypoints[i], waypoints[i + 1])
        if not result["success"]:
            return []

        segment = result["path"]
        if full_path:
            segment = segment[1:]
        full_path.extend(segment)

    return full_path
