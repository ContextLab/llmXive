"""
Unit tests for the power analysis module.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd
import numpy as np

# Import the module under test
# Note: We mock the config.Paths to avoid dependency on actual project structure in unit tests
from analysis.power import (
    calculate_effect_size_for_logistic,
    estimate_required_sample_size,
    perform_power_analysis,
    run_power_analysis,
    TARGET_EFFECT_SIZE_F2,
    TARGET_POWER,
    ALPHA
)

def test_calculate_effect_size_for_logistic():
    """Test that effect size calculation returns a reasonable value."""
    # Test with p0=0.5, p1=0.65 (medium effect heuristic)
    effect_size = calculate_effect_size_for_logistic(0.5, 0.65)
    
    # Cohen's h for 0.5 vs 0.65 should be positive and non-zero
    assert effect_size > 0
    assert effect_size < 2.0 # Upper bound for h

def test_estimate_required_sample_size():
    """Test sample size estimation."""
    # Use a known effect size (e.g., 0.5 for medium)
    # For alpha=0.05, power=0.80, effect=0.5, N should be around 100-150 for chi-square
    n = estimate_required_sample_size(0.5, alpha=0.05, power=0.80)
    
    assert isinstance(n, int)
    assert n > 0

def test_perform_power_analysis():
    """Test power calculation given sample size."""
    # If sample size is very large, power should be close to 1.0
    power_large = perform_power_analysis(10000, 0.5)
    assert power_large > 0.95
    
    # If sample size is very small, power should be low
    power_small = perform_power_analysis(10, 0.5)
    assert power_small < 0.5

@pytest.fixture
def mock_filtered_data():
    """Create a mock CSV file for testing."""
    data = {
        'task_id': range(100),
        'constraint_count': [5 + i % 5 for i in range(100)],
        'architecture': ['dual_track'] * 50 + ['monolithic'] * 50,
        'violation': [0] * 50 + [1] * 50
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        df.to_csv(f.name, index=False)
        return f.name

def test_run_power_analysis_success(mock_filtered_data):
    """Test the full power analysis pipeline with mock data."""
    try:
        report = run_power_analysis(data_path=Path(mock_filtered_data))
        
        assert 'actual_power' in report
        assert 'required_sample_size' in report
        assert 'passed' in report
        assert 'actual_sample_size' in report
        
        assert report['actual_sample_size'] == 100
        assert isinstance(report['actual_power'], float)
        
    finally:
        os.unlink(mock_filtered_data)

def test_run_power_analysis_empty_data(tmp_path):
    """Test that power analysis fails gracefully on empty data."""
    empty_csv = tmp_path / "empty.csv"
    empty_csv.write_text("task_id,constraint_count\n")
    
    with pytest.raises(ValueError, match="Filtered dataset is empty"):
        run_power_analysis(data_path=empty_csv)

def test_run_power_analysis_missing_file(tmp_path):
    """Test that power analysis fails gracefully on missing file."""
    missing_path = tmp_path / "nonexistent.csv"
    
    with pytest.raises(FileNotFoundError):
        run_power_analysis(data_path=missing_path)

def test_report_structure(mock_filtered_data):
    """Verify the report contains all required keys."""
    try:
        report = run_power_analysis(data_path=Path(mock_filtered_data))
        
        required_keys = [
            "target_effect_size_f2",
            "target_power",
            "alpha",
            "estimated_effect_size_cohens_h",
            "actual_sample_size",
            "required_sample_size",
            "actual_power",
            "passed",
            "data_source",
            "notes"
        ]
        
        for key in required_keys:
            assert key in report, f"Missing key: {key}"
    finally:
        os.unlink(mock_filtered_data)
