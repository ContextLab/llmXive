"""
Basic sanity test for the T023 re‑analysis script.
The test only checks that the script creates the expected JSON file
when at least one cleaned CSV is present.
"""

import json
import os
from pathlib import Path

import pandas as pd

from t023_reanalyze_cleaned_variants import main as t023_main
from config import get_config

def test_t023_produces_cleaned_metrics(tmp_path, monkeypatch):
    # Setup a minimal processed directory with a fake cleaned CSV
    cfg = get_config()
    processed_dir = Path(cfg.get("PROCESSED_DATA_PATH", "data/processed"))
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir(parents=True)

    # Override config paths for the test
    monkeypatch.setattr(cfg, "get", lambda k, d=None: str(processed_dir) if k == "PROCESSED_DATA_PATH" else d)

    # Create a tiny cleaned dataset (binary outcome + one numeric predictor)
    df = pd.DataFrame(
        {
            "outcome": [0, 1, 0, 1],
            "feature": [1.2, 2.3, 1.1, 2.5],
        }
    )
    cleaned_csv = processed_dir / "sample_cleaned_iqr.csv"
    df.to_csv(cleaned_csv, index=False)

    # Run the script
    t023_main()

    # Verify output file exists and contains parsable JSON
    cleaned_metrics_path = Path(
        cfg.get(
            "CLEANED_METRICS_PATH",
            "data/processed/cleaned_metrics.json",
        )
    )
    assert cleaned_metrics_path.is_file()
    with open(cleaned_metrics_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, dict)
    assert "sample_cleaned_iqr" in data
    assert "analysis" in data["sample_cleaned_iqr"]
    assert "t_test" in data["sample_cleaned_iqr"]["analysis"]
    assert "regression" in data["sample_cleaned_iqr"]["analysis"]