"""
Feature tests: submit different user personas through the form
and verify the results page renders correctly with sensible predictions.
"""

import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ── Page load ────────────────────────────────────────────────────


def test_index_loads(client):
    """The home page loads and contains the question form."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.data.decode()
    assert "What Drugs Does The Government Think You Do?" in html
    assert '<form action="/predict"' in html
    assert 'name="age"' in html
    assert 'name="sex"' in html
    assert "Reveal My Drug Profile" in html


def test_empty_submission_redirects(client):
    """Submitting with no answers redirects back to the index."""
    resp = client.post("/predict", data={})
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/")


# ── Helper ───────────────────────────────────────────────────────


def _submit(client, answers):
    """POST answers and return (status_code, decoded html)."""
    resp = client.post("/predict", data=answers)
    return resp.status_code, resp.data.decode()


DRUGS = ["Cannabis", "Powder cocaine", "Ecstasy", "Hallucinogens", "Ketamine", "Amphetamines"]


def _assert_results_page(html):
    """Check the results page has the expected structure."""
    assert "Your Government Drug Profile" in html
    assert "Disclaimer" in html
    assert "Start Again" in html
    for drug in DRUGS:
        assert drug in html


# ── User personas ────────────────────────────────────────────────


def test_young_male_clubber(client):
    """20–24 male, single, nightclub-goer, heavy drinker in London.
    Should produce above-average drug rates."""
    status, html = _submit(client, {
        "age": "20\u201324",
        "sex": "Male",
        "marital": "Single",
        "nightclub": "4 or more visits",
        "alcohol": "3 or more days a week",
        "region": "London",
    })
    assert status == 200
    _assert_results_page(html)
    # This profile should be well above average
    assert "partying" in html.lower() or "side-eye" in html.lower()
    # Multiplier should be above 1
    assert "&times;" in html  # × symbol present


def test_older_married_christian_woman(client):
    """55–59 female, married, Christian, no nightclubs, rarely drinks.
    Should produce below-average drug rates."""
    status, html = _submit(client, {
        "age": "55\u201359",
        "sex": "Female",
        "marital": "Married / civil partnership",
        "religion": "Christian",
        "nightclub": "None",
        "alcohol": "Less than once a month (inc. non-drinkers)",
        "satisfaction": "Very high (9\u201310)",
    })
    assert status == 200
    _assert_results_page(html)
    # This profile should be well below average
    assert "saint" in html.lower() or "squeaky" in html.lower()


def test_student_in_south_west(client):
    """20–24 student, no religion, A-levels, South West, moderate pub visits."""
    status, html = _submit(client, {
        "age": "20\u201324",
        "employment": "Student",
        "religion": "No religion",
        "qualification": "A-levels / apprenticeship",
        "pub": "1 to 3 visits",
        "region": "South West",
    })
    assert status == 200
    _assert_results_page(html)
    # Cannabis should appear as the top drug (highest baseline + student boost)
    # Find the first drug listed — it appears in the first drug-name span
    first_drug_pos = html.find('<span class="drug-name">')
    assert first_drug_pos != -1
    first_drug_end = html.find("</span>", first_drug_pos)
    first_drug = html[first_drug_pos + len('<span class="drug-name">'):first_drug_end].strip()
    assert first_drug == "Cannabis"


def test_middle_aged_employed_white_male(client):
    """35–44, male, white, employed, degree, married, pub-goer.
    A 'statistically average' profile."""
    status, html = _submit(client, {
        "age": "35\u201344",
        "sex": "Male",
        "ethnicity": "White",
        "employment": "Employed",
        "qualification": "Degree or diploma",
        "marital": "Married / civil partnership",
        "pub": "1 to 3 visits",
        "alcohol": "1\u20132 days a week",
    })
    assert status == 200
    _assert_results_page(html)
    # All six drugs should appear with rates and baselines
    assert html.count("vs") >= 6  # "vs" appears in "X% vs Y%"


def test_single_answer_only(client):
    """Submitting just one answer should still produce results."""
    status, html = _submit(client, {"sex": "Female"})
    assert status == 200
    _assert_results_page(html)
    # Should show "1 of" in answered count context
    assert "1" in html


def test_results_contain_drug_classifications(client):
    """Each drug should show its legal classification (Class A / Class B)."""
    status, html = _submit(client, {
        "age": "25\u201329",
        "sex": "Male",
    })
    assert status == 200
    assert "Class A" in html
    assert "Class B" in html
