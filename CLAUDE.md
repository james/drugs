# CLAUDE.md

## Project Overview

**"What Drugs Does The Government Think You Do?"** — A Flask web app that inverts UK Government drug usage statistics from the Crime Survey for England and Wales (CSEW). Users answer demographic questions and the app predicts which drugs the government would statistically expect them to use, based on a geometric-mean-of-ratios algorithm.

Live at: https://drugs-gov-stats.fly.dev/

## Repository Structure

```
.
├── app.py              # Flask entry point: routes for / and /predict
├── data.py             # Loads csew_data.json; exports BASELINE, DRUG_CLASSES, QUESTIONS, DRUGS
├── predict.py          # Prediction engine (geometric mean of ratios algorithm)
├── extract_data.py     # One-time utility to extract data from ONS Excel spreadsheet
├── csew_data.json      # Pre-extracted survey data (do not edit manually)
├── requirements.txt    # Python deps: flask, gunicorn
├── Dockerfile          # Python 3.11-slim container
├── Procfile            # Heroku-style process definition
├── fly.toml            # Fly.io deployment config (London region, 256MB)
├── static/
│   ├── app.js          # Frontend JS (vanilla, no frameworks)
│   └── style.css       # CSS (newspaper-inspired design, CSS custom properties)
├── templates/
│   └── index.html      # Jinja2 template
└── .github/workflows/
    └── fly-deploy.yml  # CI/CD: auto-deploy to Fly.io on push to main
```

## Tech Stack

- **Backend**: Python 3.11, Flask 3.1.0, Gunicorn 23.0.0
- **Frontend**: Vanilla JavaScript (ES5), HTML5, CSS3 (no build step, no JS frameworks)
- **Data**: Static JSON file (no database)
- **Deployment**: Docker on Fly.io, GitHub Actions CI/CD

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server (port 5001, debug mode)
python app.py

# Run production server
gunicorn --bind 0.0.0.0:8080 --workers 1 --threads 2 --timeout 60 app:app

# Re-extract data from ONS spreadsheet (requires openpyxl, not in requirements.txt)
pip install openpyxl
python extract_data.py
```

## Architecture

### Data Flow

1. `extract_data.py` reads the ONS Excel spreadsheet and writes `csew_data.json` (one-time)
2. `data.py` loads `csew_data.json` at import time and exposes: `BASELINE`, `DRUG_CLASSES`, `QUESTIONS`, `DRUGS`
3. `app.py` serves the index page (injecting `QUESTIONS` into the Jinja2 template) and a `/predict` POST endpoint
4. `predict.py` receives user answers, computes adjusted prevalence rates using geometric mean of ratios, and returns ranked results
5. `static/app.js` handles the frontend: question navigation, form submission via fetch, and result rendering

### Prediction Algorithm (`predict.py`)

For each drug, the algorithm:
1. Looks up the baseline prevalence rate (overall population)
2. For each answered question, gets the demographic-specific rate and computes the ratio to baseline
3. Combines all ratios via geometric mean (avoids compounding inflation)
4. Multiplies baseline by the geometric mean to get an adjusted rate
5. Caps results at 0–95%

A floor of 0.01% is used when a demographic rate is zero in the survey data, to prevent log(0).

### Drugs Tracked

Cannabis (Class B), Powder cocaine (Class A), Ecstasy (Class A), Hallucinogens (Class A), Amphetamines (Class B), Ketamine (Class B)

### API

- `GET /` — Serves the main page
- `POST /predict` — Accepts JSON body with question IDs mapped to chosen option labels; returns JSON array of `{drug, rate, classification}` sorted by rate descending

## Key Conventions

- **No tests or linting are configured.** There are no test files, no pytest/mypy/ruff configs.
- **No build step** for frontend assets. Edit JS/CSS/HTML directly.
- **`csew_data.json` is generated, not hand-edited.** Changes to survey data should go through `extract_data.py`.
- **Stateless application.** No database, sessions, or server-side state.
- **Minimal dependencies.** Only Flask and Gunicorn in production. Keep it lean.
- **Module imports**: `data.py` is the single source of truth for survey data; `predict.py` contains only the algorithm; `app.py` only does routing.

## Deployment

- Pushes to `main` trigger auto-deploy via GitHub Actions (`.github/workflows/fly-deploy.yml`)
- Deploys to Fly.io in London (`lhr` region), 256MB shared-cpu VM
- Auto-stop/start enabled; scales to 0 when idle
- Docker build uses `python:3.11-slim`

