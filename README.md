<<<<<<< HEAD
# Phishing Shield Pro

A cross-platform desktop tool that scans email files for phishing red flags
and gives every email a 0-100 risk score with a plain English explanation
and recommended actions.

## Features

- Dark, cybersecurity-themed GUI (tkinter) with drag-and-drop file upload
- Reads `.eml`, `.msg`, `.txt`, `.csv`, `.mbox`, and `.zip` (zip is unpacked
  and every supported file inside it is analyzed too)
- SPF / DKIM / DMARC header checks
- Sender spoofing detection (display name mismatch, lookalike domains,
  Reply-To / Return-Path mismatch)
- URL analysis (IP-based links, URL shorteners, hidden destinations,
  text/link mismatch, too many links)
- Attachment analysis (dangerous extensions, macro-enabled office files,
  double extension tricks, archive files)
- Content analysis (urgency language, threats, credential requests,
  generic greetings, money/gift card scams)
- Machine learning text classifier (TF-IDF + Random Forest) with a
  confidence score
- One combined 0-100 risk score, mapped to Minimal / Low / Medium / High /
  Critical
- Auto generated explanation and recommended actions for every email
- Dashboard tab with stat cards and charts (risk distribution, top
  indicator categories, analysis timeline)
- Results tab with search box, risk level filter, and a detail view per
  email
- Export results to PDF or CSV
- All results saved in a local SQLite database (`phishing_shield.db`)
- Logging to `logs/app.log`

## Requirements

- Python 3.9 or newer
- Windows or Linux (mac should also work, not officially tested)

On Linux, tkinter is sometimes a separate OS package, not just a pip
package:

```bash
sudo apt-get install python3-tk
```

On Windows, tkinter already ships with the normal python.org installer, so
nothing extra is needed there.

## Setup

```bash
# 1. (optional) create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. install dependencies
pip install -r requirements.txt

# 3. run the app
python main.py
```

The first time you run it, the app will automatically:
- create the `logs/`, `model_files/`, and `exports/` folders
- create the SQLite database and tables
- generate a small sample training set (`train_data.csv`) and train the
  ML classifier, saving it into `model_files/`

This means it works right out of the box with no extra setup. If you want
to train the classifier on your own labeled data, just replace
`train_data.csv` (columns: `text,label`, label is `phishing` or `legit`)
and delete the files inside `model_files/`, then run:

```bash
python train_model.py
```

## Project layout

```
main.py                 entry point, starts the GUI
config.py                constants, colors, paths
database.py              SQLite setup and queries
logger_setup.py           logging setup

email_parsers.py          reads .eml/.msg/.txt/.csv/.mbox/.zip files
auth_checker.py            SPF/DKIM/DMARC + spoofing checks
url_analyzer.py             link/URL analysis
attachment_analyzer.py       attachment risk checks
content_analyzer.py           subject/body keyword analysis
ml_classifier.py               loads/uses the trained ML model
risk_engine.py                  combines everything into one 0-100 score
explanation_engine.py            builds the explanation + recommendations
analysis_runner.py                glue code that runs the full pipeline
report_export.py                   PDF / CSV report builder

train_model.py             trains the TF-IDF + Random Forest model
make_train_data.py          builds a sample training csv if none exists

gui_main.py                main window, tabs
gui_theme.py                 dark theme setup for ttk widgets
gui_analyze.py                Analyze tab (drag/drop, progress bar)
gui_results.py                 Results tab (search, filter, detail view)
gui_dashboard.py                 Dashboard tab (stat cards, charts)
gui_charts.py                     matplotlib chart helpers

sample_emails/               a couple of test .eml files
```

## Notes on the authentication checks

SPF/DKIM/DMARC results are read from the `Authentication-Results` and
`Received-SPF` headers that the *receiving* mail server already stamped
onto the message. This is the standard way to check authentication for an
email you already have saved to disk, since the original sending server
is no longer reachable for a fresh check by the time you're reviewing a
saved file.

## Disclaimer

This tool is meant to help spot common phishing patterns and speed up
manual review, it is a heuristic + ML helper, not a guarantee. Always use
your own judgement and your organization's official reporting process for
suspicious email.
=======
# Phishing-Shield-Pro
>>>>>>> 53c7a1fb304483a587f54d52cdfc1de188a50458
