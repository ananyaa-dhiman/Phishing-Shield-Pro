"""
report_export.py
Builds PDF and CSV reports from a list of analyzed email rows (the
same dicts that come out of the database).
"""

import csv
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)

import database
from logger_setup import log

RISK_COLOR_MAP = {
    "Minimal": colors.HexColor("#3fb950"),
    "Low": colors.HexColor("#58a6ff"),
    "Medium": colors.HexColor("#ffb020"),
    "High": colors.HexColor("#ff7a45"),
    "Critical": colors.HexColor("#ff4d4f"),
}


def export_to_csv(email_rows, output_path):
    try:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "ID", "File Name", "Sender", "Recipient", "Subject", "Date Sent",
                "SPF", "DKIM", "DMARC", "Spoof Flag", "URL Count", "Suspicious URLs",
                "Attachments", "Dangerous Attachments", "ML Confidence",
                "Risk Score", "Risk Level", "Analyzed At",
            ])
            for row in email_rows:
                writer.writerow([
                    row.get("id"), row.get("file_name"), row.get("sender"),
                    row.get("recipient"), row.get("subject"), row.get("date_sent"),
                    row.get("spf_result"), row.get("dkim_result"), row.get("dmarc_result"),
                    "Yes" if row.get("spoof_flag") else "No",
                    row.get("url_count"), row.get("suspicious_url_count"),
                    row.get("attachment_count"), row.get("dangerous_attachment_count"),
                    round(row.get("ml_confidence", 0) or 0, 2),
                    row.get("risk_score"), row.get("risk_level"), row.get("analyzed_at"),
                ])
        log.info("csv report saved to %s", output_path)
        return True
    except Exception as err:
        log.error("csv export failed: %s", err)
        return False


def export_to_pdf(email_rows, output_path):
    try:
        doc = SimpleDocTemplate(output_path, pagesize=letter,
                                 topMargin=40, bottomMargin=40, leftMargin=40, rightMargin=40)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "ReportTitle", parent=styles["Title"], textColor=colors.HexColor("#0d1117")
        )
        normal_style = styles["Normal"]
        small_style = ParagraphStyle("Small", parent=styles["Normal"], fontSize=8, leading=10)

        story = []

        story.append(Paragraph("Phishing Shield Pro - Analysis Report", title_style))
        story.append(Spacer(1, 6))
        now_text = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        story.append(Paragraph("Generated on " + now_text, normal_style))
        story.append(Spacer(1, 16))

        # summary section
        total = len(email_rows)
        dangerous = len([r for r in email_rows if r.get("risk_level") in ("High", "Critical")])
        avg_score = round(sum(r.get("risk_score", 0) for r in email_rows) / total, 1) if total else 0

        story.append(Paragraph("Summary", styles["Heading2"]))
        summary_table_data = [
            ["Total Emails Analyzed", str(total)],
            ["High / Critical Risk Emails", str(dangerous)],
            ["Average Risk Score", str(avg_score)],
        ]
        summary_table = Table(summary_table_data, colWidths=[250, 150])
        summary_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 20))

        # main table of all emails
        story.append(Paragraph("Email Details", styles["Heading2"]))
        story.append(Spacer(1, 6))

        table_data = [["File / Subject", "Sender", "Score", "Risk Level", "SPF/DKIM/DMARC"]]
        row_colors = []

        for row in email_rows:
            file_subject = Paragraph(
                "<b>" + _escape(row.get("file_name", "")) + "</b><br/>" + _escape(row.get("subject", "")),
                small_style,
            )
            sender_cell = Paragraph(_escape(row.get("sender", "")), small_style)
            auth_text = (row.get("spf_result", "") or "?") + " / " + (row.get("dkim_result", "") or "?") + " / " + (row.get("dmarc_result", "") or "?")

            table_data.append([
                file_subject,
                sender_cell,
                str(row.get("risk_score", 0)),
                row.get("risk_level", ""),
                auth_text,
            ])
            row_colors.append(RISK_COLOR_MAP.get(row.get("risk_level"), colors.white))

        main_table = Table(table_data, colWidths=[180, 130, 45, 65, 90], repeatRows=1)
        table_style_cmds = [
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d1117")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
        for i, row_color in enumerate(row_colors):
            table_style_cmds.append(("TEXTCOLOR", (3, i + 1), (3, i + 1), row_color))
            table_style_cmds.append(("FONTNAME", (3, i + 1), (3, i + 1), "Helvetica-Bold"))

        main_table.setStyle(TableStyle(table_style_cmds))
        story.append(main_table)

        # detail pages for dangerous emails, with full explanation/recommendation
        dangerous_rows = [r for r in email_rows if r.get("risk_level") in ("High", "Critical")]
        if dangerous_rows:
            story.append(PageBreak())
            story.append(Paragraph("High / Critical Risk Email Details", styles["Heading2"]))
            story.append(Spacer(1, 10))

            for row in dangerous_rows:
                story.append(Paragraph(_escape(row.get("subject", "(no subject)")), styles["Heading3"]))
                story.append(Paragraph("From: " + _escape(row.get("sender", "")), small_style))
                story.append(Paragraph(
                    "Risk Score: " + str(row.get("risk_score")) + " (" + row.get("risk_level", "") + ")",
                    small_style,
                ))
                story.append(Spacer(1, 4))
                story.append(Paragraph("<b>Explanation:</b> " + _escape(row.get("explanation_text", "")), normal_style))
                story.append(Spacer(1, 4))

                rec_text = row.get("recommendation_text", "")
                rec_html = rec_text.replace("\n", "<br/>")
                story.append(Paragraph("<b>Recommendations:</b><br/>" + _escape_keep_br(rec_html), normal_style))
                story.append(Spacer(1, 14))

        doc.build(story)
        log.info("pdf report saved to %s", output_path)
        return True

    except Exception as err:
        log.error("pdf export failed: %s", err)
        return False


def _escape(text):
    if text is None:
        return ""
    text = str(text)
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _escape_keep_br(html_text):
    """escape but keep the <br/> tags we inserted on purpose"""
    parts = html_text.split("<br/>")
    escaped_parts = [_escape(p) for p in parts]
    return "<br/>".join(escaped_parts)
