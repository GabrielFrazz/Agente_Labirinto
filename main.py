import io
import os
import sys

if sys.stdout is not None and getattr(sys.stdout, 'encoding', None) and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_gui() -> None:
    from ttkthemes import ThemedTk
    from interface import MazeApp

    root = ThemedTk(theme='arc')
    root.title('Agente em Labirinto – TP01 CSI457')
    root.geometry('1280x720')
    app = MazeApp(root)
    root.mainloop()


if __name__ == '__main__':
    run_gui()
