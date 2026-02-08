#!/usr/bin/env python3
"""
Extract demographic drug prevalence data from the CSEW spreadsheet
into a JSON structure for the web app.
"""

import json
import openpyxl

XLSX_PATH = "Drug_Misuse_Appendix_Tables_Mar_2025.xlsx"

DRUG_COLS = {
    2: "Powder cocaine",
    3: "Ecstasy",
    4: "Hallucinogens",
    5: "Amphetamines",
    6: "Cannabis",
    7: "Ketamine",
}

DRUG_CLASSES = {
    "Powder cocaine": "Class A",
    "Ecstasy": "Class A",
    "Hallucinogens": "Class A",
    "Amphetamines": "Class B",
    "Cannabis": "Class B",
    "Ketamine": "Class B",
}

def read_table(wb, sheet_name, row_ranges):
    """Read specific rows from a sheet, returning {category_label: {drug: rate}}."""
    ws = wb[sheet_name]
    rows = list(ws.iter_rows(min_row=1, max_row=120, values_only=True))
    result = {}
    for row_idx in row_ranges:
        row = rows[row_idx - 1]  # 0-indexed
        label = str(row[1]).strip() if row[1] else str(row[0]).strip()
        rates = {}
        for col_idx, drug_name in DRUG_COLS.items():
            val = row[col_idx]
            if val is not None and isinstance(val, (int, float)):
                rates[drug_name] = round(val, 4)
            else:
                rates[drug_name] = 0.0
        result[label] = rates
    return result


def extract_all():
    wb = openpyxl.load_workbook(XLSX_PATH, read_only=True, data_only=True)

    # Baseline (all people 16-59) from row 8 of 3.01
    baseline = read_table(wb, "3.01", [8])

    data = {
        "baseline": baseline["All people aged 16-59 years"],
        "drug_classes": DRUG_CLASSES,
        "questions": []
    }

    # ── Age (rows 9-15) ──
    age_data = read_table(wb, "3.01", [9, 10, 11, 12, 13, 14, 15])
    data["questions"].append({
        "id": "age",
        "question": "How old are you?",
        "options": {
            "16–19": age_data.get("16–19", {}),
            "20–24": age_data.get("20–24", {}),
            "25–29": age_data.get("25–29", {}),
            "30–34": age_data.get("30–34", {}),
            "35–44": age_data.get("35–44", {}),
            "45–54": age_data.get("45–54", {}),
            "55–59": age_data.get("55–59", {}),
        }
    })

    # ── Sex (rows 18, 21) ──
    sex_data = read_table(wb, "3.01", [18, 21])
    data["questions"].append({
        "id": "sex",
        "question": "What is your sex?",
        "options": {
            "Male": sex_data.get("All men aged 16-59 years", {}),
            "Female": sex_data.get("All women aged 16-59 years", {}),
        }
    })

    # ── Ethnic group (rows 24-28) ──
    eth_data = read_table(wb, "3.01", [24, 25, 26, 27, 28])
    data["questions"].append({
        "id": "ethnicity",
        "question": "What is your ethnic group?",
        "options": {
            "White": eth_data.get("White ", eth_data.get("White", {})),
            "Mixed / Multiple": eth_data.get("Mixed/Multiple", {}),
            "Asian / Asian British": eth_data.get("Asian/Asian British", {}),
            "Black / Black British": eth_data.get("Black/African/Caribbean/Black British", {}),
            "Other ethnic group": eth_data.get("Other ethnic group", {}),
        }
    })

    # ── Marital status (rows 31-36) ──
    mar_data = read_table(wb, "3.01", [31, 32, 33, 34, 35])
    data["questions"].append({
        "id": "marital",
        "question": "What is your relationship status?",
        "options": {
            "Married / civil partnership": mar_data.get("Married/civil partnered", {}),
            "Cohabiting": mar_data.get("Cohabiting", {}),
            "Single": mar_data.get("Single", {}),
            "Separated": mar_data.get("Separated", {}),
            "Divorced": mar_data.get("Divorced/legally dissolved partnership", {}),
        }
    })

    # ── Employment (rows 37-44) ──
    emp_data = read_table(wb, "3.01", [37, 38, 39, 40, 42])
    data["questions"].append({
        "id": "employment",
        "question": "What is your employment status?",
        "options": {
            "Employed": emp_data.get("In employment", {}),
            "Unemployed": emp_data.get("Unemployed", {}),
            "Student": emp_data.get("Economically inactive: Student", {}),
            "Long-term sick / disabled": emp_data.get("Economically inactive: Long-term/temporarily sick/", emp_data.get("Economically inactive: Long-term/temporarily sick/ ", {})),
            "Other economically inactive": emp_data.get("Economically inactive", {}),
        }
    })

    # ── Qualification (rows 51-55) ──
    qual_data = read_table(wb, "3.01", [51, 52, 53, 55])
    data["questions"].append({
        "id": "qualification",
        "question": "What is your highest qualification?",
        "options": {
            "Degree or diploma": qual_data.get("Degree or diploma", {}),
            "A-levels / apprenticeship": qual_data.get("Apprenticeship or A/AS level", {}),
            "GCSEs / O-levels": qual_data.get("O level/GCSE", {}),
            "No qualifications": qual_data.get("None", {}),
        }
    })

    # ── Religion (rows 58-65) ──
    rel_data = read_table(wb, "3.01", [58, 59, 63])
    data["questions"].append({
        "id": "religion",
        "question": "What is your religion?",
        "options": {
            "No religion": rel_data.get("No religion", {}),
            "Christian": rel_data.get("Christian", {}),
            "Muslim": rel_data.get("Muslim", {}),
        }
    })

    # ── Nightclub visits (rows 72-74) ──
    club_data = read_table(wb, "3.01", [72, 73, 74])
    data["questions"].append({
        "id": "nightclub",
        "question": "How many times did you visit a nightclub in the past month?",
        "options": {
            "None": club_data.get("None", {}),
            "1 to 3 visits": club_data.get("1 to 3 visits", {}),
            "4 or more visits": club_data.get("4 or more visits", {}),
        }
    })

    # ── Pub visits (rows 75-78) ──
    pub_data = read_table(wb, "3.01", [75, 76, 77, 78])
    data["questions"].append({
        "id": "pub",
        "question": "How many evening visits to a pub or bar did you make in the past month?",
        "options": {
            "None": pub_data.get("None", {}),
            "1 to 3 visits": pub_data.get("1 to 3 visits", {}),
            "4 to 8 visits": pub_data.get("4 - 8 times", pub_data.get("4 - 8 visits", {})),
            "9 or more visits": pub_data.get("9 or more visits", {}),
        }
    })

    # ── Alcohol consumption (rows 79-82) ──
    alc_data = read_table(wb, "3.01", [79, 80, 81, 82])
    data["questions"].append({
        "id": "alcohol",
        "question": "How often do you drink alcohol?",
        "options": {
            "Less than once a month (inc. non-drinkers)": alc_data.get("Less than once a month (inc. non-drinkers)", {}),
            "Less than once a week": alc_data.get("Less than a day a week in the last month ", alc_data.get("Less than a day a week in the last month", {})),
            "1–2 days a week": alc_data.get("1-2 days a week in the last month", {}),
            "3 or more days a week": alc_data.get("3 or more days a week in the last month", {}),
        }
    })

    # ── Life satisfaction (rows 89-92) ──
    sat_data = read_table(wb, "3.01", [89, 90, 91, 92])
    data["questions"].append({
        "id": "satisfaction",
        "question": "How satisfied are you with your life? (0 = not at all, 10 = completely)",
        "options": {
            "Low (0–4)": sat_data.get("Low", {}),
            "Medium (5–6)": sat_data.get("Medium", {}),
            "High (7–8)": sat_data.get("High", {}),
            "Very high (9–10)": sat_data.get("Very high", sat_data.get("Very High", {})),
        }
    })

    # ── Household income from 3.02 (rows 12-17) ──
    inc_data = read_table(wb, "3.02", [12, 13, 14, 15, 16, 17])
    data["questions"].append({
        "id": "income",
        "question": "What is your total household income?",
        "options": {
            "Under £10,400": inc_data.get("Less than £10,400", {}),
            "£10,400 – £20,799": inc_data.get("£10,400 to less than £20,800", {}),
            "£20,800 – £31,199": inc_data.get("£20,800 to less than £31,200", {}),
            "£31,200 – £41,599": inc_data.get("£31,200 to less than £41,600", {}),
            "£41,600 – £51,999": inc_data.get("£41,600 to less than £52,000", {}),
            "£52,000 or more": inc_data.get("£52,000 or more", {}),
        }
    })

    # ── Region from 3.02 (rows 46-55) ──
    reg_data = read_table(wb, "3.02", [46, 47, 48, 49, 50, 51, 52, 53, 54, 55])
    # The labels have leading spaces — strip them
    cleaned_reg = {}
    for k, v in reg_data.items():
        cleaned_reg[k.strip()] = v
    data["questions"].append({
        "id": "region",
        "question": "Where do you live?",
        "options": {
            "North East": cleaned_reg.get("North East", {}),
            "North West": cleaned_reg.get("North West", {}),
            "Yorkshire and the Humber": cleaned_reg.get("Yorkshire and the Humber", {}),
            "East Midlands": cleaned_reg.get("East Midlands", {}),
            "West Midlands": cleaned_reg.get("West Midlands", {}),
            "East of England": cleaned_reg.get("East", {}),
            "London": cleaned_reg.get("London", {}),
            "South East": cleaned_reg.get("South East", {}),
            "South West": cleaned_reg.get("South West", {}),
            "Wales": cleaned_reg.get("Wales", {}),
        }
    })

    wb.close()
    return data


if __name__ == "__main__":
    data = extract_all()
    # Quick sanity check
    print(f"Baseline rates: {data['baseline']}")
    print(f"Number of questions: {len(data['questions'])}")
    for q in data["questions"]:
        print(f"  {q['id']}: {len(q['options'])} options")
        # Check first option has data
        first_key = list(q["options"].keys())[0]
        first_val = q["options"][first_key]
        non_zero = sum(1 for v in first_val.values() if v > 0)
        print(f"    First option '{first_key}': {non_zero}/{len(first_val)} non-zero rates")

    with open("csew_data.json", "w") as f:
        json.dump(data, f, indent=2)
    print(f"\nWritten to csew_data.json ({len(json.dumps(data))} bytes)")
