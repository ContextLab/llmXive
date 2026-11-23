"""
Unit test for the T009 preprocessing script.

The test invokes the script's `main` function and then checks that the three
expected output artifacts have been created and contain sensible structures.
"""
import json
from pathlib import Path

import pytest

from code.data.preprocess import main as preprocess_main
from llmxive_toolkit import paths

@pytest.fixture(scope="module")
def run_preprocess():
    """Run the preprocessing step once for the test module."""
    exit_code = preprocess_main()
    assert exit_code == 0, "Preprocess script exited with non‑zero status"
    yield

def test_monthly_parquet_exists(run_preprocess):
    parquet_path = paths.data("processed", "monthly_tag_counts.parquet")
    assert parquet_path.exists(), f"{parquet_path} was not created"
    # Basic sanity check – try to read a few rows
    try:
        import pandas as pd

        df = pd.read_parquet(parquet_path, engine="pyarrow")
    except Exception:
        # Fall back to fastparquet if pyarrow is unavailable
        df = pd.read_parquet(parquet_path, engine="fastparquet")
    assert not df.empty, "Monthly tag counts Parquet is empty"
    # Expect the required columns
    for col in ["tag", "year_month", "count"]:
        assert col in df.columns, f"Column {col} missing in Parquet file"

def test_top_50_tags_json(run_preprocess):
    json_path = paths.data("processed", "top_50_tags.json")
    assert json_path.exists(), f"{json_path} was not created"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list), "Top‑50 tags JSON should be a list"
    assert 0 < len(data) <= 50, "Top‑50 tags list length invalid"
    # All entries should be strings
    assert all(isinstance(tag, str) for tag in data), "All tags must be strings"

def test_data_sufficiency_report(run_preprocess):
    json_path = paths.data("processed", "data_sufficiency_report.json")
    assert json_path.exists(), f"{json_path} was not created"
    with open(json_path, "r", encoding="utf-8") as f:
        report = json.load(f)
    required_keys = {
        "total_tags_considered",
        "tags_meeting_min_months",
        "tags_filtered_out",
        "min_months_required",
    }
    assert isinstance(report, dict), "Report should be a JSON object"
    assert required_keys.issubset(report.keys()), "Missing keys in sufficiency report"