"""
database.py
Handles all the SQLite stuff. Two tables:
  emails     -> one row per analyzed email
  indicators -> one row per red flag found in an email (many per email)
"""

import sqlite3
import datetime
import config
from logger_setup import log


def get_connection():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def setup_database():
    """create the tables if they do not already exist"""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT,
            file_path TEXT,
            sender TEXT,
            recipient TEXT,
            subject TEXT,
            date_sent TEXT,
            spf_result TEXT,
            dkim_result TEXT,
            dmarc_result TEXT,
            spoof_flag INTEGER,
            url_count INTEGER,
            suspicious_url_count INTEGER,
            attachment_count INTEGER,
            dangerous_attachment_count INTEGER,
            ml_confidence REAL,
            risk_score INTEGER,
            risk_level TEXT,
            explanation_text TEXT,
            recommendation_text TEXT,
            analyzed_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id INTEGER,
            category TEXT,
            description TEXT,
            severity TEXT,
            FOREIGN KEY (email_id) REFERENCES emails (id)
        )
    """)

    conn.commit()
    conn.close()
    log.info("database ready at %s", config.DB_PATH)


def insert_email(data, indicator_list):
    """
    data is a dict with all the email columns.
    indicator_list is a list of dicts like {"category":..,"description":..,"severity":..}
    returns the new email id
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO emails (
            file_name, file_path, sender, recipient, subject, date_sent,
            spf_result, dkim_result, dmarc_result, spoof_flag,
            url_count, suspicious_url_count, attachment_count, dangerous_attachment_count,
            ml_confidence, risk_score, risk_level, explanation_text, recommendation_text, analyzed_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        data.get("file_name"),
        data.get("file_path"),
        data.get("sender"),
        data.get("recipient"),
        data.get("subject"),
        data.get("date_sent"),
        data.get("spf_result"),
        data.get("dkim_result"),
        data.get("dmarc_result"),
        1 if data.get("spoof_flag") else 0,
        data.get("url_count", 0),
        data.get("suspicious_url_count", 0),
        data.get("attachment_count", 0),
        data.get("dangerous_attachment_count", 0),
        data.get("ml_confidence", 0.0),
        data.get("risk_score", 0),
        data.get("risk_level", "Unknown"),
        data.get("explanation_text", ""),
        data.get("recommendation_text", ""),
        datetime.datetime.now().isoformat(timespec="seconds"),
    ))

    email_id = cur.lastrowid

    for item in indicator_list:
        cur.execute("""
            INSERT INTO indicators (email_id, category, description, severity)
            VALUES (?,?,?,?)
        """, (email_id, item.get("category"), item.get("description"), item.get("severity")))

    conn.commit()
    conn.close()
    return email_id


def get_all_emails():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM emails ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_email_by_id(email_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM emails WHERE id = ?", (email_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_indicators_for_email(email_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM indicators WHERE email_id = ?", (email_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def search_emails(keyword="", risk_level="All"):
    """used by the results tab search/filter box"""
    conn = get_connection()
    cur = conn.cursor()

    query = "SELECT * FROM emails WHERE 1=1"
    params = []

    if keyword:
        query += " AND (sender LIKE ? OR subject LIKE ? OR file_name LIKE ?)"
        like_word = "%" + keyword + "%"
        params.extend([like_word, like_word, like_word])

    if risk_level and risk_level != "All":
        query += " AND risk_level = ?"
        params.append(risk_level)

    query += " ORDER BY id DESC"

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_stats():
    """numbers used on the dashboard cards"""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) AS total FROM emails")
    total = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) AS dangerous FROM emails WHERE risk_level IN ('High','Critical')")
    dangerous = cur.fetchone()["dangerous"]

    cur.execute("SELECT AVG(risk_score) AS avg_score FROM emails")
    avg_row = cur.fetchone()
    avg_score = avg_row["avg_score"] if avg_row["avg_score"] is not None else 0

    cur.execute("SELECT COUNT(*) AS spoofed FROM emails WHERE spoof_flag = 1")
    spoofed = cur.fetchone()["spoofed"]

    conn.close()
    return {
        "total": total,
        "dangerous": dangerous,
        "avg_score": round(avg_score, 1),
        "spoofed": spoofed,
    }


def get_risk_distribution():
    """count of emails in each risk band, used for the pie chart"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT risk_level, COUNT(*) AS cnt FROM emails GROUP BY risk_level")
    rows = cur.fetchall()
    conn.close()
    result = {}
    for row in rows:
        result[row["risk_level"]] = row["cnt"]
    return result


def get_top_indicators(limit=8):
    """most common red flags across all analyzed emails, used for bar chart"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT category, COUNT(*) AS cnt
        FROM indicators
        GROUP BY category
        ORDER BY cnt DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return [(row["category"], row["cnt"]) for row in rows]


def get_dangerous_emails(limit=10):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM emails
        WHERE risk_level IN ('High','Critical')
        ORDER BY risk_score DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_timeline():
    """count of emails analyzed per day, used for the trend chart"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT substr(analyzed_at,1,10) AS day, COUNT(*) AS cnt
        FROM emails
        GROUP BY day
        ORDER BY day ASC
    """)
    rows = cur.fetchall()
    conn.close()
    return [(row["day"], row["cnt"]) for row in rows]


def delete_email(email_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM indicators WHERE email_id = ?", (email_id,))
    cur.execute("DELETE FROM emails WHERE id = ?", (email_id,))
    conn.commit()
    conn.close()


def clear_all_data():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM indicators")
    cur.execute("DELETE FROM emails")
    conn.commit()
    conn.close()
    log.info("all data cleared from database")
