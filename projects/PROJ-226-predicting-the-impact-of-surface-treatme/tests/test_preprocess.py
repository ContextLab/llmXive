"""
test_preprocess.py
------------------
Integration test for the preprocess pipeline (Task T004).
The test invokes ``code.preprocess.main`` and checks that the expected
output files are created and contain no missing values.
"""

import json
from pathlib import Path

import pandas as pd

from llmxive_toolkit import paths
from preprocess import main


def test_preprocess_outputs(tmp_path):
    """
    Run the preprocessing script and verify that:
    * data/cleaned/cleaned.csv exists and has no NaNs
    * data/cleaned/imputation_log.json and field_coverage.json are valid JSON
    """
    # Run the pipeline
    main()

    # Paths to expected artifacts
    cleaned_csv = paths.data("cleaned", "cleaned.csv")
    impute_json = paths.data("cleaned", "imputation_log.json")
    coverage_json = paths.data("cleaned", "field_coverage.json")

    # Verify files exist
    assert cleaned_csv.is_file(), f"Missing cleaned CSV at {cleaned_csv}"
    assert impute_json.is_file(), f"Missing imputation log at {impute_json}"
    assert coverage_json.is_file(), f"Missing coverage report at {coverage_json}"

    # Load cleaned data and ensure no missing values
    df = pd.read_csv(cleaned_csv)
    assert not df.isna().any().any(), "Cleaned data still contains missing values"

    # Load JSON artifacts to ensure they are well‑formed
    with impute_json.open("r", encoding="utf-8") as f:
        impute_log = json.load(f)
    with coverage_json.open("r", encoding="utf-8") as f:
        coverage = json.load(f)

    # Basic sanity checks on JSON structures
    assert isinstance(impute_log, dict), "Imputation log is not a dict"
    assert isinstance(coverage, dict), "Coverage report is not a dict"
    # Each column in coverage should have the required keys
    for col, info in coverage.items():
        assert "coverage_percent" in info and "low_coverage" in info, f"Incomplete coverage info for {col}"