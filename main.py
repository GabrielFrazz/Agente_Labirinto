import argparse
import io
import os
import sys

if sys.stdout is not None and getattr(sys.stdout, 'encoding', None) and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))



def run_batch(maze_path: str) -> None:
    import matplotlib
    matplotlib.use('Agg')

    from core.maze import Maze
    from core.metrics import save_csv, plot_convergence, plot_comparison_bar
    from search.classical import run_algorithm
    from search.local_search import (
        precompute_distances, hill_climbing, simulated_annealing,
    )
    from search.online_agent import OnlineAgent, compute_online_ratio

    maze_name = os.path.splitext(os.path.basename(maze_path))[0]
    os.makedirs(f'results/{maze_name}/plots', exist_ok=True)

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
            'algoritmo': display_names[alg],
            'sucesso': result['sucesso'],
            'custo': result['custo'],
            'passos': result['passos'],
            'explorados': result['explorados'],
            'expandidos': result['expandidos'],
            'tempo_ms': round(result['tempo_ms'], 3),
            'fronteira_max': result['fronteira_max'],
        }
        classical_results.append(row)
        status = '✓' if result['sucesso'] else '✗'
        print(f"  {display_names[alg]:>8s}: {status}  custo={result['custo']:>4d}  "
              f"expandidos={result['expandidos']:>5d}  tempo={result['tempo_ms']:.2f}ms")

    save_csv(classical_results, f'results/{maze_name}/classical_results_{maze_name}.csv')
    print(f'\n  -> Salvo em results/{maze_name}/classical_results_{maze_name}.csv')

    expanded_data = {r['algoritmo']: r['expandidos'] for r in classical_results if r['sucesso']}
    time_data = {r['algoritmo']: r['tempo_ms'] for r in classical_results if r['sucesso']}

    if expanded_data:
        plot_comparison_bar(
            expanded_data,
            title='Nós Expandidos por Algoritmo',
            ylabel='Nós expandidos',
            save_path=f'results/{maze_name}/plots/classical_expanded_{maze_name}.png',
        )
        print(f'  -> Gráfico: results/{maze_name}/plots/classical_expanded_{maze_name}.png')

    if time_data:
        plot_comparison_bar(
            time_data,
            title='Tempo de Execução por Algoritmo',
            ylabel='Tempo (ms)',
            save_path=f'results/{maze_name}/plots/classical_time_{maze_name}.png',
        )
        print(f'  -> Gráfico: results/{maze_name}/plots/classical_time_{maze_name}.png')

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
        print(f"    Melhor custo: {hc_result['melhor_custo']}")
        print(f"    Pior custo:   {hc_result['pior_custo']}")
        print(f"    Custo médio:  {hc_result['custo_medio']:.2f}")
        print(f"    Iterações:    {hc_result['iteracoes']}")
        print(f"    Tempo:        {hc_result['tempo_ms']:.2f}ms")

        print(f"\n  Simulated Annealing:")
        print(f"    Melhor custo: {sa_result['melhor_custo']}")
        print(f"    Pior custo:   {sa_result['pior_custo']}")
        print(f"    Custo médio:  {sa_result['custo_medio']:.2f}")
        print(f"    Execuções:    {sa_result['execucoes']}")
        print(f"    Tempo:        {sa_result['tempo_ms']:.2f}ms")

        local_rows = [
            {
                'algoritmo': 'HillClimbing',
                'melhor_custo': hc_result['melhor_custo'],
                'pior_custo': hc_result['pior_custo'],
                'custo_medio': round(hc_result['custo_medio'], 2),
                'tempo_ms': round(hc_result['tempo_ms'], 3),
                'iteracoes': hc_result['iteracoes'],
                'T0': '-',
                'alfa': '-',
            },
            {
                'algoritmo': 'SA',
                'melhor_custo': sa_result['melhor_custo'],
                'pior_custo': sa_result['pior_custo'],
                'custo_medio': round(sa_result['custo_medio'], 2),
                'tempo_ms': round(sa_result['tempo_ms'], 3),
                'iteracoes': sa_result.get('max_iter', '-'),
                'T0': sa_result['T0'],
                'alfa': sa_result['alfa'],
            },
        ]
        save_csv(local_rows, f'results/{maze_name}/local_search_results_{maze_name}.csv')
        print(f'\n  -> Salvo em results/{maze_name}/local_search_results_{maze_name}.csv')

        if hc_result.get('historico_custo'):
            plot_convergence(
                {'Hill-Climbing': hc_result['historico_custo']},
                title='Convergência — Hill-Climbing',
                save_path=f'results/{maze_name}/plots/convergence_hc_{maze_name}.png',
            )
            print(f'  -> Gráfico: results/{maze_name}/plots/convergence_hc_{maze_name}.png')

        if sa_result.get('historico_best'):
            plot_convergence(
                {
                    'Melhor custo': sa_result['historico_best'],
                    'Custo atual': sa_result['historico_current'],
                },
                title='Convergência — Simulated Annealing',
                save_path=f'results/{maze_name}/plots/convergence_sa_{maze_name}.png',
            )
            print(f'  -> Gráfico: results/{maze_name}/plots/convergence_sa_{maze_name}.png')

    print()
    print('=' * 60)
    print('BUSCA ONLINE (A -> B, mapa desconhecido)')
    print('=' * 60)

    agent = OnlineAgent(maze)
    online_result = agent.run()
    online_result = compute_online_ratio(online_result, maze)

    status = '✓' if online_result['sucesso'] else '✗'
    print(f"  Sucesso:             {status}")
    print(f"  Movimentos totais:   {online_result['movimentos_totais']}")
    print(f"  Custo real:          {online_result['custo_real']}")
    print(f"  Células reveladas:   {online_result['celulas_reveladas']}")
    print(f"  Células revisitadas: {online_result['celulas_revisitadas']}")
    print(f"  Replanejamentos:     {online_result['replanejamentos']}")
    print(f"  Custo ótimo offline: {online_result['otimo_offline']}")
    print(f"  Razao online/offline: "
          f"{online_result['razao_online']:.2f}" if online_result['razao_online'] else "  -")
    print(f"  Tempo:               {online_result['tempo_ms']:.2f}ms")

    maze_name = os.path.basename(maze_path)
    online_rows = [{
        'labirinto': maze_name,
        'sucesso': online_result['sucesso'],
        'movimentos_totais': online_result['movimentos_totais'],
        'celulas_reveladas': online_result['celulas_reveladas'],
        'celulas_revisitadas': online_result['celulas_revisitadas'],
        'replanejamentos': online_result['replanejamentos'],
        'otimo_offline': online_result['otimo_offline'],
        'razao_online': round(online_result['razao_online'], 3) if online_result['razao_online'] else '-',
        'tempo_ms': round(online_result['tempo_ms'], 3),
    }]
    save_csv(online_rows, f'results/{maze_name}/online_results_{maze_name}.csv')
    print(f'\n  -> Salvo em results/{maze_name}/online_results_{maze_name}.csv')

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
