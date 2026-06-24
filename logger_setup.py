"""
logger_setup.py
Simple logging setup. We write to a log file and also print to console
so the manager... I mean the user, can see what is happening.
"""

import logging
import config


def get_logger():
    config.make_folders()

    logger = logging.getLogger("phishing_shield")
    logger.setLevel(logging.DEBUG)

    # avoid adding handlers twice if this gets called more than once
    if logger.handlers:
        return logger

    file_format = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S"
    )

    file_handler = logging.FileHandler(config.LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_format)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(file_format)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


log = get_logger()
