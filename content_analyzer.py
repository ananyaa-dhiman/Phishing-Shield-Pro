"""
content_analyzer.py
Looks at the words used in the subject and body of the email to find
common phishing language patterns like urgency, threats, and requests
for sensitive info.
"""

import re
from logger_setup import log

URGENCY_WORDS = [
    "urgent", "immediately", "right away", "as soon as possible", "asap",
    "act now", "expire", "expires", "expiring", "deadline", "final notice",
    "last chance", "limited time", "within 24 hours", "within 48 hours",
    "suspend", "suspended", "locked", "restricted",
]

THREAT_WORDS = [
    "your account will be closed", "account suspended", "legal action",
    "unauthorized access", "unusual activity", "security alert",
    "you have been hacked", "failure to comply", "penalty", "fine",
]

CREDENTIAL_REQUEST_WORDS = [
    "verify your account", "confirm your password", "update your billing",
    "click here to login", "enter your password", "social security number",
    "credit card number", "bank account number", "verify your identity",
    "confirm your identity", "reset your password",
]

MONEY_WORDS = [
    "wire transfer", "gift card", "bitcoin", "western union",
    "payment is overdue", "invoice attached", "tax refund", "lottery",
    "you have won", "inheritance", "claim your prize",
]

GENERIC_GREETINGS = [
    "dear customer", "dear user", "dear valued customer", "dear account holder",
    "dear sir/madam", "dear winner",
]

POOR_GRAMMAR_PATTERNS = [
    r"\bkindly\b.*\brevert\b",
    r"\bplease to\b",
    r"\bdo the needful\b",
]


def analyze_content(email_data):
    """
    returns dict:
    {
        "indicators": [...],
        "score_hint": int   (rough 0-40 contribution, used by risk engine)
    }
    """
    subject = (email_data.get("subject", "") or "").lower()
    body = (email_data.get("body_text", "") or "").lower()
    html_body = (email_data.get("body_html", "") or "").lower()
    full_text = subject + " " + body + " " + html_body

    indicators = []
    hint = 0

    urgency_hits = _count_hits(full_text, URGENCY_WORDS)
    if urgency_hits > 0:
        indicators.append(_make_indicator(
            "Content Analysis",
            "Email uses urgency language (" + str(urgency_hits) + " phrase match(es)) to pressure quick action.",
            "Medium",
        ))
        hint += min(urgency_hits * 3, 10)

    threat_hits = _count_hits(full_text, THREAT_WORDS)
    if threat_hits > 0:
        indicators.append(_make_indicator(
            "Content Analysis",
            "Email contains threatening or alarming language about the account or legal consequences.",
            "High",
        ))
        hint += min(threat_hits * 4, 12)

    cred_hits = _count_hits(full_text, CREDENTIAL_REQUEST_WORDS)
    if cred_hits > 0:
        indicators.append(_make_indicator(
            "Content Analysis",
            "Email asks the reader to enter or confirm sensitive credentials or personal information.",
            "Critical",
        ))
        hint += min(cred_hits * 5, 15)

    money_hits = _count_hits(full_text, MONEY_WORDS)
    if money_hits > 0:
        indicators.append(_make_indicator(
            "Content Analysis",
            "Email mentions money transfers, gift cards, or unexpected prizes, a common scam pattern.",
            "High",
        ))
        hint += min(money_hits * 4, 12)

    greeting_hits = _count_hits(full_text, GENERIC_GREETINGS)
    if greeting_hits > 0:
        indicators.append(_make_indicator(
            "Content Analysis",
            "Email uses a generic greeting instead of the recipient's actual name, common in mass phishing campaigns.",
            "Low",
        ))
        hint += 3

    grammar_hits = 0
    for pattern in POOR_GRAMMAR_PATTERNS:
        if re.search(pattern, full_text):
            grammar_hits += 1
    if grammar_hits > 0:
        indicators.append(_make_indicator(
            "Content Analysis",
            "Email text contains phrasing patterns often seen in poorly translated phishing templates.",
            "Low",
        ))
        hint += 2

    # ALL CAPS shouting in subject line
    raw_subject = email_data.get("subject", "") or ""
    letters_only = re.sub(r"[^A-Za-z]", "", raw_subject)
    if len(letters_only) > 6 and letters_only.isupper():
        indicators.append(_make_indicator(
            "Content Analysis",
            "Subject line is written in all capital letters, often used to grab attention in spam.",
            "Low",
        ))
        hint += 2

    # excessive exclamation marks
    if raw_subject.count("!") >= 2 or body.count("!") >= 5:
        indicators.append(_make_indicator(
            "Content Analysis",
            "Excessive use of exclamation marks in subject or body.",
            "Low",
        ))
        hint += 2

    return {
        "indicators": indicators,
        "score_hint": min(hint, 40),
    }


def _count_hits(text, word_list):
    count = 0
    for word in word_list:
        if word in text:
            count += 1
    return count


def _make_indicator(category, description, severity):
    return {"category": category, "description": description, "severity": severity}
