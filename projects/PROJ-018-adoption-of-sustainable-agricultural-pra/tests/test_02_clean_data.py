"""Integration test for the ``02_clean_data`` pipeline.

The test ensures that the pipeline runs end‑to‑end on a tiny synthetic
dataset (generated on‑the‑fly) and that the expected output file exists.
"""

import csv
import os
from pathlib import Path

import pandas as pd
import pytest

from code import config
from code._02_clean_data import main as clean_main  # type: ignore

@pytest.fixture(scope="module")
def synthetic_raw_file(tmp_path_factory):
    """Create a minimal raw CSV with the required columns."""
    tmp_dir = tmp_path_factory.mktemp("raw")
    path = tmp_dir / "survey_data.csv"
    rows = [
        {
            "age": 35,
            "education": "primary",
            "farm_size": 1.2,
            "credit": 500,
            "adoption": 1,
            "engagement_membership": "yes",
            "engagement_extension": "no",
            "engagement_collective_action": "yes",
            "engagement_knowledge_exchange": "yes",
        },
        {
            "age": None,
            "education": None,
            "farm_size": None,
            "credit": None,
            "adoption": 0,
            "engagement_membership": None,
            "engagement_extension": None,
            "engagement_collective_action": None,
            "engagement_knowledge_exchange": None,
        },
    ]
    pd.DataFrame(rows).to_csv(path, index=False)
    return path

def test_clean_data_produces_output(tmp_path, synthetic_raw_file, monkeypatch):
    # Point the config to the temporary raw directory.
    raw_dir = synthetic_raw_file.parent
    processed_dir = tmp_path / "processed"
    monkeypatch.setattr(
        config,
        "get_raw_data_path",
        lambda: raw_dir,
    )
    monkeypatch.setattr(
        config,
        "get_processed_data_path",
        lambda: processed_dir,
    )
    # Run the cleaning script.
    clean_main([])
    # Verify the cleaned file exists and has the expected shape.
    cleaned_path = processed_dir / "cleaned_data.csv"
    assert cleaned_path.is_file()
    df = pd.read_csv(cleaned_path)
    # After dropping the row with >30% missing, only one row should remain.
    assert len(df) == 1
    # All original columns should still be present (now numeric codes).
    expected_cols = [
        "age",
        "education",
        "farm_size",
        "credit",
        "adoption",
        "engagement_membership",
        "engagement_extension",
        "engagement_collective_action",
        "engagement_knowledge_exchange",
    ]
    for col in expected_cols:
        assert col in df.columns