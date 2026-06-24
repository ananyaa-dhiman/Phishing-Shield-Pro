"""
analysis_runner.py
The main "glue" file. Given a file path, this runs the full pipeline:
parse -> auth check -> url check -> attachment check -> content check
-> ml classify -> risk score -> explanation -> save to database.

Returns a list of result dicts (one per email found in the file, since
a single .zip or .mbox can contain many emails).
"""

import email_parsers
import auth_checker
import url_analyzer
import attachment_analyzer
import content_analyzer
import ml_classifier
import risk_engine
import explanation_engine
import database
from logger_setup import log


def analyze_file(file_path, progress_callback=None):
    """
    progress_callback, if given, is called with a short status string,
    used by the gui to update the progress label
    """
    results = []

    if progress_callback:
        progress_callback("Reading file...")

    try:
        email_list = email_parsers.parse_any_file(file_path)
    except Exception as err:
        log.error("could not parse %s : %s", file_path, err)
        return results

    total = len(email_list)
    if total == 0:
        log.warning("no emails found inside %s", file_path)
        return results

    for index, email_data in enumerate(email_list):
        email_data["file_path"] = file_path

        if progress_callback:
            progress_callback("Analyzing " + str(index + 1) + " of " + str(total) + "...")

        result = analyze_single_email(email_data)
        results.append(result)

    return results


def analyze_single_email(email_data):
    """runs every analyzer on one already-parsed email_data dict"""

    auth_result = auth_checker.check_authentication(email_data)
    url_result = url_analyzer.analyze_urls(email_data)
    attachment_result = attachment_analyzer.analyze_attachments(email_data)
    content_result = content_analyzer.analyze_content(email_data)
    ml_result = ml_classifier.classify_email(email_data)

    score, level = risk_engine.calculate_risk(
        auth_result, url_result, attachment_result, content_result, ml_result
    )

    explanation = explanation_engine.build_explanation(
        email_data, auth_result, url_result, attachment_result, content_result, ml_result, score, level
    )
    recommendations = explanation_engine.build_recommendations(
        auth_result, url_result, attachment_result, content_result, ml_result, level
    )
    recommendation_text = "\n".join("- " + r for r in recommendations)

    all_indicators = risk_engine.combine_indicators(
        auth_result["indicators"],
        url_result["indicators"],
        attachment_result["indicators"],
        content_result["indicators"],
        ml_result["indicators"],
    )

    db_row = {
        "file_name": email_data.get("file_name", ""),
        "file_path": email_data.get("file_path", ""),
        "sender": email_data.get("sender", ""),
        "recipient": email_data.get("recipient", ""),
        "subject": email_data.get("subject", ""),
        "date_sent": email_data.get("date_sent", ""),
        "spf_result": auth_result["spf"],
        "dkim_result": auth_result["dkim"],
        "dmarc_result": auth_result["dmarc"],
        "spoof_flag": auth_result["spoof_flag"],
        "url_count": url_result["url_count"],
        "suspicious_url_count": url_result["suspicious_url_count"],
        "attachment_count": attachment_result["attachment_count"],
        "dangerous_attachment_count": attachment_result["dangerous_count"],
        "ml_confidence": ml_result["confidence"],
        "risk_score": score,
        "risk_level": level,
        "explanation_text": explanation,
        "recommendation_text": recommendation_text,
    }

    email_id = database.insert_email(db_row, all_indicators)
    db_row["id"] = email_id
    db_row["indicators"] = all_indicators

    log.info("analyzed %s -> score %s (%s)", db_row["file_name"], score, level)

    return db_row
