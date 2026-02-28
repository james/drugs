"""
Feature tests: use Playwright to drive a real browser through the app,
submitting different user personas and verifying the results page.
"""

import subprocess
import time
import signal
import os

import pytest
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:5001"
DRUGS = ["Cannabis", "Powder cocaine", "Ecstasy", "Hallucinogens", "Ketamine", "Amphetamines"]


@pytest.fixture(scope="session")
def server():
    """Start the Flask dev server for the test session."""
    proc = subprocess.Popen(
        ["python", "app.py"],
        env=os.environ.copy(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.path.dirname(__file__) or ".",
    )
    # Wait for the server to be ready
    for _ in range(30):
        try:
            import urllib.request
            urllib.request.urlopen(BASE_URL, timeout=1)
            break
        except Exception:
            time.sleep(0.3)
    yield proc
    proc.send_signal(signal.SIGTERM)
    proc.wait(timeout=5)


@pytest.fixture(scope="session")
def browser(server):
    """Launch a headless Chromium browser for the test session."""
    pw = sync_playwright().start()
    launch_opts = {"headless": True}
    # Allow overriding the Chromium path for environments where
    # `playwright install` can't download (e.g. sandboxed containers).
    chromium_path = os.environ.get("PLAYWRIGHT_CHROMIUM_PATH")
    if chromium_path:
        launch_opts["executable_path"] = chromium_path
    b = pw.chromium.launch(**launch_opts)
    yield b
    b.close()
    pw.stop()


@pytest.fixture
def page(browser):
    """Create a fresh browser page for each test."""
    p = browser.new_page()
    yield p
    p.close()


def _select_option(page, question_name, value):
    """Click the label wrapping a radio button (the input itself is visually hidden)."""
    label = page.locator(f'label:has(input[name="{question_name}"][value="{value}"])')
    label.click()


def _submit_form(page):
    """Click the submit button and wait for navigation."""
    page.locator("button[type='submit']").click()
    page.wait_for_url("**/predict", timeout=5000)


def _assert_results_page(page):
    """Verify the results page has the expected structure."""
    assert page.locator("h2").inner_text() == "Your Government Drug Profile"
    assert page.locator(".disclaimer").is_visible()
    assert page.locator(".restart-btn").is_visible()
    # All six drugs should appear
    for drug in DRUGS:
        assert page.locator(f".drug-name:has-text('{drug}')").is_visible()


# ── Page load ────────────────────────────────────────────────────


def test_index_loads(page):
    """The home page loads and shows the question form."""
    page.goto(BASE_URL)
    assert "What Drugs Does The Government Think You Do?" in page.title()
    assert page.locator("form[action='/predict']").is_visible()
    # Button text is CSS-uppercased, so compare case-insensitively
    assert page.locator("button[type='submit']").inner_text().lower() == "reveal my drug profile"
    # Check that question fieldsets are rendered
    assert page.locator("fieldset.question-card").count() > 0


def test_empty_submission_stays_on_index(page):
    """Submitting with no answers redirects back to the index."""
    page.goto(BASE_URL)
    page.locator("button[type='submit']").click()
    # Should redirect back to index (the form page)
    page.wait_for_load_state("networkidle")
    assert page.locator("form[action='/predict']").is_visible()


# ── User personas ────────────────────────────────────────────────


def test_young_male_clubber(page):
    """20-24 male, single, nightclub-goer, heavy drinker in London.
    Should produce above-average drug rates."""
    page.goto(BASE_URL)

    _select_option(page, "age", "20\u201324")
    _select_option(page, "sex", "Male")
    _select_option(page, "marital", "Single")
    _select_option(page, "nightclub", "4 or more visits")
    _select_option(page, "alcohol", "3 or more days a week")
    _select_option(page, "region", "London")

    _submit_form(page)
    _assert_results_page(page)

    # This profile should be well above average
    verdict = page.locator(".verdict").inner_text().lower()
    assert "partying" in verdict or "side-eye" in verdict

    # Multiplier should be above 1x
    multiplier_text = page.locator(".any-drug-pct").inner_text()
    multiplier_val = float(multiplier_text.replace("\u00d7", ""))
    assert multiplier_val > 1.0


def test_older_married_christian_woman(page):
    """55-59 female, married, Christian, no nightclubs, rarely drinks.
    Should produce below-average drug rates."""
    page.goto(BASE_URL)

    _select_option(page, "age", "55\u201359")
    _select_option(page, "sex", "Female")
    _select_option(page, "marital", "Married / civil partnership")
    _select_option(page, "religion", "Christian")
    _select_option(page, "nightclub", "None")
    _select_option(page, "alcohol", "Less than once a month (inc. non-drinkers)")
    _select_option(page, "satisfaction", "Very high (9\u201310)")

    _submit_form(page)
    _assert_results_page(page)

    # This profile should be well below average
    verdict = page.locator(".verdict").inner_text().lower()
    assert "saint" in verdict or "squeaky" in verdict

    # Multiplier should be below 1x
    multiplier_text = page.locator(".any-drug-pct").inner_text()
    multiplier_val = float(multiplier_text.replace("\u00d7", ""))
    assert multiplier_val < 1.0


def test_student_in_south_west(page):
    """20-24 student, no religion, A-levels, South West, pub-goer."""
    page.goto(BASE_URL)

    _select_option(page, "age", "20\u201324")
    _select_option(page, "employment", "Student")
    _select_option(page, "religion", "No religion")
    _select_option(page, "qualification", "A-levels / apprenticeship")
    _select_option(page, "pub", "1 to 3 visits")
    _select_option(page, "region", "South West")

    _submit_form(page)
    _assert_results_page(page)

    # Cannabis should be the top-ranked drug
    first_drug = page.locator(".drug-name").first.inner_text()
    assert first_drug == "Cannabis"


def test_middle_aged_employed_white_male(page):
    """35-44, male, white, employed, degree, married, pub-goer.
    A 'statistically average' profile."""
    page.goto(BASE_URL)

    _select_option(page, "age", "35\u201344")
    _select_option(page, "sex", "Male")
    _select_option(page, "ethnicity", "White")
    _select_option(page, "employment", "Employed")
    _select_option(page, "qualification", "Degree or diploma")
    _select_option(page, "marital", "Married / civil partnership")
    _select_option(page, "pub", "1 to 3 visits")
    _select_option(page, "alcohol", "1\u20132 days a week")

    _submit_form(page)
    _assert_results_page(page)

    # All six drugs should show rate vs baseline
    rate_elements = page.locator(".drug-abs-rate")
    assert rate_elements.count() == 6
    for i in range(6):
        text = rate_elements.nth(i).inner_text()
        assert "vs" in text


def test_single_answer_only(page):
    """Submitting just one answer should still produce full results."""
    page.goto(BASE_URL)

    _select_option(page, "sex", "Female")

    _submit_form(page)
    _assert_results_page(page)


def test_results_contain_drug_classifications(page):
    """Each drug should show its legal classification (Class A / Class B)."""
    page.goto(BASE_URL)

    _select_option(page, "age", "25\u201329")
    _select_option(page, "sex", "Male")

    _submit_form(page)

    class_a = page.locator(".drug-class.class-a")
    class_b = page.locator(".drug-class.class-b")
    assert class_a.count() > 0
    assert class_b.count() > 0


def test_start_again_returns_to_form(page):
    """Clicking 'Start Again' on results page returns to the form."""
    page.goto(BASE_URL)

    _select_option(page, "sex", "Male")
    _submit_form(page)
    _assert_results_page(page)

    # Click "Start Again"
    page.locator(".restart-btn").click()
    page.wait_for_url(BASE_URL + "/", timeout=5000)
    assert page.locator("form[action='/predict']").is_visible()
