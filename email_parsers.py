"""
email_parsers.py
Takes in a file path and returns a list of "email_data" dicts.
A list is returned (not a single dict) because one file like .mbox or .zip
can contain many emails inside it.

email_data dict looks like this:
{
    "file_name": "invoice.eml",
    "sender": "boss@company.com",
    "recipient": "me@company.com",
    "subject": "...",
    "date_sent": "...",
    "body_text": "...",
    "body_html": "...",
    "headers": {...},          raw header dict, lower case keys
    "attachments": [{"name":.., "size":.., "data": bytes}],
}
"""

import os
import email
import email.policy
import csv
import mailbox
import zipfile
import tempfile
from logger_setup import log

try:
    import extract_msg
    HAVE_EXTRACT_MSG = True
except ImportError:
    HAVE_EXTRACT_MSG = False


def parse_any_file(file_path):
    """main entry point, looks at the extension and calls the right parser"""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".eml":
        return [parse_eml_file(file_path)]
    elif ext == ".msg":
        return [parse_msg_file(file_path)]
    elif ext == ".txt":
        return [parse_txt_file(file_path)]
    elif ext == ".csv":
        return parse_csv_file(file_path)
    elif ext == ".mbox":
        return parse_mbox_file(file_path)
    elif ext == ".zip":
        return parse_zip_file(file_path)
    else:
        log.warning("unsupported file type: %s", file_path)
        return []


def _empty_email_data(file_name):
    return {
        "file_name": file_name,
        "sender": "",
        "recipient": "",
        "subject": "",
        "date_sent": "",
        "body_text": "",
        "body_html": "",
        "headers": {},
        "attachments": [],
    }


def _headers_to_dict(msg_obj):
    headers = {}
    for key in msg_obj.keys():
        # there can be repeated header names, keep the last one, good enough
        headers[key.lower()] = msg_obj.get(key, "")
    return headers


def _get_body_and_attachments(msg_obj):
    body_text = ""
    body_html = ""
    attachments = []

    if msg_obj.is_multipart():
        for part in msg_obj.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition") or "")

            if "attachment" in disposition or part.get_filename():
                file_name = part.get_filename() or "unnamed_attachment"
                try:
                    payload = part.get_payload(decode=True) or b""
                except Exception:
                    payload = b""
                attachments.append({
                    "name": file_name,
                    "size": len(payload),
                    "data": payload,
                })
            elif content_type == "text/plain":
                try:
                    body_text += part.get_payload(decode=True).decode(
                        part.get_content_charset() or "utf-8", errors="ignore"
                    )
                except Exception:
                    pass
            elif content_type == "text/html":
                try:
                    body_html += part.get_payload(decode=True).decode(
                        part.get_content_charset() or "utf-8", errors="ignore"
                    )
                except Exception:
                    pass
    else:
        content_type = msg_obj.get_content_type()
        try:
            payload = msg_obj.get_payload(decode=True)
            decoded = payload.decode(msg_obj.get_content_charset() or "utf-8", errors="ignore") if payload else ""
        except Exception:
            decoded = ""

        if content_type == "text/html":
            body_html = decoded
        else:
            body_text = decoded

    return body_text, body_html, attachments


def parse_eml_file(file_path):
    file_name = os.path.basename(file_path)
    try:
        with open(file_path, "rb") as f:
            msg_obj = email.message_from_binary_file(f, policy=email.policy.default)
        return _build_data_from_msg(msg_obj, file_name)
    except Exception as err:
        log.error("failed to parse eml file %s : %s", file_path, err)
        return _empty_email_data(file_name)


def _build_data_from_msg(msg_obj, file_name):
    data = _empty_email_data(file_name)
    data["sender"] = str(msg_obj.get("From", ""))
    data["recipient"] = str(msg_obj.get("To", ""))
    data["subject"] = str(msg_obj.get("Subject", ""))
    data["date_sent"] = str(msg_obj.get("Date", ""))
    data["headers"] = _headers_to_dict(msg_obj)

    body_text, body_html, attachments = _get_body_and_attachments(msg_obj)
    data["body_text"] = body_text
    data["body_html"] = body_html
    data["attachments"] = attachments
    return data


def parse_msg_file(file_path):
    """outlook .msg files need the extract_msg library"""
    file_name = os.path.basename(file_path)
    data = _empty_email_data(file_name)

    if not HAVE_EXTRACT_MSG:
        log.warning("extract_msg library not installed, cannot read %s", file_path)
        return data

    try:
        msg_obj = extract_msg.Message(file_path)
        data["sender"] = msg_obj.sender or ""
        data["recipient"] = msg_obj.to or ""
        data["subject"] = msg_obj.subject or ""
        data["date_sent"] = str(msg_obj.date or "")
        data["body_text"] = msg_obj.body or ""
        data["body_html"] = getattr(msg_obj, "htmlBody", "") or ""

        # headers, extract_msg gives a header object similar to email module
        headers = {}
        if msg_obj.header:
            for key in msg_obj.header.keys():
                headers[key.lower()] = msg_obj.header.get(key, "")
        data["headers"] = headers

        attachments = []
        for att in msg_obj.attachments:
            try:
                att_data = att.data
            except Exception:
                att_data = b""
            attachments.append({
                "name": att.longFilename or att.shortFilename or "unnamed_attachment",
                "size": len(att_data) if att_data else 0,
                "data": att_data if att_data else b"",
            })
        data["attachments"] = attachments
        msg_obj.close()
    except Exception as err:
        log.error("failed to parse msg file %s : %s", file_path, err)

    return data


def parse_txt_file(file_path):
    """treat a .txt file as a raw email (headers + body pasted as text)"""
    file_name = os.path.basename(file_path)
    try:
        with open(file_path, "rb") as f:
            raw_bytes = f.read()
        msg_obj = email.message_from_bytes(raw_bytes, policy=email.policy.default)

        # if it does not look like a real email (no From/Subject header)
        # just treat the whole file as body text
        if not msg_obj.get("From") and not msg_obj.get("Subject"):
            data = _empty_email_data(file_name)
            data["body_text"] = raw_bytes.decode("utf-8", errors="ignore")
            return data

        return _build_data_from_msg(msg_obj, file_name)
    except Exception as err:
        log.error("failed to parse txt file %s : %s", file_path, err)
        return _empty_email_data(file_name)


def parse_csv_file(file_path):
    """
    a csv export of emails, expected columns (not case sensitive):
    sender, recipient, subject, date, body
    any missing column is just left blank
    """
    file_name = os.path.basename(file_path)
    results = []

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            row_num = 0
            for row in reader:
                row_num += 1
                lower_row = {k.lower().strip(): v for k, v in row.items() if k}

                data = _empty_email_data(file_name + " (row " + str(row_num) + ")")
                data["sender"] = lower_row.get("sender", lower_row.get("from", ""))
                data["recipient"] = lower_row.get("recipient", lower_row.get("to", ""))
                data["subject"] = lower_row.get("subject", "")
                data["date_sent"] = lower_row.get("date", "")
                data["body_text"] = lower_row.get("body", lower_row.get("message", ""))
                results.append(data)
    except Exception as err:
        log.error("failed to parse csv file %s : %s", file_path, err)

    return results


def parse_mbox_file(file_path):
    file_name = os.path.basename(file_path)
    results = []

    try:
        box = mailbox.mbox(file_path)
        index = 0
        for msg_obj in box:
            index += 1
            sub_name = file_name + " (msg " + str(index) + ")"
            results.append(_build_data_from_msg(msg_obj, sub_name))
        box.close()
    except Exception as err:
        log.error("failed to parse mbox file %s : %s", file_path, err)

    return results


def parse_zip_file(file_path):
    """unzip into a temp folder and parse every supported file found inside"""
    file_name = os.path.basename(file_path)
    results = []

    try:
        with tempfile.TemporaryDirectory() as temp_folder:
            with zipfile.ZipFile(file_path, "r") as zip_obj:
                zip_obj.extractall(temp_folder)

            for root, dirs, files in os.walk(temp_folder):
                for inner_file in files:
                    inner_ext = os.path.splitext(inner_file)[1].lower()
                    if inner_ext in [".eml", ".msg", ".txt", ".csv", ".mbox"]:
                        inner_path = os.path.join(root, inner_file)
                        inner_results = parse_any_file(inner_path)
                        for item in inner_results:
                            item["file_name"] = file_name + " -> " + inner_file
                        results.extend(inner_results)
    except Exception as err:
        log.error("failed to parse zip file %s : %s", file_path, err)

    return results
