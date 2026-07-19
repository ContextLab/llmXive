import os
import csv
import pytest
from pathlib import Path

# Import analysis functions if needed for setup, though this is an integration test
# We assume the pipeline has been run up to T024 before this test runs.
# If the test is run in isolation without data, it should fail explicitly.
try:
    from analysis import main as analysis_main
except ImportError:
    analysis_main = None

RESULTS_DIR = Path("results")
REPORT_FILE = RESULTS_DIR / "results_report.csv"
HEATMAP_FILE = RESULTS_DIR / "correlation_heatmap.png"
ANALYSIS_RESULTS_FILE = Path("data/processed/analysis_results.csv")

REQUIRED_COLUMNS = [
    "trait", "genre", "rho", "p_value", "p_value_adj", "is_significant",
    "beta_age", "beta_gender", "beta_country", "effect_size_r", "ci_lower", "ci_upper", "model_definition"
]

REQUIRED_TRAITS = [
    "Extraversion", "Agreeableness", "Conscientiousness", "Emotional Stability", "Openness"
]

MIN_GENRES = 10  # As per task description "10+ genres"

def _ensure_analysis_data_exists():
    """Helper to ensure the prerequisite analysis file exists.
    If T024 hasn't run, this test cannot proceed and should fail loudly."""
    if not ANALYSIS_RESULTS_FILE.exists():
        pytest.fail(
            f"Prerequisite file {ANALYSIS_RESULTS_FILE} not found. "
            "Ensure T024 (analysis) has been executed successfully before running T025 tests."
        )

def _ensure_reporting_run():
    """Helper to ensure the reporting script has been executed.
    Since T025 is a test task, it assumes the implementation (T026-T028)
    has already generated the outputs. If not, we fail explicitly."""
    if not REPORT_FILE.exists():
        pytest.fail(
            f"Report file {REPORT_FILE} not found. "
            "Ensure the reporting script (T026-T028 implementation) has been executed."
        )
    if not HEATMAP_FILE.exists():
        pytest.fail(
            f"Heatmap file {HEATMAP_FILE} not found. "
            "Ensure the reporting script (T026-T028 implementation) has been executed."
        )

def test_report_file_existence():
    """Verify that the reporting script generates the required output files."""
    _ensure_analysis_data_exists()
    _ensure_reporting_run()
    
    assert REPORT_FILE.exists(), f"Report file {REPORT_FILE} does not exist"
    assert HEATMAP_FILE.exists(), f"Heatmap file {HEATMAP_FILE} does not exist"
    assert REPORT_FILE.stat().st_size > 0, f"Report file {REPORT_FILE} is empty"
    assert HEATMAP_FILE.stat().st_size > 0, f"Heatmap file {HEATMAP_FILE} is empty"

def test_report_content_schema():
    """Verify the content schema of results_report.csv."""
    _ensure_analysis_data_exists()
    _ensure_reporting_run()

    with open(REPORT_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        
        # Check all required columns are present
        missing_columns = set(REQUIRED_COLUMNS) - set(headers)
        assert not missing_columns, f"Missing columns in report: {missing_columns}"

        rows = list(reader)
        assert len(rows) > 0, "Report file contains no data rows"

        # Verify data types and basic constraints
        for i, row in enumerate(rows):
            # Check numeric fields are parseable (if not NaN)
            for field in ["rho", "p_value", "p_value_adj", "effect_size_r", "ci_lower", "ci_upper"]:
                val = row.get(field)
                if val and val != "NaN" and val != "":
                    try:
                        float(val)
                    except ValueError:
                        pytest.fail(f"Row {i}, column {field} is not a valid number: {val}")

            # Check significant flag logic
            is_sig = row.get("is_significant")
            assert is_sig in ["True", "False", "true", "false", "1", "0", "Non-significant"], \
                f"Invalid is_significant value: {is_sig}"

def test_report_completeness():
    """Verify the report includes all 5 traits across multiple genres (at least 10)."""
    _ensure_analysis_data_exists()
    _ensure_reporting_run()

    with open(REPORT_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    traits_in_report = set()
    genres_in_report = set()

    for row in rows:
        trait = row.get("trait")
        genre = row.get("genre")
        if trait:
            traits_in_report.add(trait)
        if genre:
            genres_in_report.add(genre)

    # Check all 5 traits are present
    missing_traits = set(REQUIRED_TRAITS) - traits_in_report
    assert not missing_traits, f"Missing traits in report: {missing_traits}. Found: {traits_in_report}"

    # Check at least 10 genres
    assert len(genres_in_report) >= MIN_GENRES, \
        f"Expected at least {MIN_GENRES} genres, found {len(genres_in_report)}: {genres_in_report}"

def test_heatmap_image_validity():
    """Basic check that the heatmap file is a valid image (non-empty binary)."""
    _ensure_analysis_data_exists()
    _ensure_reporting_run()

    assert HEATMAP_FILE.exists()
    size = HEATMAP_FILE.stat().st_size
    # A valid PNG is at least 67 bytes (header + IHDR + IEND), usually much larger
    assert size > 100, f"Heatmap file {HEATMAP_FILE} is suspiciously small ({size} bytes)"
    
    # Check PNG magic number
    with open(HEATMAP_FILE, 'rb') as f:
        magic = f.read(8)
        assert magic[:8] == b'\x89PNG\r\n\x1a\n', "File does not appear to be a valid PNG image"