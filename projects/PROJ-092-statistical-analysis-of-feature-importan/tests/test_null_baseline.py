import pytest
import json
import csv
import os
from pathlib import Path
import tempfile
import numpy as np

# Add code to path
import sys
project_root = Path(__file__).resolve().parent.parent
if (project_root / "code").exists():
    sys.path.insert(0, str(project_root))

from code.null_baseline import (
    load_importance_profiles,
    extract_window_rankings,
    calculate_rank_correlation,
    shuffle_windows_and_compute_rho,
    run_null_baseline
)

@pytest.fixture
def sample_profiles(tmp_path):
    """Create a sample importance_profiles.csv for testing."""
    profiles_path = tmp_path / "importance_profiles.csv"
    data = [
        {"window_id": 1, "feature_name": "f1", "importance_score": 0.5, "rank": 1},
        {"window_id": 1, "feature_name": "f2", "importance_score": 0.3, "rank": 2},
        {"window_id": 1, "feature_name": "f3", "importance_score": 0.2, "rank": 3},
        {"window_id": 2, "feature_name": "f1", "importance_score": 0.4, "rank": 1},
        {"window_id": 2, "feature_name": "f2", "importance_score": 0.35, "rank": 2},
        {"window_id": 2, "feature_name": "f3", "importance_score": 0.25, "rank": 3},
        {"window_id": 3, "feature_name": "f1", "importance_score": 0.6, "rank": 1},
        {"window_id": 3, "feature_name": "f2", "importance_score": 0.25, "rank": 2},
        {"window_id": 3, "feature_name": "f3", "importance_score": 0.15, "rank": 3},
    ]

    with open(profiles_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["window_id", "feature_name", "importance_score", "rank"])
        writer.writeheader()
        writer.writerows(data)

    return profiles_path

def test_load_importance_profiles(sample_profiles):
    """Test loading profiles from CSV."""
    profiles = load_importance_profiles(sample_profiles)
    assert len(profiles) == 9
    assert profiles[0]["window_id"] == 1
    assert profiles[0]["feature_name"] == "f1"
    assert profiles[0]["importance_score"] == 0.5

def test_extract_window_rankings(sample_profiles):
    """Test extracting and sorting window rankings."""
    profiles = load_importance_profiles(sample_profiles)
    rankings = extract_window_rankings(profiles)

    assert 1 in rankings
    assert 2 in rankings
    assert 3 in rankings

    # Check order (descending by importance)
    assert rankings[1][0][0] == "f1"  # f1 has highest importance in window 1
    assert rankings[1][1][0] == "f2"
    assert rankings[1][2][0] == "f3"

def test_calculate_rank_correlation():
    """Test Spearman correlation calculation."""
    ranks_a = ["f1", "f2", "f3"]
    ranks_b = ["f1", "f2", "f3"]

    rho, p_value = calculate_rank_correlation(ranks_a, ranks_b)
    assert rho == 1.0  # Perfect correlation

    ranks_c = ["f3", "f2", "f1"]  # Reverse order
    rho_rev, p_value_rev = calculate_rank_correlation(ranks_a, ranks_c)
    assert rho_rev == -1.0  # Perfect negative correlation

def test_shuffle_windows_and_compute_rho(sample_profiles):
    """Test shuffling windows and computing mean rho."""
    profiles = load_importance_profiles(sample_profiles)
    rankings = extract_window_rankings(profiles)

    # With 3 windows, we have 2 pairs. Shuffling should give different orderings.
    mean_rho = shuffle_windows_and_compute_rho(rankings, seed=42)

    # Result should be a float between -1 and 1
    assert isinstance(mean_rho, float)
    assert -1.0 <= mean_rho <= 1.0

def test_run_null_baseline(sample_profiles):
    """Test full null baseline calculation."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "null_baseline.json"
        result = run_null_baseline(sample_profiles, output_path, n_runs=10, base_seed=42)

        # Check result structure
        assert "mean_rho" in result
        assert "std_rho" in result
        assert "min_rho" in result
        assert "max_rho" in result
        assert "n_runs" in result
        assert result["n_runs"] == 10

        # Check file was created
        assert output_path.exists()

        # Check JSON content
        with open(output_path, "r") as f:
            saved_result = json.load(f)

        assert saved_result["mean_rho"] == result["mean_rho"]

def test_null_baseline_with_incomplete_windows(tmp_path):
    """Test handling of windows with different feature sets."""
    # Create profiles with mismatched features
    profiles_path = tmp_path / "importance_profiles.csv"
    data = [
        {"window_id": 1, "feature_name": "f1", "importance_score": 0.5, "rank": 1},
        {"window_id": 1, "feature_name": "f2", "importance_score": 0.3, "rank": 2},
        {"window_id": 2, "feature_name": "f1", "importance_score": 0.4, "rank": 1},
        {"window_id": 2, "feature_name": "f3", "importance_score": 0.25, "rank": 2},  # f2 missing, f3 added
    ]

    with open(profiles_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["window_id", "feature_name", "importance_score", "rank"])
        writer.writeheader()
        writer.writerows(data)

    rankings = extract_window_rankings(load_importance_profiles(profiles_path))

    # Should handle mismatch gracefully (return 0 or skip)
    mean_rho = shuffle_windows_and_compute_rho(rankings, seed=42)
    # Since features don't match, it should skip the pair and return 0.0
    assert mean_rho == 0.0
