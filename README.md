# What Drugs Does The Government Think You Do?

A Python web app that inverts the UK Government's drug usage statistics. Instead of reporting *"X% of demographic group Y use drug Z"*, it asks **you** some questions about yourself and tells you which drugs the government would statistically expect you to be taking.

## Data source

**Crime Survey for England and Wales, year ending March 2025**
Published by the Office for National Statistics (ONS), December 2025.

The app reads directly from the official appendix tables spreadsheet (`Drug_Misuse_Appendix_Tables_Mar_2025.xlsx`), specifically:

- **Table 3.01** — Drug use by personal characteristics (age, sex, ethnicity, marital status, employment, qualifications, religion, sexual orientation, nightclub visits, pub visits, alcohol consumption, life satisfaction)
- **Table 3.02** — Drug use by household and area characteristics (income, tenure, region)

## How it works

1. `extract_data.py` reads the CSEW spreadsheet and extracts demographic prevalence rates for six drug categories (Cannabis, Powder cocaine, Ecstasy, Hallucinogens, Amphetamines, Ketamine) across 13 demographic questions.

2. The web app asks you 13 multiple-choice questions matching the CSEW demographic categories.

3. For each drug, it computes an adjusted prevalence rate using a **geometric mean of ratios**: for each question you answer, the app computes the ratio of your demographic group's rate to the overall baseline rate, then combines all ratios via geometric mean. This avoids the product of many independent multipliers blowing up to absurd values.

4. Results are displayed as a ranked "drug profile" showing your estimated prevalence for each drug.

## Setup

```bash
pip install flask openpyxl
```

## Running

```bash
python app.py
```

Then open http://localhost:5000 in your browser.

## Files

| File | Purpose |
|---|---|
| `app.py` | Flask web app — the prediction engine and full HTML/CSS/JS frontend |
| `extract_data.py` | Extracts data from the CSEW spreadsheet into `csew_data.json` |
| `csew_data.json` | Pre-extracted data (so you don't need openpyxl at runtime) |
| `Drug_Misuse_Appendix_Tables_Mar_2025.xlsx` | The original ONS data |

## Disclaimer

This is a statistical toy. The figures are simplified estimates based on published survey data, not predictions of anyone's actual behaviour. Drug use carries serious health and legal risks. No personal data is stored or transmitted.
