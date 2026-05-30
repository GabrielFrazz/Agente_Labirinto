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
    'EXPLORED': '#FAEEDA',
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
    'Online':         'online',
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
                canvas.create_text(
                    (x1 + x2) // 2, (y1 + y2) // 2,
                    text=ch, fill='white',
                    font=('Consolas', max(8, cell_size // 2), 'bold'),
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
        ttk.Button(ctrl_frame, text='Exportar CSV', command=self.export_csv).pack(side=tk.LEFT, padx=4)
        ttk.Button(ctrl_frame, text='Sair', command=self.master.destroy).pack(side=tk.LEFT, padx=4)


        ttk.Separator(ctrl_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)

        ttk.Label(ctrl_frame, text='Algoritmo:').pack(side=tk.LEFT, padx=(4, 2))
        self._alg_var = tk.StringVar(value='BFS')
        alg_combo = ttk.Combobox(
            ctrl_frame, textvariable=self._alg_var,
            values=list(ALG_MAP.keys()), state='readonly', width=16,
        )
        alg_combo.pack(side=tk.LEFT, padx=2)

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

            full_path = reconstruct_full_path(result['best_order'], nodes, self.maze)
            result['path'] = full_path
            result['_nodes'] = nodes

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
        status = agent.step()
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
                'success': True,
                'total_moves': agent.total_moves,
                'cost_real': agent.total_moves,
                'cells_revealed': len(agent.cells_revealed),
                'cells_revisited': agent.cells_revisited,
                'replannings': agent.replannings,
                'path_taken': agent.path_taken,
                'time_ms': elapsed,
                'offline_optimal': None,
                'online_ratio': None,
            }
            result = compute_online_ratio(result, self.maze)
            self._last_result = result
            self._last_alg_type = 'online'
            self._on_result_ready()
        elif status == 'stuck':
            self._animating = False
            elapsed = (time.perf_counter() - self._online_start_time) * 1000
            self._last_result = {
                'success': False,
                'total_moves': agent.total_moves,
                'cost_real': agent.total_moves,
                'cells_revealed': len(agent.cells_revealed),
                'cells_revisited': agent.cells_revisited,
                'replannings': agent.replannings,
                'path_taken': agent.path_taken,
                'time_ms': elapsed,
                'offline_optimal': None,
                'online_ratio': None,
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
                ('Sucesso', '✓' if result['success'] else '✗'),
                ('Custo do caminho', result['cost']),
                ('Passos', result['steps']),
                ('Nós explorados', result['explored']),
                ('Nós expandidos', result['expanded']),
                ('Tempo (ms)', f"{result['time_ms']:.2f}"),
                ('Fronteira máxima', result['max_frontier']),
            ]
        elif self._last_alg_type == 'local':
            metrics = [
                ('Melhor custo', result['best_cost']),
                ('Pior custo', result['worst_cost']),
                ('Custo médio', f"{result['mean_cost']:.2f}"),
                ('Tempo (ms)', f"{result['time_ms']:.2f}"),
                ('Iterações', result.get('iterations', result.get('runs_done', '-'))),
            ]
        elif self._last_alg_type == 'online':
            metrics = [
                ('Sucesso', '✓' if result['success'] else '✗'),
                ('Movimentos totais', result['total_moves']),
                ('Custo real', result['cost_real']),
                ('Células reveladas', result['cells_revealed']),
                ('Células revisitadas', result['cells_revisited']),
                ('Replanejamentos', result['replannings']),
                ('Custo ótimo offline', result.get('offline_optimal', '-')),
                ('Razão online/offline',
                 f"{result['online_ratio']:.2f}" if result.get('online_ratio') else '-'),
            ]
        else:
            metrics = []

        for metric, value in metrics:
            tree.insert('', tk.END, values=(metric, value))

        row = {'algorithm': self._alg_var.get()}
        row.update({k: v for k, v in result.items()
                    if k not in ('path', 'path_taken', 'cost_history', '_nodes', '_explored_set')})
        self._results_history.append(row)

        maze_basename = os.path.basename(self.maze.filepath)
        maze_name = os.path.splitext(maze_basename)[0]
        csv_filename = f"metrics_{maze_name}_{self._last_alg_type}.csv"
        csv_path = os.path.join(os.path.dirname(__file__), 'results', csv_filename)
        try:
            save_csv([row], csv_path, append=True)
        except Exception as e:
            print(f"Erro ao salvar CSV automático: {e}")

        success = result.get('success', True)
        self._status_var.set(
            f"{self._alg_var.get()}: {'Concluído ✓' if success else 'Falhou ✗'}")

        path = result.get('path', [])
        if self._last_alg_type in ('classical', 'local') and path:
            self._animating = True
            self._animate_path(path, 0)
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
            if self._last_alg_type == 'local' and self._last_result.get('_nodes'):
                highlight = self._last_result['_nodes'][1:-1]
            if self._show_explored_var.get() and self._last_alg_type == 'classical':
                explored = self._last_result.get('_explored_set')
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

        path = result.get('path', result.get('path_taken', []))
        explored = None
        if self._show_explored_var.get() and self._last_alg_type == 'classical':
            explored = result.get('_explored_set')

        if self._last_alg_type == 'online':
            if self._online_agent:
                snapshot = self._online_agent.get_snapshot()
                draw_maze_on_canvas(self.canvas, snapshot, cell_size, path=path)
            else:
                draw_maze_on_canvas(self.canvas, self.maze.grid, cell_size, path=path)
        else:
            highlight = None
            if self._last_alg_type == 'local' and result.get('_nodes'):
                highlight = result['_nodes'][1:-1]  # pontos C
            draw_maze_on_canvas(
                self.canvas, self.maze.grid, cell_size,
                path=path, explored=explored, highlight=highlight,
            )

    def _show_convergence(self, result: dict, alg_name: str) -> None:
        history = result.get('cost_history', [])
        if not history:
            return

        # Downsample para melhorar a leitura e não travar o plot
        max_points = 200
        if len(history) > max_points:
            step = len(history) / max_points
            history = [history[int(i * step)] for i in range(max_points)]

        title = 'Hill-Climbing' if alg_name == 'hc' else 'Simulated Annealing'
        
        # Auto-exportar gráfico
        maze_basename = os.path.basename(self.maze.filepath)
        maze_name = os.path.splitext(maze_basename)[0]
        plot_path = os.path.join(os.path.dirname(__file__), 'results', 'plots', f"conv_{maze_name}_{alg_name}.png")
        try:
            from core.metrics import plot_convergence
            plot_convergence({title: history}, title=f"Convergência — {title}", save_path=plot_path)
        except Exception as e:
            print(f"Erro ao salvar gráfico automático: {e}")

        win = tk.Toplevel(self.master)
        win.title(f'Convergência — {title}')
        win.geometry('640x480')

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(history, color='#E85D24', linewidth=1.5, label=title)
        ax.set_title(f'Convergência — {title}')
        ax.set_xlabel('Iteração')
        ax.set_ylabel('Melhor custo')
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.tight_layout()

        canvas_fig = FigureCanvasTkAgg(fig, master=win)
        canvas_fig.draw()
        canvas_fig.get_tk_widget().pack(fill=tk.BOTH, expand=True)


    def export_csv(self) -> None:
        if not self._results_history:
            messagebox.showwarning('Aviso', 'Nenhum resultado para exportar.')
            return

        filepath = filedialog.asksaveasfilename(
            title='Salvar resultados como CSV',
            defaultextension='.csv',
            filetypes=[('CSV', '*.csv')],
            initialdir=os.path.join(os.path.dirname(__file__), 'results'),
        )
        if not filepath:
            return

        try:
            save_csv(self._results_history, filepath)
            messagebox.showinfo('Exportado', f'Resultados salvos em:\n{filepath}')
        except Exception as e:
            messagebox.showerror('Erro', str(e))


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
