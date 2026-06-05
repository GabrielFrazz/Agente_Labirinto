import csv
import os
from typing import Optional

import matplotlib.pyplot as plt


_COLORS = [
    "#4C72B0",
    "#DD8452",
    "#55A868",
    "#C44E52",
    "#8172B3",
    "#937860",
    "#DA8BC3",
    "#8C8C8C",
    "#CCB974",
    "#64B5CD",
]


def save_csv(rows: list[dict], filepath: str, append: bool = False) -> None:
    if not rows:
        return

    dirpath = os.path.dirname(filepath)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)

    fieldnames = list(rows[0].keys())
    
    file_exists = os.path.exists(filepath)
    mode = "a" if append else "w"

    with open(filepath, mode=mode, newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        if not (append and file_exists):
            writer.writeheader()
        writer.writerows(rows)


def plot_convergence(
    histories: dict[str, list[float]],
    title: str = "Convergência",
    xlabel: str = "Iteração",
    ylabel: str = "Melhor custo",
    save_path: Optional[str] = None,
) -> None:
    fig, ax = plt.subplots(figsize=(10, 6))

    for idx, (label, values) in enumerate(histories.items()):
        color = _COLORS[idx % len(_COLORS)]
        ax.plot(values, label=label, color=color, linewidth=1.8)

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.legend(fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.6)

    fig.tight_layout()

    if save_path:
        dirpath = os.path.dirname(save_path)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)
        fig.savefig(save_path, dpi=150)

    plt.close(fig)


def plot_comparison_bar(
    data: dict[str, float],
    title: str,
    ylabel: str,
    save_path: Optional[str] = None,
) -> None:
    labels = list(data.keys())
    values = list(data.values())
    colors = [_COLORS[i % len(_COLORS)] for i in range(len(labels))]

    fig, ax = plt.subplots(figsize=(max(6, len(labels) * 1.2), 6))

    bars = ax.bar(labels, values, color=colors, edgecolor="white", linewidth=0.8)

    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{val:,.2f}" if isinstance(val, float) else str(val),
            ha="center",
            va="bottom",
            fontsize=9,
        )

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_ylabel(ylabel, fontsize=12)
    ax.grid(True, axis="y", linestyle="--", alpha=0.6)

    fig.tight_layout()

    if save_path:
        dirpath = os.path.dirname(save_path)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)
        fig.savefig(save_path, dpi=150)

    plt.close(fig)
