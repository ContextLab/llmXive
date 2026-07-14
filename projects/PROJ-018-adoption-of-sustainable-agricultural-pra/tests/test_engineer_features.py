"""Basic sanity test for the feature‑engineering script.

The test checks that the script creates the expected output files
when run on a minimal synthetic dataset.  The dataset is generated
on‑the‑fly to avoid dependence on external data sources.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

# Helper to create a tiny cleaned dataset
def _create_minimal_cleaned_data(tmp_path: Path) -> Path:
    data = {
        "age": [30, 45],
        "education": [12, 16],
        "farm_size": [2.5, 3.0],
        "membership": [1, 0],
        "extension": [0, 1],
        "collective_action": [1, 1],
        "knowledge_exchange": [0, 0],
        "practice_conservation": [1, 0],
        "practice_crop_rotation": [0, 1],
    }
    df = pd.DataFrame(data)
    cleaned_dir = Path("data/processed")
    cleaned_dir.mkdir(parents=True, exist_ok=True)
    cleaned_path = cleaned_dir / "cleaned_data.csv"
    df.to_csv(cleaned_path, index=False)
    return cleaned_path

@pytest.mark.integration
def test_engineer_features_produces_outputs(tmp_path: Path):
    # Ensure a clean environment
    for p in ["data/processed/engineered_data.csv", "results/validity_metrics.yaml"]:
        if Path(p).exists():
            Path(p).unlink()

    _create_minimal_cleaned_data(tmp_path)

    # Run the feature‑engineering script
    result = subprocess.run(
        [sys.executable, "code/03_engineer_features.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Verify engineered data exists and contains required columns
    engineered_path = Path("data/processed/engineered_data.csv")
    assert engineered_path.is_file(), "engineered_data.csv not created"
    engineered_df = pd.read_csv(engineered_path)
    for col in ["adoption_binary", "engagement_score"]:
        assert col in engineered_df.columns, f"Missing column {col}"

    # Verify validity metrics file exists and contains expected keys
    validity_path = Path("results/validity_metrics.yaml")
    assert validity_path.is_file(), "validity_metrics.yaml not created"
    with validity_path.open() as f:
        metrics = yaml.safe_load(f)
    for key in ["cronbach_alpha", "efa_n_factors", "efa_loadings"]:
        assert key in metrics, f"Missing metric {key}"