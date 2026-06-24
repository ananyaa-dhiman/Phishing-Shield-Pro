"""
main.py
Run this file to start Phishing Shield Pro.

    python main.py

On first run this will:
1. create the logs/model/exports folders
2. create the sqlite database and tables
3. train the ML model from the sample dataset (only if no model is saved yet)
then it opens the GUI.
"""

import sys
import config
import database
from logger_setup import log

try:
    from tkinterdnd2 import TkinterDnD
    ROOT_CLASS = TkinterDnD.Tk
except ImportError:
    import tkinter as tk
    ROOT_CLASS = tk.Tk
    log.warning("tkinterdnd2 not installed, drag and drop will be disabled. Run: pip install tkinterdnd2")

from gui_main import MainWindow


def main():
    log.info("starting %s", config.APP_NAME)

    config.make_folders()
    database.setup_database()

    root = ROOT_CLASS()
    app = MainWindow(root)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass

    log.info("application closed")


if __name__ == "__main__":
    main()
