#!/usr/bin/env python3
"""
"What Drugs Does The Government Think You Do?"

A Python web app that inverts the UK Government's Crime Survey for
England and Wales drug usage data. Instead of reporting demographics
of drug users, it asks YOU demographic questions and tells you which
drugs the government would statistically expect you to use.

Data source: Drug misuse in England and Wales, year ending March 2025
Published by the Office for National Statistics (ONS)
"""

from flask import Flask, render_template, request, jsonify

from data import QUESTIONS
from predict import predict

app = Flask(__name__)


# ──────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html", questions=QUESTIONS)


@app.route("/predict", methods=["POST"])
def predict_route():
    answers = request.get_json()
    results = predict(answers)
    return jsonify(results)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
