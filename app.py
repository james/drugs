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

import json
import math
from flask import Flask, render_template_string, request, jsonify

# ──────────────────────────────────────────────────────────────────
# Load extracted CSEW data
# ──────────────────────────────────────────────────────────────────

with open("csew_data.json") as f:
    CSEW = json.load(f)

BASELINE = CSEW["baseline"]
DRUG_CLASSES = CSEW["drug_classes"]
QUESTIONS = CSEW["questions"]
DRUGS = list(BASELINE.keys())

app = Flask(__name__)


# ──────────────────────────────────────────────────────────────────
# Prediction engine
# ──────────────────────────────────────────────────────────────────

def predict(answers: dict) -> list[dict]:
    """
    For each drug, compute an adjusted prevalence rate by combining
    the demographic-specific rates from each answered question.

    Method: geometric mean of ratios.

    For each question the user answered, we know the prevalence rate
    for their specific demographic group. We express this as a ratio
    relative to the baseline rate. Then we combine all these ratios
    using a geometric mean, and multiply by the baseline. This avoids
    the product of many independent multipliers blowing up to absurd
    values, while still reflecting the direction and rough magnitude
    of each factor.
    """
    results = []

    for drug in DRUGS:
        base = BASELINE[drug]
        if base <= 0:
            results.append({"drug": drug, "rate": 0.0})
            continue

        log_ratios = []

        for q in QUESTIONS:
            qid = q["id"]
            if qid not in answers:
                continue
            chosen = answers[qid]
            if chosen not in q["options"]:
                continue
            demo_rate = q["options"][chosen].get(drug, 0.0)
            if demo_rate <= 0:
                # If zero in survey data, use a small floor (0.01%)
                # rather than letting log blow up
                demo_rate = 0.01
            ratio = demo_rate / base
            log_ratios.append(math.log(ratio))

        if log_ratios:
            # Geometric mean of the ratios
            geo_mean_log = sum(log_ratios) / len(log_ratios)
            adjusted = base * math.exp(geo_mean_log)
        else:
            adjusted = base

        # Cap at 95%
        adjusted = min(adjusted, 95.0)
        adjusted = max(adjusted, 0.0)

        results.append({
            "drug": drug,
            "rate": round(adjusted, 2),
            "classification": DRUG_CLASSES.get(drug, ""),
        })

    results.sort(key=lambda x: x["rate"], reverse=True)
    return results


# ──────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, questions=QUESTIONS)


@app.route("/predict", methods=["POST"])
def predict_route():
    answers = request.get_json()
    results = predict(answers)
    return jsonify(results)


# ──────────────────────────────────────────────────────────────────
# HTML Template (single file, unobtrusive JS, no React)
# ──────────────────────────────────────────────────────────────────

HTML_TEMPLATE = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>What Drugs Does The Government Think You Do?</title>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,500;0,9..40,700;1,9..40,400&display=swap" rel="stylesheet">
<style>
  :root {
    --ink: #1a1a18;
    --paper: #f5f0e8;
    --paper-dark: #e8e0d0;
    --red: #c23616;
    --red-light: #e8513a;
    --blue: #2f3640;
    --gold: #b8860b;
    --green: #27613b;
    --muted: #7f8c8d;
    --class-a: #c23616;
    --class-b: #b8860b;
    --class-c: #2f6640;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: 'DM Sans', Georgia, serif;
    background: var(--paper);
    color: var(--ink);
    min-height: 100vh;
    line-height: 1.5;
  }

  /* ── Newspaper masthead ── */
  .masthead {
    text-align: center;
    padding: 2.5rem 1rem 1.5rem;
    border-bottom: 4px double var(--ink);
    max-width: 800px;
    margin: 0 auto;
  }
  .masthead-rule {
    display: block;
    width: 100%;
    height: 2px;
    background: var(--ink);
    margin-bottom: 0.75rem;
  }
  .masthead h1 {
    font-family: 'Instrument Serif', Georgia, serif;
    font-weight: 400;
    font-size: clamp(2rem, 5.5vw, 3.4rem);
    line-height: 1.1;
    letter-spacing: -0.01em;
    margin-bottom: 0.4rem;
  }
  .masthead .subtitle {
    font-size: 0.85rem;
    font-weight: 300;
    color: var(--muted);
    letter-spacing: 0.15em;
    text-transform: uppercase;
  }
  .masthead .edition {
    font-family: 'Instrument Serif', Georgia, serif;
    font-style: italic;
    font-size: 0.95rem;
    color: var(--muted);
    margin-top: 0.3rem;
  }

  /* ── Main container ── */
  .container {
    max-width: 720px;
    margin: 0 auto;
    padding: 1.5rem 1.5rem 4rem;
  }

  .intro {
    font-size: 1.05rem;
    line-height: 1.7;
    margin-bottom: 2rem;
    padding: 1.25rem 0;
    border-bottom: 1px solid var(--paper-dark);
    font-weight: 300;
  }
  .intro strong {
    font-weight: 500;
  }

  /* ── Question cards ── */
  .question-card {
    margin-bottom: 1.5rem;
    opacity: 0;
    transform: translateY(12px);
    transition: opacity 0.4s ease, transform 0.4s ease;
  }
  .question-card.visible {
    opacity: 1;
    transform: translateY(0);
  }
  .question-card.answered {
    opacity: 0.55;
    transform: scale(0.98);
    transition: opacity 0.5s ease 0.2s, transform 0.5s ease 0.2s;
  }
  .question-card.answered:hover {
    opacity: 0.85;
  }

  .q-number {
    font-family: 'Instrument Serif', Georgia, serif;
    font-size: 2.5rem;
    font-weight: 400;
    color: var(--paper-dark);
    line-height: 1;
    float: left;
    margin-right: 0.75rem;
    margin-top: -0.15rem;
  }

  .q-text {
    font-family: 'Instrument Serif', Georgia, serif;
    font-size: 1.3rem;
    font-weight: 400;
    margin-bottom: 0.75rem;
    min-height: 2.5rem;
    display: flex;
    align-items: center;
  }

  .options {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    clear: both;
  }

  .option-btn {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.85rem;
    font-weight: 500;
    padding: 0.5rem 1rem;
    border: 1.5px solid var(--ink);
    border-radius: 2px;
    background: transparent;
    color: var(--ink);
    cursor: pointer;
    transition: all 0.15s ease;
    position: relative;
  }
  .option-btn:hover {
    background: var(--ink);
    color: var(--paper);
  }
  .option-btn.selected {
    background: var(--ink);
    color: var(--paper);
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  }

  /* ── Progress ── */
  .progress-track {
    position: sticky;
    top: 0;
    z-index: 100;
    background: var(--paper);
    padding: 0.5rem 0;
    border-bottom: 1px solid var(--paper-dark);
  }
  .progress-bar-wrap {
    max-width: 720px;
    margin: 0 auto;
    padding: 0 1.5rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }
  .progress-bar {
    flex: 1;
    height: 3px;
    background: var(--paper-dark);
    border-radius: 2px;
    overflow: hidden;
  }
  .progress-fill {
    height: 100%;
    background: var(--ink);
    width: 0%;
    transition: width 0.4s ease;
  }
  .progress-text {
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--muted);
    white-space: nowrap;
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }

  /* ── Submit button ── */
  .submit-area {
    text-align: center;
    margin: 2rem 0;
    opacity: 0;
    transition: opacity 0.5s ease;
  }
  .submit-area.ready { opacity: 1; }

  .submit-btn {
    font-family: 'DM Sans', sans-serif;
    font-size: 1rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 1rem 3rem;
    background: var(--red);
    color: #fff;
    border: none;
    cursor: pointer;
    transition: all 0.2s ease;
    position: relative;
    overflow: hidden;
  }
  .submit-btn:hover {
    background: var(--red-light);
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(194,54,22,0.3);
  }
  .submit-btn:active {
    transform: translateY(0);
  }
  .submit-btn:disabled {
    background: var(--muted);
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }

  /* ── Results ── */
  #results {
    display: none;
  }
  #results.show {
    display: block;
    animation: fadeUp 0.6s ease forwards;
  }

  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(30px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .results-header {
    text-align: center;
    padding: 2rem 0;
    border-bottom: 4px double var(--ink);
    margin-bottom: 2rem;
  }
  .results-header h2 {
    font-family: 'Instrument Serif', Georgia, serif;
    font-size: clamp(1.8rem, 4vw, 2.6rem);
    font-weight: 400;
    line-height: 1.15;
    margin-bottom: 0.5rem;
  }
  .results-header .verdict {
    font-family: 'Instrument Serif', Georgia, serif;
    font-style: italic;
    font-size: 1.15rem;
    color: var(--muted);
  }

  .any-drug-stat {
    text-align: center;
    padding: 1.5rem;
    margin-bottom: 2rem;
    border: 1px solid var(--paper-dark);
    background: linear-gradient(135deg, var(--paper) 0%, var(--paper-dark) 100%);
  }
  .any-drug-pct {
    font-family: 'Instrument Serif', Georgia, serif;
    font-size: 3.5rem;
    font-weight: 400;
    line-height: 1;
    color: var(--red);
  }
  .any-drug-label {
    font-size: 0.85rem;
    color: var(--muted);
    margin-top: 0.3rem;
    font-weight: 300;
  }

  .drug-row {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.85rem 0;
    border-bottom: 1px solid var(--paper-dark);
    opacity: 0;
    transform: translateX(-10px);
    animation: slideIn 0.3s ease forwards;
  }
  .drug-row:nth-child(1) { animation-delay: 0.1s; }
  .drug-row:nth-child(2) { animation-delay: 0.17s; }
  .drug-row:nth-child(3) { animation-delay: 0.24s; }
  .drug-row:nth-child(4) { animation-delay: 0.31s; }
  .drug-row:nth-child(5) { animation-delay: 0.38s; }
  .drug-row:nth-child(6) { animation-delay: 0.45s; }

  @keyframes slideIn {
    to { opacity: 1; transform: translateX(0); }
  }

  .drug-rank {
    font-family: 'Instrument Serif', Georgia, serif;
    font-size: 1.5rem;
    color: var(--paper-dark);
    min-width: 2rem;
    text-align: right;
  }
  .drug-rank.top { color: var(--red); }

  .drug-info {
    flex: 1;
    min-width: 0;
  }
  .drug-name {
    font-weight: 700;
    font-size: 0.95rem;
  }
  .drug-class {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 0.1rem 0.4rem;
    display: inline-block;
    margin-left: 0.3rem;
    vertical-align: middle;
    color: #fff;
    border-radius: 1px;
  }
  .drug-class.class-a { background: var(--class-a); }
  .drug-class.class-b { background: var(--class-b); }
  .drug-class.class-c { background: var(--class-c); }

  .drug-bar-wrap {
    margin-top: 0.3rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  .drug-bar {
    flex: 1;
    height: 6px;
    background: var(--paper-dark);
    border-radius: 1px;
    overflow: hidden;
  }
  .drug-bar-fill {
    height: 100%;
    border-radius: 1px;
    transition: width 1s ease;
    width: 0%;
  }
  .drug-bar-fill.class-a { background: var(--class-a); }
  .drug-bar-fill.class-b { background: var(--class-b); }
  .drug-bar-fill.class-c { background: var(--class-c); }
  .drug-bar-fill.default { background: var(--ink); }

  .drug-pct {
    font-family: 'DM Sans', monospace;
    font-size: 0.85rem;
    font-weight: 700;
    min-width: 4rem;
    text-align: right;
  }

  .drug-comment {
    font-size: 0.8rem;
    font-style: italic;
    color: var(--muted);
    font-weight: 300;
    margin-top: 0.15rem;
  }

  .disclaimer {
    margin-top: 2.5rem;
    padding: 1.25rem;
    border: 1px solid var(--paper-dark);
    font-size: 0.8rem;
    color: var(--muted);
    line-height: 1.6;
    font-weight: 300;
  }
  .disclaimer strong {
    font-weight: 500;
    color: var(--ink);
  }

  .restart-btn {
    display: block;
    margin: 2rem auto;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.85rem;
    font-weight: 500;
    padding: 0.6rem 2rem;
    border: 1.5px solid var(--ink);
    background: transparent;
    color: var(--ink);
    cursor: pointer;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    transition: all 0.15s ease;
  }
  .restart-btn:hover {
    background: var(--ink);
    color: var(--paper);
  }

  /* ── Loading spinner ── */
  .loading { display: none; text-align: center; padding: 3rem 0; }
  .loading.show { display: block; }
  .spinner {
    width: 24px;
    height: 24px;
    border: 2px solid var(--paper-dark);
    border-top-color: var(--ink);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
    margin: 0 auto 1rem;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .loading-text {
    font-family: 'Instrument Serif', Georgia, serif;
    font-style: italic;
    color: var(--muted);
  }

  /* ── Responsive ── */
  @media (max-width: 500px) {
    .container { padding: 1rem; }
    .option-btn { font-size: 0.8rem; padding: 0.45rem 0.75rem; }
    .q-number { font-size: 1.8rem; }
  }
</style>
</head>
<body>

<div class="masthead">
  <span class="masthead-rule"></span>
  <h1>What Drugs Does The Government Think You Do?</h1>
  <p class="subtitle">Based on the Crime Survey for England &amp; Wales</p>
  <p class="edition">Data: year ending March 2025 &middot; Published by the Office for National Statistics</p>
</div>

<div class="progress-track">
  <div class="progress-bar-wrap">
    <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
    <span class="progress-text" id="progressText">0 / {{ questions|length }}</span>
  </div>
</div>

<div class="container">

  <p class="intro">
    The UK Government surveys tens of thousands of people each year about illegal drug use,
    broken down by <strong>age, sex, ethnicity, income, employment, religion, lifestyle</strong>
    and more. This app inverts that data: answer a few questions about yourself and find out
    which drugs the government would <em>statistically expect</em> you to be taking.
  </p>

  <form id="questionnaire">
    {% for q in questions %}
    <div class="question-card" data-qid="{{ q.id }}" id="card-{{ q.id }}">
      <div class="q-text">
        <span class="q-number">{{ loop.index }}.</span>
        {{ q.question }}
      </div>
      <div class="options">
        {% for opt_key in q.options %}
        <button type="button" class="option-btn" data-qid="{{ q.id }}" data-value="{{ opt_key }}">
          {{ opt_key }}
        </button>
        {% endfor %}
      </div>
    </div>
    {% endfor %}
  </form>

  <div class="submit-area" id="submitArea">
    <button type="button" class="submit-btn" id="submitBtn" disabled>
      Reveal My Drug Profile
    </button>
  </div>

  <div class="loading" id="loading">
    <div class="spinner"></div>
    <p class="loading-text">Cross-referencing your profile with government data&hellip;</p>
  </div>

  <div id="results"></div>
</div>

<script>
(function() {
  "use strict";

  var answers = {};
  var totalQuestions = {{ questions|length }};
  var allCards = document.querySelectorAll(".question-card");
  var allBtns = document.querySelectorAll(".option-btn");
  var submitArea = document.getElementById("submitArea");
  var submitBtn = document.getElementById("submitBtn");
  var progressFill = document.getElementById("progressFill");
  var progressText = document.getElementById("progressText");
  var resultsDiv = document.getElementById("results");
  var loading = document.getElementById("loading");

  var drugComments = {
    "Cannabis": "The perennial favourite. It's been number one since records began in 1995.",
    "Powder cocaine": "Friday night's open secret — popularity peaks in the 25–29 bracket.",
    "Ecstasy": "Still going strong three decades after the Second Summer of Love.",
    "Hallucinogens": "Magic mushrooms and LSD — nature and chemistry's mind-benders.",
    "Ketamine": "From veterinary anaesthetic to nightlife staple in a single generation.",
    "Amphetamines": "Speed: quietly persistent since the Northern Soul all-nighters."
  };

  // Reveal cards with staggered animation
  function revealCards() {
    allCards.forEach(function(card, i) {
      setTimeout(function() {
        card.classList.add("visible");
      }, 80 * i);
    });
  }

  function updateProgress() {
    var count = Object.keys(answers).length;
    var pct = Math.round((count / totalQuestions) * 100);
    progressFill.style.width = pct + "%";
    progressText.textContent = count + " / " + totalQuestions;
    if (count >= 3) {
      submitArea.classList.add("ready");
      submitBtn.disabled = false;
    }
  }

  // Handle option selection
  function handleOptionClick(e) {
    var btn = e.target;
    if (!btn.classList.contains("option-btn")) return;

    var qid = btn.getAttribute("data-qid");
    var value = btn.getAttribute("data-value");

    // Deselect siblings
    var siblings = btn.parentNode.querySelectorAll(".option-btn");
    siblings.forEach(function(s) { s.classList.remove("selected"); });

    // Select this one
    btn.classList.add("selected");
    answers[qid] = value;

    // Dim the answered card after a beat
    var card = document.getElementById("card-" + qid);
    setTimeout(function() {
      card.classList.add("answered");
    }, 300);

    updateProgress();
  }

  // Allow clicking answered card to re-expand it
  allCards.forEach(function(card) {
    card.addEventListener("click", function(e) {
      if (card.classList.contains("answered") && !e.target.classList.contains("option-btn")) {
        card.classList.remove("answered");
      }
    });
  });

  document.getElementById("questionnaire").addEventListener("click", handleOptionClick);

  // Submit
  submitBtn.addEventListener("click", function() {
    document.getElementById("questionnaire").style.display = "none";
    submitArea.style.display = "none";
    loading.classList.add("show");

    fetch("/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(answers)
    })
    .then(function(res) { return res.json(); })
    .then(function(data) { renderResults(data); })
    .catch(function(err) {
      loading.classList.remove("show");
      alert("Something went wrong. Please try again.");
      console.error(err);
    });
  });

  function renderResults(drugs) {
    loading.classList.remove("show");

    // Compute a rough "any drug" estimate from top rates
    var topThreeSum = drugs.slice(0, 3).reduce(function(s, d) { return s + d.rate; }, 0);
    // Inclusion-exclusion rough approximation
    var anyDrug = Math.min(topThreeSum * 0.85, 95);

    var verdict;
    if (anyDrug > 20) verdict = "The government is fairly confident you're partying.";
    else if (anyDrug > 12) verdict = "A statistical side-eye from Whitehall.";
    else if (anyDrug > 7) verdict = "Statistically average — you blend into the crowd.";
    else if (anyDrug > 3) verdict = "Statistically squeaky-clean, but not implausibly so.";
    else verdict = "The Home Office considers you an absolute saint.";

    var maxRate = drugs[0].rate;

    var html = '<div class="results-header">';
    html += '<h2>Your Government Drug Profile</h2>';
    html += '<p class="verdict">' + verdict + '</p>';
    html += '</div>';

    html += '<div class="any-drug-stat">';
    html += '<div class="any-drug-pct">' + anyDrug.toFixed(1) + '%</div>';
    html += '<div class="any-drug-label">estimated chance you\'ve used any illegal drug in the past year</div>';
    html += '</div>';

    html += '<div class="drug-list">';
    drugs.forEach(function(d, i) {
      var classSlug = d.classification.toLowerCase().replace(/\s+/g, "-");
      var barClass = classSlug || "default";
      var barWidth = maxRate > 0 ? Math.max((d.rate / maxRate) * 100, 0.5) : 0;
      var comment = drugComments[d.drug] || "";
      var rankClass = i < 3 ? "top" : "";

      html += '<div class="drug-row">';
      html += '<div class="drug-rank ' + rankClass + '">' + (i + 1) + '</div>';
      html += '<div class="drug-info">';
      html += '<span class="drug-name">' + d.drug + '</span>';
      if (d.classification) {
        html += '<span class="drug-class ' + barClass + '">' + d.classification + '</span>';
      }
      html += '<div class="drug-bar-wrap">';
      html += '<div class="drug-bar"><div class="drug-bar-fill ' + barClass + '" data-width="' + barWidth + '"></div></div>';
      html += '</div>';
      if (comment) {
        html += '<div class="drug-comment">' + comment + '</div>';
      }
      html += '</div>';
      html += '<div class="drug-pct">' + d.rate.toFixed(2) + '%</div>';
      html += '</div>';
    });
    html += '</div>';

    html += '<div class="disclaimer">';
    html += '<strong>Disclaimer.</strong> ';
    html += 'This is a statistical toy based on published survey data from the Crime Survey for England and Wales (year ending March 2025). ';
    html += 'Rates are adjusted using a geometric mean of demographic-specific prevalences — a simplification of complex, correlated factors. ';
    html += 'The figures shown are not a prediction of <em>your</em> actual behaviour, nor should they be taken as advice or accusation. ';
    html += 'Drug use carries serious health and legal risks. ';
    html += 'No personal data is stored or transmitted beyond this page.';
    html += '</div>';

    html += '<button type="button" class="restart-btn" onclick="location.reload()">Start Again</button>';

    resultsDiv.innerHTML = html;
    resultsDiv.classList.add("show");

    // Animate bars after a tick
    setTimeout(function() {
      var fills = resultsDiv.querySelectorAll(".drug-bar-fill");
      fills.forEach(function(f) {
        f.style.width = f.getAttribute("data-width") + "%";
      });
    }, 100);

    // Scroll to results
    resultsDiv.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  // Init
  revealCards();

})();
</script>
</body>
</html>
'''

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
