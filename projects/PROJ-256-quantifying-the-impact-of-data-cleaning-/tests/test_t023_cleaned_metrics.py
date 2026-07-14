"""
Unit test for the cleaned‑variant re‑analysis script (T023).
The test runs the script on a tiny synthetic dataset to verify that
``cleaned_metrics.json`` is created and contains the expected keys.
"""

import json
import os
import shutil
from pathlib import Path

import pandas as pd
import pytest

from t023_reanalyze_cleaned_variants import main as reanalyze_main
from config import get_config

@pytest.fixture(scope="function")
def temporary_processed_dir(tmp_path):
    """Create a temporary processed directory with a single cleaned CSV."""
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir(parents=True)

    # Small synthetic dataset
    df = pd.DataFrame(
        {
            "feature1": [1, 2, 3, 4, 5],
            "feature2": [5, 4, 3, 2, 1],
            "target": [0, 1, 0, 1, 0],
        }
    )
    csv_path = processed_dir / "synthetic_cleaned.csv"
    df.to_csv(csv_path, index=False)

    # Patch the config to point to this temporary location
    cfg = get_config()
    cfg_path = Path(cfg.get("CONFIG_PATH", ""))
    # Monkey‑patch the config values in memory (the Config object reads env vars)
    cfg._overrides = {
        "PROCESSED_DATA_PATH": str(processed_dir),
        "CLEANED_METRICS_PATH": str(tmp_path / "cleaned_metrics.json"),
        "OUTCOME_COLUMN": "target",
    }

    yield tmp_path

    # Cleanup – nothing needed because tmp_path is auto‑removed

def test_cleaned_metrics_file_created(temporary_processed_dir):
    # Run the re‑analysis script
    reanalyze_main()

    output_path = Path(
        get_config().get(
            "CLEANED_METRICS_PATH",
            "data/processed/cleaned_metrics.json",
        )
    )
    assert output_path.is_file(), "cleaned_metrics.json was not created"

    with output_path.open() as f:
        data = json.load(f)

    # Expect a list with one entry
    assert isinstance(data, list) and len(data) == 1
    entry = data[0]
    assert "dataset_name" in entry
    assert entry["dataset_name"] == "synthetic_cleaned"
    assert "analysis" in entry
    assert isinstance(entry["analysis"], dict)
    # Basic sanity checks on analysis sub‑structure
    assert "t_test" in entry["analysis"]
    assert "regression" in entry["analysis"]