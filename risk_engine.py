"""
risk_engine.py
Takes the results from every analyzer (auth, url, attachment, content, ml)
and turns them into one final 0-100 risk score plus a risk level label.

The weights below were picked by hand to feel reasonable, not from some
fancy statistical model. Feel free to tune them.
"""

import config
from logger_setup import log


def calculate_risk(auth_result, url_result, attachment_result, content_result, ml_result):
    score = 0

    # authentication problems are a strong signal
    if auth_result["spf"] in ("fail", "softfail"):
        score += 12
    elif auth_result["spf"] == "none":
        score += 5

    if auth_result["dkim"] in ("fail", "none"):
        score += 10

    if auth_result["dmarc"] == "fail":
        score += 15
    elif auth_result["dmarc"] == "none":
        score += 3

    if auth_result.get("spoof_flag"):
        score += 20

    # urls
    score += min(url_result["suspicious_url_count"] * 6, 24)
    if url_result["url_count"] > 8:
        score += 4

    # attachments
    score += min(attachment_result["dangerous_count"] * 15, 30)

    # content heuristics, capped contribution already inside content_analyzer
    score += content_result["score_hint"]

    # ml classifier confidence, scaled to a max contribution of 25 points
    if ml_result["label"] == "phishing":
        score += round(ml_result["confidence"] * 25)

    score = max(0, min(100, score))
    level = config.get_risk_level(score)

    return score, level


def combine_indicators(*indicator_lists):
    """just flattens all the indicator lists from each analyzer into one list"""
    combined = []
    for lst in indicator_lists:
        combined.extend(lst)
    return combined
