"""
gui_theme.py
Sets up the dark cybersecurity look for all the ttk widgets so we do
not have to repeat style code in every gui file.
"""

import tkinter as tk
from tkinter import ttk
import config


def apply_theme(root):
    style = ttk.Style(root)

    # 'clam' theme is the easiest base theme to recolor
    style.theme_use("clam")

    root.configure(bg=config.COLOR_BG)

    style.configure(".",
                     background=config.COLOR_BG,
                     foreground=config.COLOR_TEXT,
                     font=config.FONT_NORMAL)

    style.configure("TFrame", background=config.COLOR_BG)

    style.configure("Panel.TFrame", background=config.COLOR_PANEL)

    style.configure("TLabel",
                     background=config.COLOR_BG,
                     foreground=config.COLOR_TEXT,
                     font=config.FONT_NORMAL)

    style.configure("Header.TLabel",
                     background=config.COLOR_BG,
                     foreground=config.COLOR_ACCENT,
                     font=config.FONT_HEADER)

    style.configure("Dim.TLabel",
                     background=config.COLOR_BG,
                     foreground=config.COLOR_TEXT_DIM,
                     font=config.FONT_NORMAL)

    style.configure("Card.TLabel",
                     background=config.COLOR_PANEL,
                     foreground=config.COLOR_TEXT,
                     font=config.FONT_NORMAL)

    style.configure("CardValue.TLabel",
                     background=config.COLOR_PANEL,
                     foreground=config.COLOR_ACCENT,
                     font=("Segoe UI", 22, "bold"))

    style.configure("TButton",
                     background=config.COLOR_PANEL,
                     foreground=config.COLOR_TEXT,
                     font=config.FONT_BOLD,
                     borderwidth=1,
                     focusthickness=0,
                     padding=8)
    style.map("TButton",
              background=[("active", config.COLOR_BORDER)],
              foreground=[("active", config.COLOR_ACCENT)])

    style.configure("Accent.TButton",
                     background=config.COLOR_ACCENT,
                     foreground="#001b10",
                     font=config.FONT_BOLD,
                     padding=8)
    style.map("Accent.TButton",
              background=[("active", config.COLOR_ACCENT_DIM)])

    style.configure("Danger.TButton",
                     background=config.COLOR_DANGER,
                     foreground="#1a0000",
                     font=config.FONT_BOLD,
                     padding=8)

    style.configure("TNotebook", background=config.COLOR_BG, borderwidth=0)
    style.configure("TNotebook.Tab",
                     background=config.COLOR_PANEL,
                     foreground=config.COLOR_TEXT_DIM,
                     padding=[16, 8],
                     font=config.FONT_BOLD)
    style.map("TNotebook.Tab",
              background=[("selected", config.COLOR_BG)],
              foreground=[("selected", config.COLOR_ACCENT)])

    style.configure("Treeview",
                     background=config.COLOR_PANEL,
                     foreground=config.COLOR_TEXT,
                     fieldbackground=config.COLOR_PANEL,
                     borderwidth=0,
                     rowheight=26,
                     font=config.FONT_NORMAL)
    style.configure("Treeview.Heading",
                     background=config.COLOR_BORDER,
                     foreground=config.COLOR_TEXT,
                     font=config.FONT_BOLD)
    style.map("Treeview",
              background=[("selected", config.COLOR_ACCENT_DIM)],
              foreground=[("selected", "#001b10")])

    style.configure("TEntry",
                     fieldbackground=config.COLOR_PANEL,
                     foreground=config.COLOR_TEXT,
                     insertcolor=config.COLOR_TEXT,
                     borderwidth=1)

    style.configure("TCombobox",
                     fieldbackground=config.COLOR_PANEL,
                     background=config.COLOR_PANEL,
                     foreground=config.COLOR_TEXT,
                     arrowcolor=config.COLOR_TEXT)

    style.configure("Horizontal.TProgressbar",
                     background=config.COLOR_ACCENT,
                     troughcolor=config.COLOR_PANEL,
                     borderwidth=0)

    style.configure("TScrollbar",
                     background=config.COLOR_PANEL,
                     troughcolor=config.COLOR_BG,
                     arrowcolor=config.COLOR_TEXT)

    return style


def make_card(parent, title, value_text, value_color=None):
    """small stat card used on the dashboard, returns the frame"""
    frame = ttk.Frame(parent, style="Panel.TFrame", padding=16)

    title_label = ttk.Label(frame, text=title, style="Card.TLabel", font=config.FONT_NORMAL)
    title_label.pack(anchor="w")

    value_label = ttk.Label(frame, text=value_text, style="CardValue.TLabel")
    if value_color:
        value_label.configure(foreground=value_color)
    value_label.pack(anchor="w", pady=(6, 0))

    return frame
