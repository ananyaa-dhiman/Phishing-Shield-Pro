"""
gui_results.py
The Results tab. Shows every analyzed email in a table, with a search
box and risk level filter dropdown. Double-clicking a row opens a
detail window with the full explanation, recommendations, and
indicator list. Also has buttons to export to PDF/CSV.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import config
import database
import report_export
from logger_setup import log


class ResultsTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self._build_layout()
        self.refresh()

    def _build_layout(self):
        header_row = ttk.Frame(self)
        header_row.pack(fill="x", pady=(0, 12))
        ttk.Label(header_row, text="Results", style="Header.TLabel").pack(side="left")

        export_row = ttk.Frame(header_row)
        export_row.pack(side="right")
        ttk.Button(export_row, text="Export CSV", command=self._export_csv).pack(side="left", padx=4)
        ttk.Button(export_row, text="Export PDF", command=self._export_pdf).pack(side="left", padx=4)
        ttk.Button(export_row, text="Refresh", command=self.refresh).pack(side="left", padx=4)

        # search / filter row
        filter_row = ttk.Frame(self)
        filter_row.pack(fill="x", pady=(0, 10))

        ttk.Label(filter_row, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_row, textvariable=self.search_var, width=30)
        search_entry.pack(side="left", padx=(6, 16))
        search_entry.bind("<KeyRelease>", lambda e: self.refresh())

        ttk.Label(filter_row, text="Risk Level:").pack(side="left")
        self.level_var = tk.StringVar(value="All")
        level_box = ttk.Combobox(filter_row, textvariable=self.level_var, state="readonly",
                                  values=["All", "Minimal", "Low", "Medium", "High", "Critical"], width=12)
        level_box.pack(side="left", padx=(6, 0))
        level_box.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        # table
        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True)

        columns = ("id", "file", "sender", "subject", "score", "level", "date")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")

        headings = {
            "id": "ID", "file": "File", "sender": "Sender", "subject": "Subject",
            "score": "Score", "level": "Risk Level", "date": "Analyzed At",
        }
        widths = {"id": 40, "file": 150, "sender": 160, "subject": 220, "score": 60, "level": 90, "date": 130}

        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", self._open_detail)

        for level, color in config.RISK_COLORS.items():
            self.tree.tag_configure(level, foreground=color)

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        keyword = self.search_var.get().strip()
        level = self.level_var.get()
        rows = database.search_emails(keyword=keyword, risk_level=level)

        for row in rows:
            self.tree.insert("", "end", iid=str(row["id"]), values=(
                row["id"], row["file_name"], row["sender"], row["subject"],
                row["risk_score"], row["risk_level"], row["analyzed_at"],
            ), tags=(row["risk_level"],))

    def _get_selected_id(self):
        selection = self.tree.selection()
        if not selection:
            return None
        return int(selection[0])

    def _open_detail(self, event):
        email_id = self._get_selected_id()
        if email_id is None:
            return
        DetailWindow(self, email_id)

    def _get_current_rows(self):
        keyword = self.search_var.get().strip()
        level = self.level_var.get()
        return database.search_emails(keyword=keyword, risk_level=level)

    def _export_csv(self):
        rows = self._get_current_rows()
        if not rows:
            messagebox.showinfo("Nothing to export", "There are no results matching the current filter.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                             initialdir=config.EXPORT_FOLDER,
                                             initialfile="phishing_report.csv",
                                             filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        ok = report_export.export_to_csv(rows, path)
        if ok:
            messagebox.showinfo("Export complete", "CSV report saved to:\n" + path)
        else:
            messagebox.showerror("Export failed", "Could not save the CSV report, check the log file.")

    def _export_pdf(self):
        rows = self._get_current_rows()
        if not rows:
            messagebox.showinfo("Nothing to export", "There are no results matching the current filter.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                             initialdir=config.EXPORT_FOLDER,
                                             initialfile="phishing_report.pdf",
                                             filetypes=[("PDF files", "*.pdf")])
        if not path:
            return
        ok = report_export.export_to_pdf(rows, path)
        if ok:
            messagebox.showinfo("Export complete", "PDF report saved to:\n" + path)
        else:
            messagebox.showerror("Export failed", "Could not save the PDF report, check the log file.")


class DetailWindow(tk.Toplevel):
    def __init__(self, parent, email_id):
        super().__init__(parent)
        self.title("Email Analysis Detail")
        self.geometry("700x600")
        self.configure(bg=config.COLOR_BG)

        row = database.get_email_by_id(email_id)
        indicators = database.get_indicators_for_email(email_id)

        if not row:
            ttk.Label(self, text="Email not found.").pack(padx=20, pady=20)
            return

        self._build_layout(row, indicators)

    def _build_layout(self, row, indicators):
        top = ttk.Frame(self, padding=16)
        top.pack(fill="x")

        score = row["risk_score"]
        level = row["risk_level"]
        color = config.RISK_COLORS.get(level, config.COLOR_TEXT)

        ttk.Label(top, text=row["subject"] or "(no subject)", style="Header.TLabel",
                  font=("Segoe UI", 13, "bold")).pack(anchor="w")
        ttk.Label(top, text="From: " + (row["sender"] or "unknown"), style="Dim.TLabel").pack(anchor="w", pady=(4, 0))

        score_label = tk.Label(top, text="Risk Score: " + str(score) + " / 100   (" + level + ")",
                                bg=config.COLOR_BG, fg=color, font=("Segoe UI", 12, "bold"))
        score_label.pack(anchor="w", pady=(8, 0))

        auth_text = "SPF: " + str(row["spf_result"]) + "   DKIM: " + str(row["dkim_result"]) + "   DMARC: " + str(row["dmarc_result"])
        ttk.Label(top, text=auth_text, style="Dim.TLabel").pack(anchor="w", pady=(4, 0))

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        # explanation tab
        explain_frame = ttk.Frame(notebook, padding=10)
        notebook.add(explain_frame, text="Explanation")
        explain_box = tk.Text(explain_frame, wrap="word", bg=config.COLOR_PANEL, fg=config.COLOR_TEXT,
                               font=config.FONT_NORMAL, borderwidth=0)
        explain_box.insert("1.0", row["explanation_text"] or "No explanation available.")
        explain_box.configure(state="disabled")
        explain_box.pack(fill="both", expand=True)

        # recommendations tab
        rec_frame = ttk.Frame(notebook, padding=10)
        notebook.add(rec_frame, text="Recommendations")
        rec_box = tk.Text(rec_frame, wrap="word", bg=config.COLOR_PANEL, fg=config.COLOR_TEXT,
                           font=config.FONT_NORMAL, borderwidth=0)
        rec_box.insert("1.0", row["recommendation_text"] or "No recommendations available.")
        rec_box.configure(state="disabled")
        rec_box.pack(fill="both", expand=True)

        # indicators tab
        ind_frame = ttk.Frame(notebook, padding=10)
        notebook.add(ind_frame, text="Indicators (" + str(len(indicators)) + ")")

        ind_tree = ttk.Treeview(ind_frame, columns=("category", "severity", "description"), show="headings")
        ind_tree.heading("category", text="Category")
        ind_tree.heading("severity", text="Severity")
        ind_tree.heading("description", text="Description")
        ind_tree.column("category", width=110)
        ind_tree.column("severity", width=70)
        ind_tree.column("description", width=420)

        severity_colors = {
            "Low": config.COLOR_INFO, "Medium": config.COLOR_WARNING,
            "High": "#ff7a45", "Critical": config.COLOR_DANGER,
        }
        for sev, color in severity_colors.items():
            ind_tree.tag_configure(sev, foreground=color)

        for item in indicators:
            ind_tree.insert("", "end", values=(item["category"], item["severity"], item["description"]),
                             tags=(item["severity"],))

        ind_tree.pack(fill="both", expand=True)
