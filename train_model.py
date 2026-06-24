"""
train_model.py
Trains the TF-IDF + Random Forest phishing text classifier and saves
it to disk. Run this once (or whenever you have new training data).
The main app will call this automatically on first run if no saved
model is found.
"""

import os
import csv
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

import config
from logger_setup import log
import make_train_data


def load_training_data():
    if not os.path.exists(config.TRAIN_DATA_FILE):
        log.info("no training data file found, generating a sample one")
        make_train_data.build_dataset()

    texts = []
    labels = []

    with open(config.TRAIN_DATA_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            texts.append(row["text"])
            labels.append(row["label"])

    return texts, labels


def train_and_save_model():
    config.make_folders()

    texts, labels = load_training_data()

    x_train, x_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42
    )

    vectorizer = TfidfVectorizer(
        max_features=2000,
        stop_words="english",
        ngram_range=(1, 2),
    )
    x_train_vec = vectorizer.fit_transform(x_train)
    x_test_vec = vectorizer.transform(x_test)

    model = RandomForestClassifier(
        n_estimators=150,
        max_depth=20,
        random_state=42,
    )
    model.fit(x_train_vec, y_train)

    predictions = model.predict(x_test_vec)
    accuracy = accuracy_score(y_test, predictions)
    log.info("model trained, test accuracy = %.2f", accuracy)
    print("test accuracy:", round(accuracy, 3))

    joblib.dump(model, config.MODEL_FILE)
    joblib.dump(vectorizer, config.VECTOR_FILE)
    log.info("model saved to %s", config.MODEL_FILE)

    return accuracy


if __name__ == "__main__":
    train_and_save_model()
