"""
ml_classifier.py
Loads the saved TF-IDF + Random Forest model and uses it to score an
email's text. If no model is saved yet, it trains one automatically
using the bundled sample dataset so the app works right out of the box.
"""

import os
import joblib
import config
from logger_setup import log

_model = None
_vectorizer = None


def _load_model_if_needed():
    global _model, _vectorizer

    if _model is not None and _vectorizer is not None:
        return

    if not os.path.exists(config.MODEL_FILE) or not os.path.exists(config.VECTOR_FILE):
        log.info("no saved ml model found, training a new one now")
        import train_model
        train_model.train_and_save_model()

    _model = joblib.load(config.MODEL_FILE)
    _vectorizer = joblib.load(config.VECTOR_FILE)
    log.info("ml model loaded")


def classify_email(email_data):
    """
    returns dict:
    {
        "label": "phishing" or "legit",
        "confidence": float 0 to 1, confidence in the phishing label,
        "indicators": [...]
    }
    """
    try:
        _load_model_if_needed()
    except Exception as err:
        log.error("could not load or train ml model: %s", err)
        return {"label": "unknown", "confidence": 0.0, "indicators": []}

    subject = email_data.get("subject", "") or ""
    body = email_data.get("body_text", "") or ""
    text = subject + " " + body

    if not text.strip():
        return {"label": "unknown", "confidence": 0.0, "indicators": []}

    try:
        text_vector = _vectorizer.transform([text])
        prediction = _model.predict(text_vector)[0]
        probabilities = _model.predict_proba(text_vector)[0]

        class_list = list(_model.classes_)
        phishing_index = class_list.index("phishing") if "phishing" in class_list else 0
        phishing_confidence = float(probabilities[phishing_index])

    except Exception as err:
        log.error("ml classify failed: %s", err)
        return {"label": "unknown", "confidence": 0.0, "indicators": []}

    indicators = []
    if prediction == "phishing" and phishing_confidence >= 0.6:
        indicators.append({
            "category": "ML Classifier",
            "description": "Machine learning text classifier flagged this email as phishing with "
                            + str(round(phishing_confidence * 100, 1)) + "% confidence.",
            "severity": "High" if phishing_confidence >= 0.8 else "Medium",
        })

    return {
        "label": prediction,
        "confidence": phishing_confidence,
        "indicators": indicators,
    }
