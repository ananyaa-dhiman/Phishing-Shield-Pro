"""
auth_checker.py
Looks at email headers to check SPF, DKIM, DMARC results and to spot
common spoofing tricks. We read the headers that the receiving mail
server already wrote (Authentication-Results, Received-SPF) instead of
doing live DNS lookups, because by the time we are analyzing a saved
.eml file the original sending server is what matters, and that
information is already stamped on the message by the mail provider.
"""

import re
from logger_setup import log


def check_authentication(email_data):
    """
    returns a dict:
    {
        "spf": "pass" / "fail" / "none" / "unknown",
        "dkim": "pass" / "fail" / "none" / "unknown",
        "dmarc": "pass" / "fail" / "none" / "unknown",
        "indicators": [list of indicator dicts]
    }
    """
    headers = email_data.get("headers", {})
    indicators = []

    auth_results_header = headers.get("authentication-results", "")
    received_spf_header = headers.get("received-spf", "")
    dkim_header = headers.get("dkim-signature", "")

    spf_result = _find_result(auth_results_header, "spf")
    if spf_result == "unknown" and received_spf_header:
        spf_result = _find_result(received_spf_header, "spf")
        if spf_result == "unknown":
            # received-spf headers often start with the word pass/fail/none directly
            lower_text = received_spf_header.lower()
            for word in ["pass", "fail", "softfail", "neutral", "none"]:
                if lower_text.strip().startswith(word):
                    spf_result = word
                    break

    dkim_result = _find_result(auth_results_header, "dkim")
    if dkim_result == "unknown" and dkim_header:
        dkim_result = "present"

    dmarc_result = _find_result(auth_results_header, "dmarc")

    if spf_result in ("fail", "softfail"):
        indicators.append(_make_indicator(
            "Authentication",
            "SPF check did not pass (result: " + spf_result + "). The sending server is not authorized for this domain.",
            "High",
        ))
    elif spf_result == "none":
        indicators.append(_make_indicator(
            "Authentication",
            "No SPF record found for the sending domain.",
            "Medium",
        ))

    if dkim_result in ("fail", "none"):
        indicators.append(_make_indicator(
            "Authentication",
            "DKIM signature missing or invalid (result: " + dkim_result + "). Message content could have been altered.",
            "High",
        ))

    if dmarc_result == "fail":
        indicators.append(_make_indicator(
            "Authentication",
            "DMARC check failed, message does not align with the sender domain policy.",
            "Critical",
        ))
    elif dmarc_result == "none":
        indicators.append(_make_indicator(
            "Authentication",
            "No DMARC policy result found.",
            "Low",
        ))

    spoof_flag, spoof_indicators = check_spoofing(email_data)
    indicators.extend(spoof_indicators)

    return {
        "spf": spf_result,
        "dkim": dkim_result,
        "dmarc": dmarc_result,
        "spoof_flag": spoof_flag,
        "indicators": indicators,
    }


def _find_result(header_text, keyword):
    """
    Authentication-Results headers look like:
    spf=pass smtp.mailfrom=example.com; dkim=fail header.d=example.com; dmarc=pass
    this pulls out the word right after "keyword="
    """
    if not header_text:
        return "unknown"

    pattern = keyword + r"\s*=\s*(\w+)"
    match = re.search(pattern, header_text, re.IGNORECASE)
    if match:
        return match.group(1).lower()
    return "unknown"


def _make_indicator(category, description, severity):
    return {"category": category, "description": description, "severity": severity}


def check_spoofing(email_data):
    """
    Looks for mismatches that suggest the sender is faking who they are.
    Returns (spoof_flag, indicator_list)
    """
    indicators = []
    spoof_flag = False

    headers = email_data.get("headers", {})
    sender = email_data.get("sender", "")
    reply_to = headers.get("reply-to", "")
    return_path = headers.get("return-path", "")

    sender_display, sender_email = _split_display_and_email(sender)
    sender_domain = _get_domain(sender_email)

    # 1) display name shows a real company but the email domain does not match
    known_brands = [
        "paypal", "microsoft", "apple", "amazon", "google", "bank",
        "netflix", "facebook", "instagram", "irs", "fedex", "ups", "dhl",
        "linkedin", "outlook", "office365", "docusign",
    ]
    if sender_display:
        display_lower = sender_display.lower()
        for brand in known_brands:
            if brand in display_lower and sender_domain and brand not in sender_domain:
                indicators.append(_make_indicator(
                    "Spoofing",
                    "Display name claims to be '" + sender_display + "' but the actual sending domain is '" + sender_domain + "', which does not match.",
                    "Critical",
                ))
                spoof_flag = True
                break

    # 2) reply-to domain is different from the from domain, a classic phishing trick
    if reply_to:
        _, reply_email = _split_display_and_email(reply_to)
        reply_domain = _get_domain(reply_email)
        if reply_domain and sender_domain and reply_domain != sender_domain:
            indicators.append(_make_indicator(
                "Spoofing",
                "Reply-To domain ('" + reply_domain + "') is different from the From domain ('" + sender_domain + "'). Replies would go somewhere else than expected.",
                "High",
            ))
            spoof_flag = True

    # 3) return-path domain different from from domain
    if return_path:
        _, return_email = _split_display_and_email(return_path)
        return_domain = _get_domain(return_email)
        if return_domain and sender_domain and return_domain != sender_domain:
            indicators.append(_make_indicator(
                "Spoofing",
                "Return-Path domain ('" + return_domain + "') does not match the From domain ('" + sender_domain + "').",
                "Medium",
            ))
            spoof_flag = True

    # 4) lookalike domain check, things like paypa1.com, micros0ft.com, faceb00k-security.com
    if sender_domain and _looks_like_lookalike_domain(sender_domain):
        indicators.append(_make_indicator(
            "Spoofing",
            "Sending domain '" + sender_domain + "' looks like it is imitating a well known brand using lookalike characters or extra words.",
            "High",
        ))
        spoof_flag = True

    return spoof_flag, indicators


def _split_display_and_email(raw_value):
    """ 'John Smith <john@example.com>' -> ('John Smith', 'john@example.com') """
    if not raw_value:
        return "", ""

    match = re.search(r"(.*)<(.+)>", raw_value)
    if match:
        display = match.group(1).strip().strip('"')
        addr = match.group(2).strip()
        return display, addr

    # no angle brackets, just an address
    return "", raw_value.strip()


def _get_domain(email_address):
    if not email_address or "@" not in email_address:
        return ""
    return email_address.split("@")[-1].strip().lower().rstrip(">").rstrip()


_LOOKALIKE_BRANDS = [
    "paypal", "microsoft", "apple", "amazon", "google", "netflix",
    "facebook", "instagram", "linkedin", "bankofamerica", "wellsfargo",
    "chase", "fedex", "ups", "dhl", "docusign", "outlook",
]


def _looks_like_lookalike_domain(domain):
    """
    very simple heuristic: take each known brand name and see if a
    "messed up" version of it shows up in the domain, for example
    swapping a letter for a digit, or the brand name plus extra words
    and a different ending.
    """
    domain_main = domain.split(".")[0]

    digit_swaps = {"0": "o", "1": "l", "1": "i", "3": "e", "5": "s", "@": "a"}
    cleaned = domain_main
    for digit, letter in digit_swaps.items():
        cleaned = cleaned.replace(digit, letter)

    for brand in _LOOKALIKE_BRANDS:
        if brand == domain_main:
            continue  # this is the real domain name itself, not a lookalike
        if brand in cleaned and brand != cleaned:
            return True
        # brand name with extra security/verify/login words attached
        if brand in domain_main and domain_main != brand:
            suspicious_words = ["secure", "verify", "login", "account", "update", "support", "alert"]
            for word in suspicious_words:
                if word in domain_main:
                    return True

    return False
