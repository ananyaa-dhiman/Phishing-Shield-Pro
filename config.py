"""
config.py
Holds all the constant values used across the app.
Keeping them in one file so we do not repeat magic numbers everywhere.
"""

import os

# base folder of the project, works on windows and linux
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "phishing_shield.db")
LOG_FOLDER = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_FOLDER, "app.log")
MODEL_FOLDER = os.path.join(BASE_DIR, "model_files")
MODEL_FILE = os.path.join(MODEL_FOLDER, "phishing_model.pkl")
VECTOR_FILE = os.path.join(MODEL_FOLDER, "tfidf_vectorizer.pkl")
TRAIN_DATA_FILE = os.path.join(BASE_DIR, "train_data.csv")
EXPORT_FOLDER = os.path.join(BASE_DIR, "exports")

APP_NAME = "Phishing Shield Pro"
APP_VERSION = "1.0.0"

# file types we know how to open
SUPPORTED_EXTENSIONS = [".eml", ".msg", ".txt", ".csv", ".mbox", ".zip"]

# risk score bands, score goes from 0 to 100
RISK_LEVELS = [
    (0, 19, "Minimal"),
    (20, 39, "Low"),
    (40, 59, "Medium"),
    (60, 79, "High"),
    (80, 100, "Critical"),
]

# dark cybersecurity theme colors
COLOR_BG = "#0d1117"
COLOR_BG_LIGHT = "#161b22"
COLOR_PANEL = "#1c2128"
COLOR_BORDER = "#30363d"
COLOR_TEXT = "#c9d1d9"
COLOR_TEXT_DIM = "#8b949e"
COLOR_ACCENT = "#00ff9d"
COLOR_ACCENT_DIM = "#00b377"
COLOR_DANGER = "#ff4d4f"
COLOR_WARNING = "#ffb020"
COLOR_OK = "#3fb950"
COLOR_INFO = "#58a6ff"

FONT_NORMAL = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_HEADER = ("Segoe UI", 16, "bold")
FONT_MONO = ("Consolas", 10)

# colors tied to risk level, used in charts and tables
RISK_COLORS = {
    "Minimal": COLOR_OK,
    "Low": COLOR_INFO,
    "Medium": COLOR_WARNING,
    "High": "#ff7a45",
    "Critical": COLOR_DANGER,
}


def get_risk_level(score):
    """take a 0-100 score and return the matching text label"""
    for low, high, name in RISK_LEVELS:
        if low <= score <= high:
            return name
    return "Unknown"


def make_folders():
    """create any missing folders the app needs on first run"""
    for folder in [LOG_FOLDER, MODEL_FOLDER, EXPORT_FOLDER]:
        if not os.path.exists(folder):
            os.makedirs(folder)
