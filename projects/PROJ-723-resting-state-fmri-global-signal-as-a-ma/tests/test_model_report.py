import json
import os
import tempfile
from pathlib import Path
import numpy as np
import pytest

from model_report import (
    load_existing_results,
    compute_null_distribution_stats,
    calculate_empirical_p_value,
    generate_model_report
)
from utils import write_json, read_json

@pytest.fixture
def temp_results_dir():
    """Create a temporary directory for test results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_load_existing_results_missing_files(temp_results_dir):
    """Test loading results when files are missing."""
    results = load_existing_results(temp_results_dir)
    
    assert results["null_distribution"] is None
    assert results["delta_r2"] is None

def test_load_existing_results_with_files(temp_results_dir):
    """Test loading results when files exist."""
    # Create mock null distribution file
    null_data = {
        "mae_values": [0.1, 0.2, 0.3, 0.4, 0.5],
        "count": 5
    }
    write_json(temp_results_dir / "null_distribution.json", null_data)
    
    # Create mock delta_r2 file
    delta_r2_data = {
        "delta_r2": 0.05,
        "status": "success",
        "full_model_r2": 0.2,
        "reduced_model_r2": 0.15
    }
    write_json(temp_results_dir / "delta_r2.json", delta_r2_data)
    
    results = load_existing_results(temp_results_dir)
    
    assert results["null_distribution"] is not None
    assert results["delta_r2"] is not None
    assert results["null_distribution"]["count"] == 5
    assert results["delta_r2"]["delta_r2"] == 0.05

def test_compute_null_distribution_stats():
    """Test computing statistics from null distribution."""
    null_data = {
        "mae_values": [0.1, 0.2, 0.3, 0.4, 0.5]
    }
    
    stats = compute_null_distribution_stats(null_data)
    
    assert stats["mean"] == 0.3
    assert stats["std"] == pytest.approx(0.1414, rel=0.01)
    assert stats["min"] == 0.1
    assert stats["max"] == 0.5
    assert stats["count"] == 5

def test_compute_null_distribution_stats_none():
    """Test computing statistics when null data is None."""
    stats = compute_null_distribution_stats(None)
    
    assert stats["mean"] == 0.0
    assert stats["std"] == 0.0
    assert stats["min"] == 0.0
    assert stats["max"] == 0.0
    assert stats["count"] == 0

def test_calculate_empirical_p_value():
    """Test calculating empirical p-value."""
    null_data = {
        "mae_values": [0.1, 0.2, 0.3, 0.4, 0.5]
    }
    observed_mae = 0.25
    
    # count(mae <= 0.25) = 2 (0.1, 0.2)
    # p = (2 + 1) / (5 + 1) = 3/6 = 0.5
    p_value = calculate_empirical_p_value(null_data, observed_mae)
    
    assert p_value == 0.5

def test_calculate_empirical_p_value_none():
    """Test calculating p-value when null data is None."""
    p_value = calculate_empirical_p_value(None, 0.25)
    
    assert p_value == 1.0

def test_generate_model_report(temp_results_dir):
    """Test generating the complete model report."""
    # Create mock null distribution file
    null_data = {
        "mae_values": [0.1, 0.2, 0.3, 0.4, 0.5],
        "count": 5
    }
    write_json(temp_results_dir / "null_distribution.json", null_data)
    
    # Create mock delta_r2 file
    delta_r2_data = {
        "delta_r2": 0.05,
        "status": "success",
        "full_model_r2": 0.2,
        "reduced_model_r2": 0.15
    }
    write_json(temp_results_dir / "delta_r2.json", delta_r2_data)
    
    # Observed metrics
    observed_metrics = {
        "mean_mae": 0.18,
        "mean_r": 0.35,
        "mean_r2": 0.12,
        "observed_mae": 0.18
    }
    
    output_path = temp_results_dir / "model_report.json"
    report = generate_model_report(
        base_path=temp_results_dir,
        output_path=output_path,
        observed_metrics=observed_metrics
    )
    
    # Verify the report structure
    assert report["mean_mae"] == 0.18
    assert report["mean_r"] == 0.35
    assert report["mean_r2"] == 0.12
    assert report["p_value"] == 0.5  # Calculated from null distribution
    assert report["observed_mae"] == 0.18
    assert report["permutation_count"] == 5
    assert report["null_distribution_stats"]["count"] == 5
    assert report["reduced_model_stats"]["delta_r2"] == 0.05
    
    # Verify file was written
    assert output_path.exists()
    written_report = read_json(output_path)
    assert written_report == report