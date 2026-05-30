"""
Uso:
    python main.py                        # abre a GUI
    python main.py --batch maze_simple.txt  # roda todos algoritmos e salva CSV
    python main.py --help
"""

import argparse
import io
import os
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))



def run_batch(maze_path: str) -> None:
    import matplotlib
    matplotlib.use('Agg')  #  backend não-interativo para batch

    from core.maze import Maze
    from core.metrics import save_csv, plot_convergence, plot_comparison_bar
    from search.classical import run_algorithm
    from search.local_search import (
        precompute_distances, hill_climbing, simulated_annealing,
    )
    from search.online_agent import OnlineAgent, compute_online_ratio

    os.makedirs('results/plots', exist_ok=True)

    print(f'Carregando labirinto: {maze_path}')
    maze = Maze(maze_path)
    print(f'  Dimensões: {maze.rows}×{maze.cols}')
    print(f'  Início: {maze.start}  Objetivo: {maze.goal}')
    print(f'  Pontos de coleta: {len(maze.collect)}')
    print()

    print('=' * 60)
    print('ALGORITMOS CLASSICOS (A -> B)')
    print('=' * 60)

    classical_names = ['bfs', 'dfs', 'ucs', 'greedy', 'astar']
    display_names = {'bfs': 'BFS', 'dfs': 'DFS', 'ucs': 'UCS',
                     'greedy': 'Greedy', 'astar': 'AStar'}
    classical_results = []

    for alg in classical_names:
        result = run_algorithm(alg, maze, maze.start, maze.goal)
        row = {
            'algorithm': display_names[alg],
            'success': result['success'],
            'cost': result['cost'],
            'steps': result['steps'],
            'explored': result['explored'],
            'expanded': result['expanded'],
            'time_ms': round(result['time_ms'], 3),
            'max_frontier': result['max_frontier'],
        }
        classical_results.append(row)
        status = '✓' if result['success'] else '✗'
        print(f"  {display_names[alg]:>8s}: {status}  custo={result['cost']:>4d}  "
              f"expandidos={result['expanded']:>5d}  tempo={result['time_ms']:.2f}ms")

    save_csv(classical_results, 'results/classical_results.csv')
    print('\n  -> Salvo em results/classical_results.csv')

    expanded_data = {r['algorithm']: r['expanded'] for r in classical_results if r['success']}
    time_data = {r['algorithm']: r['time_ms'] for r in classical_results if r['success']}

    if expanded_data:
        plot_comparison_bar(
            expanded_data,
            title='Nós Expandidos por Algoritmo',
            ylabel='Nós expandidos',
            save_path='results/plots/classical_expanded.png',
        )
        print('  -> Gráfico: results/plots/classical_expanded.png')

    if time_data:
        plot_comparison_bar(
            time_data,
            title='Tempo de Execução por Algoritmo',
            ylabel='Tempo (ms)',
            save_path='results/plots/classical_time.png',
        )
        print('  -> Gráfico: results/plots/classical_time.png')

    if len(maze.collect) > 0:
        print()
        print('=' * 60)
        print('BUSCA LOCAL (A -> C1...Ck -> B)')
        print('=' * 60)

        dist, nodes = precompute_distances(maze)
        print(f'  Distâncias pré-computadas: {len(dist)} pares')

        hc_result = hill_climbing(maze, dist, nodes)
        sa_result = simulated_annealing(maze, dist, nodes)

        print(f"\n  Hill-Climbing:")
        print(f"    Melhor custo: {hc_result['best_cost']}")
        print(f"    Pior custo:   {hc_result['worst_cost']}")
        print(f"    Custo médio:  {hc_result['mean_cost']:.2f}")
        print(f"    Iterações:    {hc_result['iterations']}")
        print(f"    Tempo:        {hc_result['time_ms']:.2f}ms")

        print(f"\n  Simulated Annealing:")
        print(f"    Melhor custo: {sa_result['best_cost']}")
        print(f"    Pior custo:   {sa_result['worst_cost']}")
        print(f"    Custo médio:  {sa_result['mean_cost']:.2f}")
        print(f"    Runs:         {sa_result['runs_done']}")
        print(f"    Tempo:        {sa_result['time_ms']:.2f}ms")

        local_rows = [
            {
                'algorithm': 'HillClimbing',
                'best_cost': hc_result['best_cost'],
                'worst_cost': hc_result['worst_cost'],
                'mean_cost': round(hc_result['mean_cost'], 2),
                'time_ms': round(hc_result['time_ms'], 3),
                'iterations': hc_result['iterations'],
                'T0': '-',
                'alpha': '-',
            },
            {
                'algorithm': 'SA',
                'best_cost': sa_result['best_cost'],
                'worst_cost': sa_result['worst_cost'],
                'mean_cost': round(sa_result['mean_cost'], 2),
                'time_ms': round(sa_result['time_ms'], 3),
                'iterations': sa_result.get('max_iter', '-'),
                'T0': sa_result['T0'],
                'alpha': sa_result['alpha'],
            },
        ]
        save_csv(local_rows, 'results/local_search_results.csv')
        print('\n  -> Salvo em results/local_search_results.csv')

        if hc_result.get('cost_history'):
            plot_convergence(
                {'Hill-Climbing': hc_result['cost_history']},
                title='Convergência — Hill-Climbing',
                save_path='results/plots/convergence_hc.png',
            )
            print('  -> Gráfico: results/plots/convergence_hc.png')

        if sa_result.get('cost_history'):
            plot_convergence(
                {'Simulated Annealing': sa_result['cost_history']},
                title='Convergência — Simulated Annealing',
                save_path='results/plots/convergence_sa.png',
            )
            print('  -> Gráfico: results/plots/convergence_sa.png')

    print()
    print('=' * 60)
    print('BUSCA ONLINE (A -> B, mapa desconhecido)')
    print('=' * 60)

    agent = OnlineAgent(maze)
    online_result = agent.run()
    online_result = compute_online_ratio(online_result, maze)

    status = '✓' if online_result['success'] else '✗'
    print(f"  Sucesso:             {status}")
    print(f"  Movimentos totais:   {online_result['total_moves']}")
    print(f"  Custo real:          {online_result['cost_real']}")
    print(f"  Células reveladas:   {online_result['cells_revealed']}")
    print(f"  Células revisitadas: {online_result['cells_revisited']}")
    print(f"  Replanejamentos:     {online_result['replannings']}")
    print(f"  Custo ótimo offline: {online_result['offline_optimal']}")
    print(f"  Razao online/offline: "
          f"{online_result['online_ratio']:.2f}" if online_result['online_ratio'] else "  -")
    print(f"  Tempo:               {online_result['time_ms']:.2f}ms")

    maze_name = os.path.basename(maze_path)
    online_rows = [{
        'maze': maze_name,
        'success': online_result['success'],
        'total_moves': online_result['total_moves'],
        'cells_revealed': online_result['cells_revealed'],
        'cells_revisited': online_result['cells_revisited'],
        'replannings': online_result['replannings'],
        'offline_optimal': online_result['offline_optimal'],
        'online_ratio': round(online_result['online_ratio'], 3) if online_result['online_ratio'] else '-',
        'time_ms': round(online_result['time_ms'], 3),
    }]
    save_csv(online_rows, 'results/online_results.csv')
    print('\n  -> Salvo em results/online_results.csv')

    print()
    print('=' * 60)
    print('EXPERIMENTOS CONCLUIDOS')
    print('=' * 60)


def run_gui() -> None:
    from ttkthemes import ThemedTk
    from interface import MazeApp

    root = ThemedTk(theme='arc')
    root.title('Agente em Labirinto – TP01 CSI457')
    root.geometry('1280x720')
    app = MazeApp(root)
    root.mainloop()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='TP01 – Agente em Labirinto')
    parser.add_argument('--batch', metavar='MAZE', help='Executa experimentos em modo batch')
    args = parser.parse_args()

    if args.batch:
        run_batch(args.batch)
    else:
        run_gui()
