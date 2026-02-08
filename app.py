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

from flask import Flask, render_template, request, redirect, url_for

from data import QUESTIONS
from predict import predict

app = Flask(__name__)

DRUG_COMMENTS = {
    "Cannabis": "The perennial favourite. It\u2019s been number one since records began in 1995.",
    "Powder cocaine": "Friday night\u2019s open secret \u2014 popularity peaks in the 25\u201329 bracket.",
    "Ecstasy": "Still going strong three decades after the Second Summer of Love.",
    "Hallucinogens": "Magic mushrooms and LSD \u2014 nature and chemistry\u2019s mind-benders.",
    "Ketamine": "From veterinary anaesthetic to nightlife staple in a single generation.",
    "Amphetamines": "Speed: quietly persistent since the Northern Soul all-nighters.",
}


# ──────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html", questions=QUESTIONS)


@app.route("/predict", methods=["POST"])
def predict_route():
    answers = {}
    for q in QUESTIONS:
        value = request.form.get(q["id"])
        if value:
            answers[q["id"]] = value

    if not answers:
        return redirect(url_for("index"))

    results = predict(answers)

    # Compute "any drug" estimate (same logic previously in JS)
    top_three_sum = sum(d["rate"] for d in results[:3])
    any_drug = min(top_three_sum * 0.85, 95.0)

    if any_drug > 20:
        verdict = "The government is fairly confident you\u2019re partying."
    elif any_drug > 12:
        verdict = "A statistical side-eye from Whitehall."
    elif any_drug > 7:
        verdict = "Statistically average \u2014 you blend into the crowd."
    elif any_drug > 3:
        verdict = "Statistically squeaky-clean, but not implausibly so."
    else:
        verdict = "The Home Office considers you an absolute saint."

    max_rate = results[0]["rate"] if results else 0

    return render_template(
        "results.html",
        results=results,
        any_drug=any_drug,
        verdict=verdict,
        max_rate=max_rate,
        drug_comments=DRUG_COMMENTS,
        answered=len(answers),
        total=len(QUESTIONS),
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
