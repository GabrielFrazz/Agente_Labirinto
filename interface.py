import itertools
import os
import threading
import time
import tkinter as tk
from tkinter import filedialog, ttk, messagebox

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from ttkthemes import ThemedTk

from core.maze import Maze
from core.metrics import save_csv, plot_convergence, plot_comparison_bar
from search.classical import run_algorithm as run_classical
from search.local_search import (
    precompute_distances, hill_climbing, simulated_annealing,
    reconstruct_full_path,
)
from search.online_agent import OnlineAgent, compute_online_ratio


CELL_COLORS = {
    '#':  '#2c2c2a',
    ' ':  '#f5f4f0',
    'A':  '#E85D24',
    'B':  '#1D9E75',
    'C':  '#3B8BD4',
    '?':  '#888780',
    '*':  '#D14520',
    'PATH':     '#EF9F27',
    'EXPLORED': '#3E77B6',
}

ALG_MAP = {
    '— CLÁSSICAS —':  None,
    'BFS':            'bfs',
    'DFS':            'dfs',
    'UCS':            'ucs',
    'Gulosa':         'greedy',
    'A*':             'astar',
    '— LOCAIS —':     None,
    'Hill-Climbing':  'hc',
    'SA':             'sa',
    '— ONLINE —':     None,
    'Replanning com A*': 'online',
}

CLASSICAL_ALGS = {'bfs', 'dfs', 'ucs', 'greedy', 'astar'}
LOCAL_ALGS = {'hc', 'sa'}

def draw_maze_on_canvas(
    canvas: tk.Canvas,
    grid: list[list[str]],
    cell_size: int = 20,
    path: list[tuple[int, int]] | None = None,
    explored: set[tuple[int, int]] | None = None,
    highlight: list[tuple[int, int]] | None = None,
) -> None:
    canvas.delete('all')

    rows = len(grid)
    cols = max(len(row) for row in grid) if rows > 0 else 0

    path_set = set(path) if path else set()
    explored_set = explored if explored else set()

    canvas.config(scrollregion=(0, 0, cols * cell_size, rows * cell_size))

    c_counter = 0

    for r in range(rows):
        for c in range(len(grid[r])):
            ch = grid[r][c]
            x1 = c * cell_size
            y1 = r * cell_size
            x2 = x1 + cell_size
            y2 = y1 + cell_size

            color = CELL_COLORS.get(ch, '#f5f4f0')

            if (r, c) in explored_set and ch not in ('A', 'B', 'C', '*', '#'):
                color = CELL_COLORS['EXPLORED']

            if (r, c) in path_set and ch not in ('A', 'B', 'C', '*', '#'):
                color = CELL_COLORS['PATH']

            if ch in ('A', 'B', 'C', '*'):
                color = CELL_COLORS[ch]

            canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline='#d0d0d0', width=1)

            if ch in ('A', 'B', 'C', '*'):
                text_to_draw = ch
                if ch == 'C':
                    text_to_draw = f"C{c_counter}"
                    c_counter += 1
                    
                canvas.create_text(
                    (x1 + x2) // 2, (y1 + y2) // 2,
                    text=text_to_draw, fill='white',
                    font=('Consolas', max(7, int(cell_size * 0.4)), 'bold'),
                )

    if highlight:
        for (r, c) in highlight:
            x1 = c * cell_size
            y1 = r * cell_size
            x2 = x1 + cell_size
            y2 = y1 + cell_size
            canvas.create_rectangle(x1, y1, x2, y2, outline='red', width=3)


class MazeApp:
    def __init__(self, master: tk.Tk):
        self.master = master
        self.master.title('Agente em Labirinto – TP01 CSI457')
        self.master.geometry('1280x720')
        self.master.minsize(1024, 600)


        self.maze = None
        self._last_result = None
        self._last_alg_type = None
        self._online_agent = None
        self._animating = False
        self._results_history = []

        style = ttk.Style()
        style.configure('TButton', font=('Segoe UI', 10), padding=4)
        style.configure('Header.TLabel', font=('Segoe UI', 12, 'bold'))
        style.configure('Status.TLabel', font=('Segoe UI', 9))

        ctrl_frame = ttk.Frame(master, padding=6)
        ctrl_frame.pack(side=tk.TOP, fill=tk.X)

        ttk.Button(ctrl_frame, text='Carregar Labirinto', command=self.load_maze).pack(side=tk.LEFT, padx=4)
        ttk.Button(ctrl_frame, text='Executar', command=self.run_algorithm).pack(side=tk.LEFT, padx=4)
        ttk.Button(ctrl_frame, text='Limpar', command=self._clear).pack(side=tk.LEFT, padx=4)
        ttk.Button(ctrl_frame, text='Sair', command=self.master.destroy).pack(side=tk.LEFT, padx=4)


        ttk.Separator(ctrl_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)

        ttk.Label(ctrl_frame, text='Algoritmo:').pack(side=tk.LEFT, padx=(4, 2))
        self._alg_var = tk.StringVar(value='BFS')
        self._prev_alg = 'BFS'
        alg_combo = ttk.Combobox(
            ctrl_frame, textvariable=self._alg_var,
            values=list(ALG_MAP.keys()), state='readonly', width=20,
        )
        alg_combo.pack(side=tk.LEFT, padx=2)
        alg_combo.bind('<<ComboboxSelected>>', self._on_alg_selected)

        ttk.Separator(ctrl_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)

        ttk.Label(ctrl_frame, text='Vel. Animação (ms):').pack(side=tk.LEFT, padx=(4, 2))
        self._speed_var = tk.IntVar(value=10)
        speed_scale = ttk.Scale(
            ctrl_frame, from_=1, to=20, variable=self._speed_var,
            orient=tk.HORIZONTAL, length=120,
        )
        speed_scale.pack(side=tk.LEFT, padx=2)
        self._speed_label = ttk.Label(ctrl_frame, text='10', width=4)
        self._speed_label.pack(side=tk.LEFT)
        speed_scale.config(command=lambda v: self._speed_label.config(text=str(int(float(v)))))

        self._show_explored_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            ctrl_frame, text='Mostrar nós explorados',
            variable=self._show_explored_var,
            command=self._redraw_result,
        ).pack(side=tk.LEFT, padx=8)

        main_frame = ttk.Frame(master)
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=6, pady=(0, 4))

        canvas_frame = ttk.LabelFrame(main_frame, text='Labirinto', padding=4)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg='#e8e8e4', cursor='crosshair')

        h_scroll = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        v_scroll = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.config(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)

        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        info_frame = ttk.LabelFrame(main_frame, text='Métricas', padding=4, width=340)
        info_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(4, 0))
        info_frame.pack_propagate(False)

        self._metrics_tree = ttk.Treeview(
            info_frame, columns=('Métrica', 'Valor'), show='headings', height=14,
        )
        self._metrics_tree.heading('Métrica', text='Métrica')
        self._metrics_tree.heading('Valor', text='Valor')
        self._metrics_tree.column('Métrica', width=150, anchor=tk.W)
        self._metrics_tree.column('Valor', width=140, anchor=tk.E)
        self._metrics_tree.pack(fill=tk.BOTH, expand=True)

        ttk.Label(info_frame, text='Info do Labirinto:', style='Header.TLabel').pack(
            anchor=tk.W, pady=(8, 2))
        self._maze_info_var = tk.StringVar(value='Nenhum labirinto carregado.')
        ttk.Label(info_frame, textvariable=self._maze_info_var, wraplength=320,
                  justify=tk.LEFT).pack(anchor=tk.W)

        self._status_var = tk.StringVar(value='Pronto.')
        status_bar = ttk.Label(
            master, textvariable=self._status_var, style='Status.TLabel',
            relief=tk.SUNKEN, anchor=tk.W, padding=(6, 2),
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)


    def _on_alg_selected(self, _event=None) -> None:
        selected = self._alg_var.get()
        if ALG_MAP.get(selected) is None:
            self._alg_var.set(self._prev_alg)
        else:
            self._prev_alg = selected

    def load_maze(self) -> None:
        filepath = filedialog.askopenfilename(
            title='Selecione um labirinto',
            filetypes=[('Arquivo de texto', '*.txt'), ('Todos', '*.*')],
            initialdir=os.path.join(os.path.dirname(__file__), 'mazes'),
        )
        if not filepath:
            return
        try:
            self.maze = Maze(filepath)
        except ValueError as e:
            messagebox.showerror('Erro ao carregar labirinto', str(e))
            return

        self._last_result = None
        self._results_history.clear()
        self._status_var.set(f'Labirinto carregado: {os.path.basename(filepath)}')

        cell_size = self._compute_cell_size()
        draw_maze_on_canvas(self.canvas, self.maze.grid, cell_size)

        n_collect = len(self.maze.collect)
        self._maze_info_var.set(
            f'Arquivo: {os.path.basename(filepath)}\n'
            f'Dimensões: {self.maze.rows}×{self.maze.cols}\n'
            f'Início (A): {self.maze.start}\n'
            f'Objetivo (B): {self.maze.goal}\n'
            f'Pontos de coleta: {n_collect}'
        )
        self._clear_metrics()


    def run_algorithm(self) -> None:
        if self.maze is None:
            messagebox.showwarning('Aviso', 'Carregue um labirinto primeiro.')
            return
        if self._animating:
            messagebox.showwarning('Aviso', 'Uma animação já está em andamento.')
            return

        alg_key = ALG_MAP.get(self._alg_var.get())
        if alg_key is None:
            return

        self._status_var.set(f'Executando {self._alg_var.get()}…')
        self._clear_metrics()

        if alg_key in CLASSICAL_ALGS:
            threading.Thread(target=self._run_classical, args=(alg_key,), daemon=True).start()
        elif alg_key in LOCAL_ALGS:
            threading.Thread(target=self._run_local_search, args=(alg_key,), daemon=True).start()
        elif alg_key == 'online':
            self._run_online()

    def _run_classical(self, alg_name: str) -> None:
        try:
            result = run_classical(alg_name, self.maze, self.maze.start, self.maze.goal)
            self._last_result = result
            self._last_alg_type = 'classical'
            self.canvas.after(0, self._on_result_ready)
        except Exception as e:
            self.canvas.after(0, lambda: messagebox.showerror('Erro', str(e)))

    def _run_local_search(self, alg_name: str) -> None:
        if len(self.maze.collect) == 0:
            self.canvas.after(0, lambda: messagebox.showwarning(
                'Aviso', 'Este labirinto não possui pontos de coleta (C).\n'
                         'Use um labirinto com coletas para busca local.'))
            return

        try:
            dist, nodes = precompute_distances(self.maze)

            if alg_name == 'hc':
                result = hill_climbing(self.maze, dist, nodes)
            else:
                result = simulated_annealing(self.maze, dist, nodes)

            full_path = reconstruct_full_path(result['melhor_ordem'], nodes, self.maze)
            result['caminho'] = full_path
            result['_nos'] = nodes

            self._last_result = result
            self._last_alg_type = 'local'
            self.canvas.after(0, self._on_result_ready)

            self.canvas.after(0, lambda: self._show_convergence(result, alg_name))
        except Exception as e:
            self.canvas.after(0, lambda: messagebox.showerror('Erro', str(e)))

    def _run_online(self) -> None:
        self._online_agent = OnlineAgent(self.maze)
        self._animating = True
        self._online_start_time = time.perf_counter()
        self.animate_online_step()


    def animate_online_step(self) -> None:
        if not self._animating or self._online_agent is None:
            return

        agent = self._online_agent
        delay = self._speed_var.get()

        # O problema da lentidão é que draw_maze_on_canvas desenha milhares de retângulos
        # a cada passo. Para acelerar, vamos agrupar passos antes de redesenhar a tela
        # dependendo de quão rápido o usuário quer (menor delay = mais passos por frame).
        if delay <= 2:
            steps_per_frame = 15
        elif delay <= 5:
            steps_per_frame = 8
        elif delay <= 10:
            steps_per_frame = 4
        elif delay <= 15:
            steps_per_frame = 2
        else:
            steps_per_frame = 1

        status = 'continue'
        for _ in range(steps_per_frame):
            status = agent.step()
            if status != 'continue':
                break

        cell_size = self._compute_cell_size()
        snapshot = agent.get_snapshot()

        draw_maze_on_canvas(
            self.canvas, snapshot, cell_size,
            path=agent.path_taken,
        )

        if status == 'goal':
            self._animating = False
            elapsed = (time.perf_counter() - self._online_start_time) * 1000
            result = agent.run.__wrapped__(agent) if hasattr(agent.run, '__wrapped__') else {
                'sucesso': True,
                'movimentos_totais': agent.total_moves,
                'custo_real': agent.total_moves,
                'celulas_reveladas': len(agent.cells_revealed),
                'celulas_revisitadas': agent.cells_revisited,
                'replanejamentos': agent.replannings,
                'caminho_percorrido': agent.path_taken,
                'tempo_ms': elapsed,
                'otimo_offline': None,
                'razao_online': None,
            }
            result = compute_online_ratio(result, self.maze)
            self._last_result = result
            self._last_alg_type = 'online'
            self._on_result_ready()
        elif status == 'stuck':
            self._animating = False
            elapsed = (time.perf_counter() - self._online_start_time) * 1000
            self._last_result = {
                'sucesso': False,
                'movimentos_totais': agent.total_moves,
                'custo_real': agent.total_moves,
                'celulas_reveladas': len(agent.cells_revealed),
                'celulas_revisitadas': agent.cells_revisited,
                'replanejamentos': agent.replannings,
                'caminho_percorrido': agent.path_taken,
                'tempo_ms': elapsed,
                'otimo_offline': None,
                'razao_online': None,
            }
            self._last_alg_type = 'online'
            self._on_result_ready()
        else:
            delay = self._speed_var.get()
            self.canvas.after(delay, self.animate_online_step)


    def _on_result_ready(self) -> None:
        result = self._last_result
        if result is None:
            return

        self._clear_metrics()
        tree = self._metrics_tree

        if self._last_alg_type == 'classical':
            metrics = [
                ('Sucesso', '✓' if result['sucesso'] else '✗'),
                ('Custo do caminho', result['custo']),
                ('Passos', result['passos']),
                ('Nós explorados', result['explorados']),
                ('Nós expandidos', result['expandidos']),
                ('Tempo (ms)', f"{result['tempo_ms']:.2f}"),
                ('Fronteira máxima', result['fronteira_max']),
            ]
        elif self._last_alg_type == 'local':
            metrics = [
                ('Melhor custo', result['melhor_custo']),
                ('Pior custo', result['pior_custo']),
                ('Custo médio', f"{result['custo_medio']:.2f}"),
                ('Tempo (ms)', f"{result['tempo_ms']:.2f}"),
                ('Iterações', result.get('iteracoes', result.get('execucoes', '-'))),
            ]
        elif self._last_alg_type == 'online':
            metrics = [
                ('Sucesso', '✓' if result['sucesso'] else '✗'),
                ('Movimentos totais', result['movimentos_totais']),
                ('Custo real', result['custo_real']),
                ('Células reveladas', result['celulas_reveladas']),
                ('Células revisitadas', result['celulas_revisitadas']),
                ('Replanejamentos', result['replanejamentos']),
                ('Custo ótimo offline', result.get('otimo_offline', '-')),
                ('Razão online/offline',
                 f"{result['razao_online']:.2f}" if result.get('razao_online') else '-'),
            ]
        else:
            metrics = []

        for metric, value in metrics:
            tree.insert('', tk.END, values=(metric, value))

        row = {'algoritmo': self._alg_var.get()}
        row.update({k: v for k, v in result.items()
                    if k not in ('caminho', 'caminho_percorrido', 'caminho_offline', 'historico_custo', '_nos', '_conjunto_explorados')})
        self._results_history.append(row)

        maze_basename = os.path.basename(self.maze.filepath)
        maze_name = os.path.splitext(maze_basename)[0]
        csv_filename = f"metrics_{maze_name}_{self._last_alg_type}.csv"
        csv_path = os.path.join(os.path.dirname(__file__), 'results', maze_name, csv_filename)
        try:
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)
            save_csv([row], csv_path, append=True)
        except Exception as e:
            print(f"Erro ao salvar CSV automático: {e}")

        # Gerar gráficos de comparação para buscas clássicas
        if self._last_alg_type == 'classical':
            self._generate_classical_comparison_plots(csv_path, maze_name)

        success = result.get('sucesso', True)
        self._status_var.set(
            f"{self._alg_var.get()}: {'Concluído ✓' if success else 'Falhou ✗'}")

        path = result.get('caminho', [])
        if self._last_alg_type in ('classical', 'local') and path:
            self._animating = True
            self._animate_path(path, 0)
        elif self._last_alg_type == 'online':
            self._redraw_result()
            self._show_online_comparison(result)
        else:
            self._redraw_result()

    def _animate_path(self, path: list[tuple[int, int]], index: int) -> None:
        if not self._animating:
            self._redraw_result()
            return

        cell_size = self._compute_cell_size()

        if index == 0:
            highlight = None
            explored = None
            if self._last_alg_type == 'local' and self._last_result.get('_nos'):
                highlight = self._last_result['_nos'][1:-1]
            if self._show_explored_var.get() and self._last_alg_type == 'classical':
                explored = self._last_result.get('_conjunto_explorados')
            draw_maze_on_canvas(self.canvas, self.maze.grid, cell_size, path=[], explored=explored, highlight=highlight)

        if index > 0 and index <= len(path):
            r, c = path[index - 1]
            ch = self.maze.grid[r][c]
            # Só pinta se não for célula especial
            if ch not in ('A', 'B', 'C', '#'):
                x1 = c * cell_size
                y1 = r * cell_size
                x2 = x1 + cell_size
                y2 = y1 + cell_size
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=CELL_COLORS['PATH'], outline='#d0d0d0', width=1
                )

        if index < len(path):
            delay = self._speed_var.get()
            self.canvas.after(delay, lambda: self._animate_path(path, index + 1))
        else:
            self._animating = False

    def _redraw_result(self) -> None:
        if self.maze is None:
            return

        result = self._last_result
        cell_size = self._compute_cell_size()

        if result is None:
            draw_maze_on_canvas(self.canvas, self.maze.grid, cell_size)
            return

        path = result.get('caminho', result.get('caminho_percorrido', []))
        explored = None
        if self._show_explored_var.get() and self._last_alg_type == 'classical':
            explored = result.get('_conjunto_explorados')

        if self._last_alg_type == 'online':
            if self._online_agent:
                snapshot = self._online_agent.get_snapshot()
                draw_maze_on_canvas(self.canvas, snapshot, cell_size, path=path)
            else:
                draw_maze_on_canvas(self.canvas, self.maze.grid, cell_size, path=path)
        else:
            highlight = None
            if self._last_alg_type == 'local' and result.get('_nos'):
                highlight = result['_nos'][1:-1]  # pontos C
            draw_maze_on_canvas(
                self.canvas, self.maze.grid, cell_size,
                path=path, explored=explored, highlight=highlight,
            )

    def _show_convergence(self, result: dict, alg_name: str) -> None:

        if alg_name != 'sa':
            history = result.get('historico_custo', [])

            if not history:
                return

            iterations = list(range(1, len(history) + 1))

            max_points = 300
            if len(history) > max_points:
                step = len(history) / max_points
                iterations = [int(i * step) + 1 for i in range(max_points)]
                history = [history[int(i * step)] for i in range(max_points)]

            win = tk.Toplevel(self.master)
            win.title('Convergência — Hill-Climbing')
            win.geometry('700x500')

            fig, ax = plt.subplots(figsize=(7, 5))

            ax.plot(iterations, history, linewidth=2)

            ax.set_title('Convergência — Hill-Climbing')
            ax.set_xlabel('Iteração')
            ax.set_ylabel('Melhor custo')
            ax.grid(True, alpha=0.3)

            fig.tight_layout()

            maze_basename = os.path.basename(self.maze.filepath)
            maze_name = os.path.splitext(maze_basename)[0]
            plot_path = os.path.join(os.path.dirname(__file__), 'results', maze_name, 'plots', f"conv_{maze_name}_{alg_name}.png")
            try:
                os.makedirs(os.path.dirname(plot_path), exist_ok=True)
                fig.savefig(plot_path)
            except Exception as e:
                pass

            canvas_fig = FigureCanvasTkAgg(fig, master=win)
            canvas_fig.draw()
            canvas_fig.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            return

        current_history = result.get("historico_current", [])
        best_history = result.get("historico_best", [])
        temperature_history = result.get("historico_temperatura", [])

        if not current_history:
            return

        max_points = 500

        def downsample(data):
            if len(data) <= max_points:
                return data

            step = len(data) / max_points

            return [
                data[int(i * step)]
                for i in range(max_points)
            ]

        current_history = downsample(current_history)
        best_history = downsample(best_history)
        temperature_history = downsample(temperature_history)

        iterations = list(range(len(current_history)))

        win = tk.Toplevel(self.master)
        win.title("Simulated Annealing — Diagnóstico")
        win.geometry("900x900")

        fig, axes = plt.subplots(3, 1, figsize=(8, 9))

        axes[0].plot(
            iterations,
            current_history,
            linewidth=1.2
        )

        axes[0].set_title("Custo Atual (Exploração)")
        axes[0].set_ylabel("Custo")
        axes[0].grid(True, alpha=0.3)

        axes[1].plot(
            iterations,
            best_history,
            linewidth=2
        )

        axes[1].set_title("Melhor Custo Encontrado")
        axes[1].set_ylabel("Custo")
        axes[1].grid(True, alpha=0.3)

        axes[2].plot(
            iterations,
            temperature_history,
            linewidth=2
        )

        axes[2].set_title("Temperatura")
        axes[2].set_xlabel("Iteração")
        axes[2].set_ylabel("T")
        axes[2].grid(True, alpha=0.3)

        fig.tight_layout()

        # Restaurando o salvamento automático do gráfico
        maze_basename = os.path.basename(self.maze.filepath)
        maze_name = os.path.splitext(maze_basename)[0]
        plot_path = os.path.join(os.path.dirname(__file__), 'results', maze_name, 'plots', f"conv_{maze_name}_{alg_name}.png")
        try:
            os.makedirs(os.path.dirname(plot_path), exist_ok=True)
            fig.savefig(plot_path)
            print(f"Gráfico de diagnóstico salvo em: {plot_path}")
        except Exception as e:
            print(f"Erro ao salvar gráfico automático: {e}")

        canvas_fig = FigureCanvasTkAgg(fig, master=win)
        canvas_fig.draw()
        canvas_fig.get_tk_widget().pack(fill=tk.BOTH, expand=True)


    def _show_online_comparison(self, result: dict) -> None:
        online_path = result.get('caminho_percorrido', [])
        offline_path = result.get('caminho_offline', [])

        if not online_path and not offline_path:
            return

        win = tk.Toplevel(self.master)
        win.title('Comparação — Online vs Offline')
        win.geometry('1100x560')

        # --- Lado esquerdo: caminho online ---
        left_frame = ttk.LabelFrame(win, text='Caminho Online (Replanning com A*)', padding=4)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(6, 3), pady=6)

        online_cost = result.get('custo_real', len(online_path) - 1)
        ttk.Label(left_frame, text=f'Movimentos: {online_cost}',
                  font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(0, 4))

        left_canvas = tk.Canvas(left_frame, bg='#e8e8e4')
        left_h = ttk.Scrollbar(left_frame, orient=tk.HORIZONTAL, command=left_canvas.xview)
        left_v = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=left_canvas.yview)
        left_canvas.config(xscrollcommand=left_h.set, yscrollcommand=left_v.set)
        left_v.pack(side=tk.RIGHT, fill=tk.Y)
        left_h.pack(side=tk.BOTTOM, fill=tk.X)
        left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # --- Lado direito: caminho offline ótimo ---
        right_frame = ttk.LabelFrame(win, text='Caminho Ótimo Offline (A*)', padding=4)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(3, 6), pady=6)

        offline_cost = result.get('otimo_offline', len(offline_path) - 1 if offline_path else '-')
        ratio = result.get('razao_online')
        ratio_txt = f'  |  Razão: {ratio:.2f}x' if ratio else ''
        ttk.Label(right_frame, text=f'Passos: {offline_cost}{ratio_txt}',
                  font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(0, 4))

        right_canvas = tk.Canvas(right_frame, bg='#e8e8e4')
        right_h = ttk.Scrollbar(right_frame, orient=tk.HORIZONTAL, command=right_canvas.xview)
        right_v = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=right_canvas.yview)
        right_canvas.config(xscrollcommand=right_h.set, yscrollcommand=right_v.set)
        right_v.pack(side=tk.RIGHT, fill=tk.Y)
        right_h.pack(side=tk.BOTTOM, fill=tk.X)
        right_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Calcular cell_size com base no tamanho da janela
        cell_size = max(min(500 // max(self.maze.cols, 1),
                            480 // max(self.maze.rows, 1), 40), 8)

        draw_maze_on_canvas(left_canvas, self.maze.grid, cell_size, path=online_path)
        draw_maze_on_canvas(right_canvas, self.maze.grid, cell_size, path=offline_path)

    def _generate_classical_comparison_plots(self, csv_path: str, maze_name: str) -> None:
        """Lê o CSV acumulado de métricas clássicas deste labirinto e gera
        gráficos de barras comparando nós expandidos e tempo de execução.
        Usa apenas a última execução de cada algoritmo."""
        import csv as csv_mod

        try:
            with open(csv_path, newline='', encoding='utf-8') as fh:
                reader = csv_mod.DictReader(fh)
                rows = list(reader)
        except Exception:
            return

        if not rows:
            return

        # Manter apenas a última execução de cada algoritmo
        latest: dict[str, dict] = {}
        for r in rows:
            latest[r['algoritmo']] = r

        expanded_data: dict[str, int] = {}
        time_data: dict[str, float] = {}

        for alg, r in latest.items():
            success = r.get('sucesso', 'True')
            if str(success) not in ('True', 'true', '1'):
                continue
            try:
                expanded_data[alg] = int(r['expandidos'])
            except (KeyError, ValueError):
                pass
            try:
                time_data[alg] = float(r['tempo_ms'])
            except (KeyError, ValueError):
                pass

        plots_dir = os.path.join(os.path.dirname(__file__), 'results', maze_name, 'plots')
        os.makedirs(plots_dir, exist_ok=True)

        if expanded_data:
            plot_comparison_bar(
                expanded_data,
                title=f'Nós Expandidos — {maze_name}',
                ylabel='Nós expandidos',
                save_path=os.path.join(plots_dir, f'classical_expanded_{maze_name}.png'),
            )

        if time_data:
            plot_comparison_bar(
                time_data,
                title=f'Tempo de Execução — {maze_name}',
                ylabel='Tempo (ms)',
                save_path=os.path.join(plots_dir, f'classical_time_{maze_name}.png'),
            )


    def _compute_cell_size(self) -> int:
        if self.maze is None:
            return 20
        self.canvas.update_idletasks()
        cw = max(self.canvas.winfo_width(), 400)
        ch = max(self.canvas.winfo_height(), 300)
        size_w = cw // max(self.maze.cols, 1)
        size_h = ch // max(self.maze.rows, 1)
        return max(min(size_w, size_h, 40), 8)

    def _clear(self) -> None:
        self._animating = False
        self._last_result = None
        self._last_alg_type = None
        self._online_agent = None
        self._animating = False
        self._clear_metrics()
        if self.maze:
            cell_size = self._compute_cell_size()
            draw_maze_on_canvas(self.canvas, self.maze.grid, cell_size)
        else:
            self.canvas.delete('all')
        self._status_var.set('Pronto.')

    def _clear_metrics(self) -> None:
        for item in self._metrics_tree.get_children():
            self._metrics_tree.delete(item)


if __name__ == '__main__':
    root = ThemedTk(theme='arc')
    root.title('Agente em Labirinto – TP01 CSI457')
    root.geometry('1280x720')
    app = MazeApp(root)
    root.mainloop()
