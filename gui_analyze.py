"""
gui_analyze.py
The Analyze tab. Lets the user drag and drop files (or browse for them),
shows the queued file list, then runs the analysis in a background
thread so the progress bar keeps moving and the window does not freeze.
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    from tkinterdnd2 import DND_FILES
    HAVE_DND = True
except ImportError:
    HAVE_DND = False

import config
import analysis_runner
from logger_setup import log


class AnalyzeTab(ttk.Frame):
    def __init__(self, parent, on_finished_callback):
        super().__init__(parent, padding=20)
        self.queued_files = []
        self.on_finished_callback = on_finished_callback
        self.is_running = False
        self._build_layout()

    def _build_layout(self):
        ttk.Label(self, text="Analyze Emails", style="Header.TLabel").pack(anchor="w", pady=(0, 16))

        # drop zone
        self.drop_zone = tk.Frame(self, bg=config.COLOR_PANEL, highlightbackground=config.COLOR_ACCENT,
                                   highlightthickness=2, height=120)
        self.drop_zone.pack(fill="x", pady=(0, 12))
        self.drop_zone.pack_propagate(False)

        drop_text = "Drag and drop .eml .msg .txt .csv .mbox .zip files here"
        if not HAVE_DND:
            drop_text += "\n(drag and drop unavailable, use Browse button below)"

        self.drop_label = tk.Label(self.drop_zone, text=drop_text, bg=config.COLOR_PANEL,
                                    fg=config.COLOR_TEXT_DIM, font=config.FONT_BOLD, wraplength=500)
        self.drop_label.pack(expand=True)

        if HAVE_DND:
            self.drop_zone.drop_target_register(DND_FILES)
            self.drop_zone.dnd_bind("<<Drop>>", self._handle_drop)

        # buttons row
        button_row = ttk.Frame(self)
        button_row.pack(fill="x", pady=(0, 12))

        ttk.Button(button_row, text="Browse Files...", command=self._browse_files).pack(side="left")
        ttk.Button(button_row, text="Clear Queue", command=self._clear_queue).pack(side="left", padx=8)
        self.start_button = ttk.Button(button_row, text="Start Analysis", style="Accent.TButton",
                                        command=self._start_analysis)
        self.start_button.pack(side="right")

        # queued file list
        list_frame = ttk.Frame(self, style="Panel.TFrame", padding=10)
        list_frame.pack(fill="both", expand=True, pady=(0, 12))

        ttk.Label(list_frame, text="Queued Files", style="Card.TLabel", font=config.FONT_BOLD).pack(anchor="w")

        self.file_listbox = tk.Listbox(list_frame, bg=config.COLOR_BG, fg=config.COLOR_TEXT,
                                        selectbackground=config.COLOR_ACCENT_DIM, height=8,
                                        font=config.FONT_MONO, borderwidth=0, highlightthickness=0)
        self.file_listbox.pack(fill="both", expand=True, pady=(8, 0))

        # progress area
        progress_frame = ttk.Frame(self)
        progress_frame.pack(fill="x")

        self.status_label = ttk.Label(progress_frame, text="Ready.", style="Dim.TLabel")
        self.status_label.pack(anchor="w")

        self.progress_bar = ttk.Progressbar(progress_frame, mode="determinate")
        self.progress_bar.pack(fill="x", pady=(6, 0))

    def _handle_drop(self, event):
        raw_paths = self.tk.splitlist(event.data)
        for path in raw_paths:
            self._add_file(path)

    def _browse_files(self):
        file_types = [
            ("Supported email files", "*.eml *.msg *.txt *.csv *.mbox *.zip"),
            ("All files", "*.*"),
        ]
        paths = filedialog.askopenfilenames(title="Select email files", filetypes=file_types)
        for path in paths:
            self._add_file(path)

    def _add_file(self, path):
        ext = os.path.splitext(path)[1].lower()
        if ext not in config.SUPPORTED_EXTENSIONS:
            messagebox.showwarning("Unsupported file", "File type not supported: " + path)
            return
        if path not in self.queued_files:
            self.queued_files.append(path)
            self.file_listbox.insert("end", os.path.basename(path) + "   (" + path + ")")

    def _clear_queue(self):
        self.queued_files = []
        self.file_listbox.delete(0, "end")
        self.status_label.configure(text="Ready.")
        self.progress_bar["value"] = 0

    def _start_analysis(self):
        if self.is_running:
            return
        if not self.queued_files:
            messagebox.showinfo("No files", "Add some files first using drag and drop or the Browse button.")
            return

        self.is_running = True
        self.start_button.configure(state="disabled")
        self.progress_bar["value"] = 0
        self.progress_bar["maximum"] = len(self.queued_files)

        worker = threading.Thread(target=self._run_analysis_thread, daemon=True)
        worker.start()

    def _run_analysis_thread(self):
        total_results = []
        files_to_run = list(self.queued_files)

        for index, file_path in enumerate(files_to_run):
            def progress_update(text, idx=index, fname=os.path.basename(file_path)):
                self.after(0, lambda: self.status_label.configure(
                    text="File " + str(idx + 1) + "/" + str(len(files_to_run)) + " (" + fname + "): " + text
                ))

            try:
                results = analysis_runner.analyze_file(file_path, progress_callback=progress_update)
                total_results.extend(results)
            except Exception as err:
                log.error("analysis failed for %s : %s", file_path, err)

            self.after(0, lambda v=index + 1: self.progress_bar.configure(value=v))

        self.after(0, lambda: self._finish_analysis(total_results))

    def _finish_analysis(self, total_results):
        self.is_running = False
        self.start_button.configure(state="normal")
        self.status_label.configure(text="Done. Analyzed " + str(len(total_results)) + " email(s).")
        self._clear_queue()

        if self.on_finished_callback:
            self.on_finished_callback(total_results)
