"""
explanation_engine.py
Builds a plain English explanation of why an email got its risk score,
plus a list of recommended actions. This is template based (no internet
call needed) so the app works fully offline, but it reads like a short
analyst write up.
"""

import config


def build_explanation(email_data, auth_result, url_result, attachment_result,
                       content_result, ml_result, score, level):

    lines = []

    sender = email_data.get("sender", "unknown sender")
    subject = email_data.get("subject", "(no subject)")

    lines.append(
        "This email from '" + sender + "' with subject '" + subject +
        "' received a risk score of " + str(score) + " out of 100, rated as " + level + " risk."
    )

    reason_parts = []

    if auth_result.get("spoof_flag"):
        reason_parts.append("signs of sender spoofing")

    if auth_result["spf"] in ("fail", "softfail") or auth_result["dkim"] in ("fail", "none") or auth_result["dmarc"] == "fail":
        reason_parts.append("failed or missing email authentication checks (SPF/DKIM/DMARC)")

    if url_result["suspicious_url_count"] > 0:
        reason_parts.append(str(url_result["suspicious_url_count"]) + " suspicious link(s)")

    if attachment_result["dangerous_count"] > 0:
        reason_parts.append(str(attachment_result["dangerous_count"]) + " risky attachment(s)")

    if content_result["score_hint"] > 10:
        reason_parts.append("language commonly used in phishing attempts (urgency, threats, or credential requests)")

    if ml_result["label"] == "phishing" and ml_result["confidence"] >= 0.6:
        reason_parts.append(
            "a machine learning model trained on phishing patterns flagged the text with "
            + str(round(ml_result["confidence"] * 100)) + "% confidence"
        )

    if reason_parts:
        lines.append("Main reasons for this score: " + ", ".join(reason_parts) + ".")
    else:
        lines.append("No strong phishing indicators were found, but always stay cautious with unexpected emails.")

    return " ".join(lines)


def build_recommendations(auth_result, url_result, attachment_result, content_result, ml_result, level):
    recs = []

    if level in ("High", "Critical"):
        recs.append("Do not click any links or open any attachments in this email.")
        recs.append("Report this email to your IT security team or use the 'report phishing' button in your mail client.")

    if auth_result.get("spoof_flag"):
        recs.append("Verify the sender's identity through a separate trusted channel (phone call, known contact) before responding.")

    if auth_result["spf"] in ("fail", "softfail") or auth_result["dkim"] in ("fail", "none") or auth_result["dmarc"] == "fail":
        recs.append("Treat the sending domain as unverified, this message did not pass standard email authentication checks.")

    if url_result["suspicious_url_count"] > 0:
        recs.append("Avoid clicking the links in this email, hover over them first or check the real destination before trusting them.")

    if attachment_result["dangerous_count"] > 0:
        recs.append("Do not open the attachments, especially executable or macro-enabled files, scan them with antivirus tools first if needed.")

    if content_result["score_hint"] > 10:
        recs.append("Be skeptical of urgent deadlines, threats, or requests for personal/financial information, legitimate companies rarely pressure you this way over email.")

    if level in ("Minimal", "Low"):
        recs.append("This email looks relatively safe, but still use normal caution with any unexpected requests.")

    if not recs:
        recs.append("No specific action needed, continue practicing normal email safety habits.")

    return recs
