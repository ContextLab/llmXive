import os
from pathlib import Path

import pandas as pd
import pytest

# Ensure the project code is importable
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from fetcher import (
    bootstrap_performance_resampling,
    fetch_historical_window,
    compare_current_vs_historical,
)

def test_bootstrap_and_stability(tmp_path):
    """
    Verify that bootstrap resampling creates the expected CSV,
    that the historical window directory is populated, and that the
    stability score meets the required threshold (>= 0.7).
    """
    # 1. Run bootstrap (use a modest number of samples for speed)
    bootstrap_path = bootstrap_performance_resampling(num_samples=200, seed=123)
    assert Path(bootstrap_path).exists()
    df_boot = pd.read_csv(bootstrap_path)
    assert "sample_id" in df_boot.columns
    assert len(df_boot) > 0

    # 2. Populate historical window
    hist_dir = fetch_historical_window(days=30)
    assert Path(hist_dir).exists()
    assert any(hist_dir.glob("*.json")), "Historical directory should contain JSON files."

    # 3. Compute stability score
    score_path = compare_current_vs_historical()
    assert Path(score_path).exists()
    with open(score_path, "r", encoding="utf-8") as f:
        score = float(f.read().strip())
    # The stability requirement from the specification is >= 0.7
    assert score >= 0.7, f"Stability score too low: {score}"