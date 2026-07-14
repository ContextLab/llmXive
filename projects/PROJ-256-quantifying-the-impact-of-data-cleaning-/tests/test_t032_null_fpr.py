"""
Unit tests for the permutation‑null FPR generation script (T032).

The tests exercise the core helper functions with a tiny synthetic dataset
to ensure they behave correctly without requiring the full raw‑data download.
"""

import json
import os
from pathlib import Path

import pandas as pd
import pytest

# Import the module under test
from t032_permutation_null_fpr import (
    _detect_outcome_column,
    _run_permutation,
    generate_null_fpr_metrics,
)
from utils import setup_logging

# --------------------------------------------------------------------------- #
# Helper fixtures
# --------------------------------------------------------------------------- #

@pytest.fixture
def tiny_dataset(tmp_path: Path) -> Path:
    """Create a minimal CSV file with a clear outcome column."""
    df = pd.DataFrame(
        {
            "feature1": [1, 2, 3, 4],
            "feature2": [5, 6, 7, 8],
            "target": [0, 1, 0, 1],
        }
    )
    csv_path = tmp_path / "tiny.csv"
    df.to_csv(csv_path, index=False)
    return csv_path

@pytest.fixture
def raw_dir(tmp_path: Path, tiny_dataset: Path) -> Path:
    """Directory mimicking ``data/raw`` containing the tiny CSV."""
    raw = tmp_path / "raw"
    raw.mkdir()
    tiny_dataset.rename(raw / tiny_dataset.name)
    return raw

# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #

def test_detect_outcome_column():
    df = pd.DataFrame(
        {
            "a": [1, 2],
            "b": [3, 4],
            "target": [0, 1],
        }
    )
    assert _detect_outcome_column(df) == "target"

    df2 = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
    # No explicit name – should pick the last column
    assert _detect_outcome_column(df2) == "y"

def test_run_permutation_collects_pvalues(monkeypatch):
    """
    Verify that ``_run_permutation`` returns a list of p‑values of the requested
    length and that the values are numeric (or NaN) without raising.
    """
    # Create a tiny DataFrame; the analysis function will be monkey‑patched
    df = pd.DataFrame(
        {"feat": [1, 2, 3, 4], "target": [0, 1, 0, 1]}
    )
    outcome = "target"

    # Stub ``run_baseline_analysis`` to return a deterministic p‑value
    def fake_run_baseline_analysis(*, dataframe=None, **kwargs):
        return {"t_test": {"p_value": 0.123}}

    monkeypatch.setattr("analysis.run_baseline_analysis", fake_run_baseline_analysis)

    logger = setup_logging(log_level="CRITICAL")
    p_vals = _run_permutation(df, outcome, n_perm=5, logger=logger)

    assert isinstance(p_vals, list)
    assert len(p_vals) == 5
    assert all(isinstance(p, float) for p in p_vals)
    assert all(p == 0.123 for p in p_vals)

def test_generate_null_fpr_metrics_writes_file(tmp_path: Path, raw_dir: Path):
    """
    End‑to‑end test that the public function creates the expected JSON file.
    The analysis function is stubbed to avoid heavy computation.
    """
    # Stub analysis to return a constant p‑value (so FPR is predictable)
    def fake_run_baseline_analysis(*, dataframe=None, **kwargs):
        return {"t_test": {"p_value": 0.04}}  # below α=0.05 → counted as FP

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr("analysis.run_baseline_analysis", fake_run_baseline_analysis)

    output_path = tmp_path / "null_fpr_metrics.json"
    results = generate_null_fpr_metrics(
        raw_dir=raw_dir,
        output_path=output_path,
        alpha=0.05,
        default_permutations=10,  # keep test fast
    )

    # Verify JSON file exists and content matches the returned dict
    assert output_path.is_file()
    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data == results
    # With a constant p‑value of 0.04, FPR should be 1.0
    for metric in data.values():
        assert metric["fpr"] == 1.0

    monkeypatch.undo()