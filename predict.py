"""
Prediction engine: compute adjusted drug prevalence rates from
demographic answers using a geometric mean of ratios.
"""

import math

from data import BASELINE, DRUG_CLASSES, DRUGS, QUESTIONS


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

        multiplier = adjusted / base if base > 0 else 1.0

        results.append({
            "drug": drug,
            "rate": round(adjusted, 2),
            "baseline_rate": round(base, 2),
            "multiplier": round(multiplier, 2),
            "classification": DRUG_CLASSES.get(drug, ""),
        })

    results.sort(key=lambda x: x["rate"], reverse=True)
    return results
