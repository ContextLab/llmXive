"""
Tests for Null Model Baseline Implementation (T020)
"""
import pytest
import json
import csv
import random
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from null_baseline import (
    load_importance_profiles,
    extract_window_rankings,
    calculate_rank_correlation,
    shuffle_windows_and_compute_rho,
    run_null_baseline,
    save_null_baseline
)


@pytest.fixture
def sample_profiles(tmp_path):
    """Create sample importance profiles for testing."""
    profiles_file = tmp_path / "importance_profiles.csv"
    
    data = [
        {"window_id": "window_0", "feature": "f1", "importance_score": 0.5},
        {"window_id": "window_0", "feature": "f2", "importance_score": 0.3},
        {"window_id": "window_0", "feature": "f3", "importance_score": 0.2},
        {"window_id": "window_1", "feature": "f1", "importance_score": 0.4},
        {"window_id": "window_1", "feature": "f2", "importance_score": 0.4},
        {"window_id": "window_1", "feature": "f3", "importance_score": 0.2},
        {"window_id": "window_2", "feature": "f1", "importance_score": 0.3},
        {"window_id": "window_2", "feature": "f2", "importance_score": 0.5},
        {"window_id": "window_2", "feature": "f3", "importance_score": 0.2},
    ]
    
    with open(profiles_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["window_id", "feature", "importance_score"])
        writer.writeheader()
        writer.writerows(data)
    
    return profiles_file


@pytest.fixture
def sample_window_data(sample_profiles):
    """Load sample window data from fixture."""
    profiles = load_importance_profiles(sample_profiles)
    return extract_window_rankings(profiles)


def test_load_importance_profiles(sample_profiles):
    """Test loading importance profiles from CSV."""
    profiles = load_importance_profiles(sample_profiles)
    
    assert len(profiles) == 9
    assert profiles[0]["window_id"] == "window_0"
    assert profiles[0]["feature"] == "f1"
    assert profiles[0]["importance_score"] == 0.5


def test_extract_window_rankings(sample_window_data):
    """Test extracting window rankings."""
    assert len(sample_window_data) == 3
    assert "window_0" in sample_window_data
    assert "f1" in sample_window_data["window_0"]
    assert sample_window_data["window_0"]["f1"] == 0.5


def test_calculate_rank_correlation_identical():
    """Test correlation calculation with identical rankings."""
    rankings_t = {"f1": 0.5, "f2": 0.3, "f3": 0.2}
    rankings_t1 = {"f1": 0.5, "f2": 0.3, "f3": 0.2}
    
    rho, p_value = calculate_rank_correlation(rankings_t, rankings_t1)
    
    assert rho == 1.0  # Perfect correlation
    assert p_value == 0.0


def test_calculate_rank_correlation_opposite():
    """Test correlation calculation with opposite rankings."""
    rankings_t = {"f1": 0.5, "f2": 0.3, "f3": 0.2}
    rankings_t1 = {"f1": 0.2, "f2": 0.3, "f3": 0.5}
    
    rho, p_value = calculate_rank_correlation(rankings_t, rankings_t1)
    
    # Should be negative correlation
    assert rho < 0


def test_shuffle_windows_and_compute_rho(sample_window_data):
    """Test shuffled window correlation calculation."""
    random.seed(42)
    rho = shuffle_windows_and_compute_rho(sample_window_data, 42)
    
    assert isinstance(rho, float)
    assert -1.0 <= rho <= 1.0


def test_run_null_baseline(sample_profiles, tmp_path):
    """Test full null baseline execution."""
    output_file = tmp_path / "null_baseline.json"
    
    # Run with minimal shuffles for speed
    result = run_null_baseline(num_shuffles=10, random_seed=42)
    
    assert result["status"] == "success"
    assert result["num_windows"] == 3
    assert result["num_shuffles"] == 10
    assert "original_mean_rho" in result
    assert "null_mean_rho" in result
    assert "p_value" in result
    assert -1.0 <= result["original_mean_rho"] <= 1.0
    assert -1.0 <= result["null_mean_rho"] <= 1.0
    assert 0.0 <= result["p_value"] <= 1.0


def test_save_null_baseline(sample_profiles, tmp_path):
    """Test saving null baseline results."""
    result = {
        "status": "success",
        "num_windows": 3,
        "num_shuffles": 10,
        "original_mean_rho": 0.5,
        "null_mean_rho": 0.1,
        "null_std_dev": 0.2,
        "null_variance": 0.04,
        "p_value": 0.3,
        "interpretation": "Test"
    }
    
    output_file = tmp_path / "null_baseline.json"
    save_null_baseline(result, output_file)
    
    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        saved = json.load(f)
    
    assert saved == result


def test_null_baseline_insufficient_windows(tmp_path):
    """Test null baseline with insufficient windows."""
    # Create profiles with only one window
    profiles_file = tmp_path / "importance_profiles.csv"
    
    data = [
        {"window_id": "window_0", "feature": "f1", "importance_score": 0.5},
        {"window_id": "window_0", "feature": "f2", "importance_score": 0.3},
    ]
    
    with open(profiles_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["window_id", "feature", "importance_score"])
        writer.writeheader()
        writer.writerows(data)
    
    profiles = load_importance_profiles(profiles_file)
    window_data = extract_window_rankings(profiles)
    
    result = run_null_baseline(num_shuffles=10, random_seed=42)
    
    assert result["status"] == "failed"
    assert result["reason"] == "Insufficient windows"
    assert result["num_windows"] == 1
