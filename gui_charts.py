"""
gui_charts.py
Builds the matplotlib charts and embeds them into a tkinter frame.
Kept separate from gui_dashboard.py so the chart drawing code does not
clutter up the layout code.
"""

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import config


def _style_axes(fig, ax):
    fig.patch.set_facecolor(config.COLOR_PANEL)
    ax.set_facecolor(config.COLOR_PANEL)
    ax.tick_params(colors=config.COLOR_TEXT_DIM, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color(config.COLOR_BORDER)
    ax.title.set_color(config.COLOR_TEXT)
    ax.xaxis.label.set_color(config.COLOR_TEXT_DIM)
    ax.yaxis.label.set_color(config.COLOR_TEXT_DIM)


def draw_risk_pie(parent_frame, distribution_dict):
    """pie chart of how many emails fall into each risk level"""
    fig = plt.Figure(figsize=(4, 3.2), dpi=100)
    ax = fig.add_subplot(111)
    _style_axes(fig, ax)

    labels = []
    sizes = []
    colors_list = []

    order = ["Minimal", "Low", "Medium", "High", "Critical"]
    for level in order:
        if level in distribution_dict and distribution_dict[level] > 0:
            labels.append(level)
            sizes.append(distribution_dict[level])
            colors_list.append(config.RISK_COLORS.get(level, "#888888"))

    if not sizes:
        ax.text(0.5, 0.5, "No data yet", ha="center", va="center", color=config.COLOR_TEXT_DIM)
        ax.axis("off")
    else:
        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, colors=colors_list, autopct="%1.0f%%",
            textprops={"color": config.COLOR_TEXT, "fontsize": 8},
        )
        ax.set_title("Risk Level Distribution", fontsize=10)

    fig.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    canvas.draw()
    return canvas.get_tk_widget()


def draw_top_indicators_bar(parent_frame, indicator_pairs):
    """horizontal bar chart of most common indicator categories"""
    fig = plt.Figure(figsize=(5, 3.2), dpi=100)
    ax = fig.add_subplot(111)
    _style_axes(fig, ax)

    if not indicator_pairs:
        ax.text(0.5, 0.5, "No data yet", ha="center", va="center", color=config.COLOR_TEXT_DIM)
        ax.axis("off")
    else:
        categories = [p[0] for p in indicator_pairs][::-1]
        counts = [p[1] for p in indicator_pairs][::-1]
        ax.barh(categories, counts, color=config.COLOR_ACCENT)
        ax.set_title("Top Indicator Categories", fontsize=10)
        ax.set_xlabel("Count")

    fig.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    canvas.draw()
    return canvas.get_tk_widget()


def draw_timeline(parent_frame, timeline_pairs):
    """line chart of emails analyzed per day"""
    fig = plt.Figure(figsize=(9, 3), dpi=100)
    ax = fig.add_subplot(111)
    _style_axes(fig, ax)

    if not timeline_pairs:
        ax.text(0.5, 0.5, "No data yet", ha="center", va="center", color=config.COLOR_TEXT_DIM)
        ax.axis("off")
    else:
        days = [p[0] for p in timeline_pairs]
        counts = [p[1] for p in timeline_pairs]
        ax.plot(days, counts, color=config.COLOR_ACCENT, marker="o")
        ax.fill_between(range(len(days)), counts, color=config.COLOR_ACCENT, alpha=0.15)
        ax.set_title("Emails Analyzed Over Time", fontsize=10)
        ax.set_ylabel("Count")
        if len(days) > 8:
            for label in ax.get_xticklabels():
                label.set_rotation(45)
                label.set_ha("right")

    fig.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    canvas.draw()
    return canvas.get_tk_widget()
