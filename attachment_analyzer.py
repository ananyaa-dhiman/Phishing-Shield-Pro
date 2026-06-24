"""
attachment_analyzer.py
Looks at file attachments for dangerous types, double extensions,
macro-enabled office files, and other red flags.
"""

import os
from logger_setup import log

DANGEROUS_EXTENSIONS = [
    ".exe", ".scr", ".bat", ".cmd", ".com", ".pif", ".vbs", ".vbe",
    ".js", ".jse", ".wsf", ".wsh", ".msi", ".jar", ".ps1", ".reg",
    ".lnk", ".hta", ".gadget", ".cpl",
]

MACRO_EXTENSIONS = [".docm", ".xlsm", ".pptm", ".dotm", ".xltm"]

ARCHIVE_EXTENSIONS = [".zip", ".rar", ".7z", ".iso", ".tar", ".gz"]

COMMON_SAFE_EXTENSIONS = [
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".docx", ".xlsx", ".pptx",
    ".txt", ".csv",
]


def analyze_attachments(email_data):
    """
    returns dict:
    {
        "attachment_count": int,
        "dangerous_count": int,
        "indicators": [...]
    }
    """
    attachments = email_data.get("attachments", [])
    indicators = []
    dangerous_count = 0

    for att in attachments:
        name = att.get("name", "unnamed")
        size = att.get("size", 0)
        ext = os.path.splitext(name)[1].lower()

        problems = _check_single_attachment(name, ext, size)

        if problems:
            dangerous_count += 1

        for problem, severity in problems:
            indicators.append(_make_indicator("Attachment Analysis", problem, severity))

    if len(attachments) > 5:
        indicators.append(_make_indicator(
            "Attachment Analysis",
            "Email has an unusually large number of attachments (" + str(len(attachments)) + ").",
            "Low",
        ))

    return {
        "attachment_count": len(attachments),
        "dangerous_count": dangerous_count,
        "indicators": indicators,
    }


def _check_single_attachment(name, ext, size):
    """returns list of (description, severity) tuples"""
    problems = []
    lower_name = name.lower()

    if ext in DANGEROUS_EXTENSIONS:
        problems.append((
            "Attachment '" + name + "' has a dangerous executable extension (" + ext + ").",
            "Critical",
        ))

    if ext in MACRO_EXTENSIONS:
        problems.append((
            "Attachment '" + name + "' is a macro-enabled office document (" + ext + "), macros can run hidden code.",
            "High",
        ))

    # double extension trick, like invoice.pdf.exe
    name_no_ext = lower_name[: -len(ext)] if ext else lower_name
    other_ext = os.path.splitext(name_no_ext)[1].lower()
    if other_ext and other_ext in COMMON_SAFE_EXTENSIONS and ext in DANGEROUS_EXTENSIONS + [".js", ".vbs"]:
        problems.append((
            "Attachment '" + name + "' uses a double extension trick to look like a " + other_ext + " file.",
            "Critical",
        ))

    if ext in ARCHIVE_EXTENSIONS:
        problems.append((
            "Attachment '" + name + "' is a compressed archive (" + ext + "), its real contents cannot be checked here directly.",
            "Medium",
        ))

    if size == 0:
        problems.append((
            "Attachment '" + name + "' appears to be empty or could not be read.",
            "Low",
        ))

    if size > 25 * 1024 * 1024:
        problems.append((
            "Attachment '" + name + "' is unusually large (" + str(round(size / (1024*1024), 1)) + " MB).",
            "Low",
        ))

    # generic invoice/receipt naming combined with risky type is a common lure
    lure_words = ["invoice", "receipt", "payment", "statement", "document", "scan", "fax", "order"]
    if ext in DANGEROUS_EXTENSIONS + MACRO_EXTENSIONS:
        for word in lure_words:
            if word in lower_name:
                problems.append((
                    "Attachment name '" + name + "' uses a common business lure word together with a risky file type.",
                    "High",
                ))
                break

    return problems


def _make_indicator(category, description, severity):
    return {"category": category, "description": description, "severity": severity}
