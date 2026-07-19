import os
import pandas as pd
import pytest
from pathlib import Path

# Project root relative to tests/
PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
REPORT_FILE = RESULTS_DIR / "results_report.csv"

# Expected constants based on the study design
EXPECTED_TRAITS = [
    "Extraversion",
    "Agreeableness",
    "Conscientiousness",
    "Emotional Stability",
    "Openness"
]

# Minimum number of standard genres required by the spec (10+)
MIN_GENRES = 10


@pytest.fixture(scope="module")
def report_df():
    """Load the results report CSV.
    
    This fixture ensures the file exists and loads it into a DataFrame.
    If the file is missing or empty, the test suite will fail immediately.
    """
    if not REPORT_FILE.exists():
        pytest.fail(f"Results report file not found at: {REPORT_FILE}. "
                    "Ensure the analysis pipeline (T028) has been executed.")
    
    df = pd.read_csv(REPORT_FILE)
    if df.empty:
        pytest.fail(f"Results report file at {REPORT_FILE} is empty.")
    return df


def test_report_completeness(report_df):
    """Verify that results_report.csv includes all 5 traits × 10+ genres.
    
    This test validates the completeness of the US3 reporting output.
    It checks:
    1. All 5 BFI-2 personality traits are present.
    2. At least 10 distinct genres are represented.
    3. Every trait has entries for at least the required number of genres.
    """
    # 1. Check that all expected traits are present
    # We assume the column name for traits is 'trait' or 'personality_trait'
    # Based on typical analysis output, 'trait' is the most likely candidate.
    # If the column name differs, we need to handle that.
    trait_columns = [col for col in report_df.columns if 'trait' in col.lower()]
    if not trait_columns:
        pytest.fail(f"Could not identify trait column in report. Columns found: {list(report_df.columns)}")
    
    trait_col = trait_columns[0]
    unique_traits = report_df[trait_col].unique().tolist()
    
    missing_traits = set(EXPECTED_TRAITS) - set(unique_traits)
    if missing_traits:
        pytest.fail(f"Missing expected personality traits in report: {missing_traits}")
    
    # 2. Check genre count
    genre_columns = [col for col in report_df.columns if 'genre' in col.lower()]
    if not genre_columns:
        pytest.fail(f"Could not identify genre column in report. Columns found: {list(report_df.columns)}")
    
    genre_col = genre_columns[0]
    unique_genres = report_df[genre_col].unique().tolist()
    
    if len(unique_genres) < MIN_GENRES:
        pytest.fail(f"Report contains only {len(unique_genres)} unique genres. "
                    f"Minimum required: {MIN_GENRES}. Found: {unique_genres}")
    
    # 3. Verify cross-product coverage (all traits x genres)
    # We check that for every trait, there are at least MIN_GENRES entries
    for trait in EXPECTED_TRAITS:
        trait_rows = report_df[report_df[trait_col] == trait]
        if len(trait_rows) < MIN_GENRES:
            pytest.fail(f"Trait '{trait}' has only {len(trait_rows)} entries. "
                        f"Expected at least {MIN_GENRES} entries (one per genre).")
    
    # 4. Verify that the report contains the necessary statistical columns
    required_stats = ['rho', 'p_value', 'p_value_adj', 'is_significant']
    missing_stats = [stat for stat in required_stats if stat not in report_df.columns]
    if missing_stats:
        pytest.fail(f"Report is missing required statistical columns: {missing_stats}")