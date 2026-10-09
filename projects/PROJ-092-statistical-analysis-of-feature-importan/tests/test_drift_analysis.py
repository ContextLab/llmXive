"""
Unit tests for the pairwise drift calculation implemented in ``code/drift_analysis.py``.
The tests use a tiny synthetic dataset (real CSV files are created on‑the‑fly)
to verify that the core functions behave as expected.
"""

import csv
import json
import os
import tempfile
from pathlib import Path

import pytest

from drift_analysis import (
    calculate_rank_correlation,
    compute_pairwise_drift,
    extract_window_rankings,
    load_importance_profiles,
    save_drift_metrics,
)

@pytest.fixture
def synthetic_profiles_path():
    """Create a minimal but realistic importance_profiles.csv file."""
    rows = [
        {"window_id": "0", "feature_name": "A", "importance_score": "0.9"},
        {"window_id": "0", "feature_name": "B", "importance_score": "0.5"},
        {"window_id": "0", "feature_name": "C", "importance_score": "0.1"},
        {"window_id": "1", "feature_name": "A", "importance_score": "0.8"},
        {"window_id": "1", "feature_name": "B", "importance_score": "0.6"},
        {"window_id": "1", "feature_name": "C", "importance_score": "0.2"},
    ]
    with tempfile.NamedTemporaryFile(mode="w", delete=False, newline="", suffix=".csv") as tmp:
        writer = csv.DictWriter(tmp, fieldnames=["window_id", "feature_name", "importance_score"])
        writer.writeheader()
        writer.writerows(rows)
        return tmp.name

def test_load_and_extract(synthetic_profiles_path):
    profiles = load_importance_profiles(synthetic_profiles_path)
    assert len(profiles) == 6
    rankings = extract_window_rankings(profiles)
    assert rankings[0] == ["A", "B", "C"]
    assert rankings[1] == ["A", "B", "C"]

def test_calculate_rank_correlation():
    rankings_t = ["A", "B", "C"]
    rankings_t1 = ["A", "C", "B"]
    rho, p = calculate_rank_correlation(rankings_t, rankings_t1)
    # With only three items the exact rho is -0.5
    assert abs(rho + 0.5) < 1e-6
    assert 0.0 < p <= 1.0

def test_compute_pairwise_and_save(tmp_path: Path):
    # Use the synthetic profiles from the fixture
    profiles_path = synthetic_profiles_path()
    profiles = load_importance_profiles(profiles_path)
    rankings = extract_window_rankings(profiles)

    # Minimal null baseline and empty p‑value dict
    null_baseline = {"mean": 0.0}
    p_values = {}

    drift = compute_pairwise_drift(rankings, p_values, null_baseline)
    assert len(drift) == 1
    assert drift[0]["window_t"] == 0
    assert drift[0]["window_t1"] == 1

    output_csv = tmp_path / "drift_metrics.csv"
    save_drift_metrics(drift, str(output_csv))

    # Verify CSV content
    with open(output_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["window_t"] == "0"
        assert rows[0]["window_t1"] == "1"

# Helper to obtain the fixture path inside a test function
def synthetic_profiles_path():
    # Re‑use the fixture implementation logic without pytest fixture injection
    rows = [
        {"window_id": "0", "feature_name": "A", "importance_score": "0.9"},
        {"window_id": "0", "feature_name": "B", "importance_score": "0.5"},
        {"window_id": "0", "feature_name": "C", "importance_score": "0.1"},
        {"window_id": "1", "feature_name": "A", "importance_score": "0.8"},
        {"window_id": "1", "feature_name": "B", "importance_score": "0.6"},
        {"window_id": "1", "feature_name": "C", "importance_score": "0.2"},
    ]
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["window_id", "feature_name", "importance_score"])
        writer.writeheader()
        writer.writerows(rows)
    return path