"""
url_analyzer.py
Pulls links out of the email body (plain text and html) and checks
each one for common phishing tricks.
"""

import re
from logger_setup import log

URL_PATTERN = re.compile(r"https?://[^\s\"'<>\)\]]+", re.IGNORECASE)
HREF_PATTERN = re.compile(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)

URL_SHORTENERS = [
    "bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly", "is.gd",
    "buff.ly", "adf.ly", "shorte.st", "cutt.ly", "rebrand.ly",
]

SUSPICIOUS_KEYWORDS_IN_URL = [
    "login", "verify", "secure", "account", "update", "confirm",
    "signin", "password", "billing", "suspend",
]


def analyze_urls(email_data):
    """
    returns dict:
    {
        "url_count": int,
        "suspicious_url_count": int,
        "url_list": [...],
        "indicators": [...]
    }
    """
    body_text = email_data.get("body_text", "") or ""
    body_html = email_data.get("body_html", "") or ""

    indicators = []

    urls_from_text = URL_PATTERN.findall(body_text)
    urls_from_html = URL_PATTERN.findall(body_html)

    all_urls = list(set(urls_from_text + urls_from_html))

    suspicious_count = 0
    checked_urls = []

    for url in all_urls:
        problems = _check_single_url(url)
        if problems:
            suspicious_count += 1
        checked_urls.append({"url": url, "problems": problems})

    # check for mismatched link text vs actual destination (the "click here" trick)
    mismatch_indicators = _check_link_text_mismatch(body_html)
    indicators.extend(mismatch_indicators)

    if len(all_urls) > 8:
        indicators.append(_make_indicator(
            "URL Analysis",
            "Email contains an unusually high number of links (" + str(len(all_urls)) + "), often seen in spam and phishing blasts.",
            "Low",
        ))

    for item in checked_urls:
        for problem in item["problems"]:
            indicators.append(_make_indicator("URL Analysis", problem, "Medium"))

    if suspicious_count >= 3:
        indicators.append(_make_indicator(
            "URL Analysis",
            "Multiple suspicious links (" + str(suspicious_count) + ") found in the same email.",
            "High",
        ))

    return {
        "url_count": len(all_urls),
        "suspicious_url_count": suspicious_count,
        "url_list": checked_urls,
        "indicators": indicators,
    }


def _check_single_url(url):
    """returns a list of short text problems found for this one url"""
    problems = []
    lower_url = url.lower()

    domain = _extract_domain(lower_url)

    # 1) ip address instead of a normal domain name
    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", domain):
        problems.append("Link points directly to a raw IP address (" + domain + ") instead of a domain name.")

    # 2) known url shortener
    for shortener in URL_SHORTENERS:
        if shortener in domain:
            problems.append("Link uses a URL shortener (" + shortener + ") which can hide the real destination.")
            break

    # 3) suspicious keyword combined with a non https link
    if not lower_url.startswith("https://"):
        for word in SUSPICIOUS_KEYWORDS_IN_URL:
            if word in lower_url:
                problems.append("Insecure (non-HTTPS) link containing the sensitive word '" + word + "'.")
                break

    # 4) too many subdomains, a common way to hide the real domain
    # e.g. paypal.com.security-check.ru -> real domain is security-check.ru
    if domain.count(".") >= 3:
        problems.append("Link domain has an unusually long chain of subdomains (" + domain + "), which can be used to disguise the true destination.")

    # 5) domain contains @ symbol trick (browser ignores everything before @)
    if "@" in url:
        problems.append("Link contains an '@' symbol, a known trick to hide the real destination website.")

    return problems


def _extract_domain(url):
    match = re.search(r"https?://([^/]+)", url)
    if match:
        return match.group(1)
    return url


def _check_link_text_mismatch(body_html):
    """
    looks for <a href="realsite.com">paypal.com</a> style tricks where the
    text shown does not match where the link actually goes
    """
    indicators = []
    if not body_html:
        return indicators

    matches = HREF_PATTERN.findall(body_html)
    count_found = 0

    for href, link_text in matches:
        clean_text = re.sub("<[^>]+>", "", link_text).strip()

        # if the visible text itself looks like a url, compare domains
        text_looks_like_url = re.search(r"[a-zA-Z0-9-]+\.[a-zA-Z]{2,}", clean_text)
        if text_looks_like_url:
            href_domain = _extract_domain(href.lower())
            text_domain_match = re.search(r"([a-zA-Z0-9-]+\.[a-zA-Z]{2,})", clean_text.lower())
            text_domain = text_domain_match.group(1) if text_domain_match else ""

            if text_domain and href_domain and text_domain not in href_domain:
                count_found += 1

    if count_found > 0:
        indicators.append(_make_indicator(
            "URL Analysis",
            "Found " + str(count_found) + " link(s) where the displayed text shows a different website than where the link actually goes.",
            "Critical",
        ))

    return indicators


def _make_indicator(category, description, severity):
    return {"category": category, "description": description, "severity": severity}
