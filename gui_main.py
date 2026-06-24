"""
gui_main.py
Builds the main window: title bar area, the notebook with the three
tabs (Analyze, Results, Dashboard), and a bottom status bar.
"""

import tkinter as tk
from tkinter import ttk

import config
import gui_theme
from gui_analyze import AnalyzeTab
from gui_results import ResultsTab
from gui_dashboard import DashboardTab


class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title(config.APP_NAME + "  v" + config.APP_VERSION)
        self.root.geometry("1150x750")
        self.root.minsize(950, 650)

        gui_theme.apply_theme(self.root)

        self._build_top_bar()
        self._build_notebook()
        self._build_status_bar()

    def _build_top_bar(self):
        top_bar = tk.Frame(self.root, bg=config.COLOR_BG_LIGHT, height=56)
        top_bar.pack(fill="x", side="top")
        top_bar.pack_propagate(False)

        title_label = tk.Label(top_bar, text="🛡  " + config.APP_NAME, bg=config.COLOR_BG_LIGHT,
                                fg=config.COLOR_ACCENT, font=("Segoe UI", 15, "bold"))
        title_label.pack(side="left", padx=18)

        subtitle_label = tk.Label(top_bar, text="Phishing Email Detection & Analysis",
                                   bg=config.COLOR_BG_LIGHT, fg=config.COLOR_TEXT_DIM, font=config.FONT_NORMAL)
        subtitle_label.pack(side="left")

    def _build_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        self.analyze_tab = AnalyzeTab(self.notebook, on_finished_callback=self._on_analysis_finished)
        self.results_tab = ResultsTab(self.notebook)
        self.dashboard_tab = DashboardTab(self.notebook)

        self.notebook.add(self.analyze_tab, text="  Analyze  ")
        self.notebook.add(self.results_tab, text="  Results  ")
        self.notebook.add(self.dashboard_tab, text="  Dashboard  ")

    def _build_status_bar(self):
        bar = tk.Frame(self.root, bg=config.COLOR_BG_LIGHT, height=26)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        self.status_text = tk.Label(bar, text="Ready", bg=config.COLOR_BG_LIGHT,
                                     fg=config.COLOR_TEXT_DIM, font=("Segoe UI", 9))
        self.status_text.pack(side="left", padx=10)

    def _on_analysis_finished(self, results):
        self.status_text.configure(text="Last analysis: " + str(len(results)) + " email(s) processed.")
        self.results_tab.refresh()
        self.dashboard_tab.refresh()
        self.notebook.select(self.results_tab)
