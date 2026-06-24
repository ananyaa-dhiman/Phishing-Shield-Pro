"""
gui_dashboard.py
The Dashboard tab. Shows stat cards at the top and three charts below:
risk distribution pie, top indicators bar, and a timeline.
"""

import tkinter as tk
from tkinter import ttk

import config
import database
import gui_theme
import gui_charts


class DashboardTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.chart_widgets = []
        self._build_layout()
        self.refresh()

    def _build_layout(self):
        header_row = ttk.Frame(self)
        header_row.pack(fill="x", pady=(0, 16))

        ttk.Label(header_row, text="Dashboard", style="Header.TLabel").pack(side="left")
        refresh_btn = ttk.Button(header_row, text="Refresh", command=self.refresh)
        refresh_btn.pack(side="right")

        self.cards_row = ttk.Frame(self)
        self.cards_row.pack(fill="x", pady=(0, 16))

        self.charts_area = ttk.Frame(self)
        self.charts_area.pack(fill="both", expand=True)

    def refresh(self):
        # clear old cards
        for widget in self.cards_row.winfo_children():
            widget.destroy()

        stats = database.get_stats()

        card1 = gui_theme.make_card(self.cards_row, "Total Emails Analyzed", str(stats["total"]))
        card2 = gui_theme.make_card(self.cards_row, "High / Critical Risk", str(stats["dangerous"]), config.COLOR_DANGER)
        card3 = gui_theme.make_card(self.cards_row, "Average Risk Score", str(stats["avg_score"]))
        card4 = gui_theme.make_card(self.cards_row, "Spoofing Detected", str(stats["spoofed"]), config.COLOR_WARNING)

        for card in (card1, card2, card3, card4):
            card.pack(side="left", fill="both", expand=True, padx=6)

        # clear old charts
        for widget in self.charts_area.winfo_children():
            widget.destroy()

        top_row = ttk.Frame(self.charts_area)
        top_row.pack(fill="both", expand=True)

        pie_panel = ttk.Frame(top_row, style="Panel.TFrame", padding=10)
        pie_panel.pack(side="left", fill="both", expand=True, padx=(0, 6))
        distribution = database.get_risk_distribution()
        pie_widget = gui_charts.draw_risk_pie(pie_panel, distribution)
        pie_widget.pack(fill="both", expand=True)

        bar_panel = ttk.Frame(top_row, style="Panel.TFrame", padding=10)
        bar_panel.pack(side="left", fill="both", expand=True, padx=(6, 0))
        top_indicators = database.get_top_indicators()
        bar_widget = gui_charts.draw_top_indicators_bar(bar_panel, top_indicators)
        bar_widget.pack(fill="both", expand=True)

        bottom_panel = ttk.Frame(self.charts_area, style="Panel.TFrame", padding=10)
        bottom_panel.pack(fill="both", expand=True, pady=(12, 0))
        timeline = database.get_timeline()
        timeline_widget = gui_charts.draw_timeline(bottom_panel, timeline)
        timeline_widget.pack(fill="both", expand=True)
