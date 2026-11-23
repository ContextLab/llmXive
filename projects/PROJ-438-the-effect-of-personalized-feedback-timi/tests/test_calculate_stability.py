"""
Unit tests for calculate_stability.py (Task T033).

Tests the calculation of significance stability from sensitivity analysis results.
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from calculate_stability import (
    load_sensitivity_results,
    calculate_significance_stability,
    save_stability_report
)
from config import generate_default_config

@pytest.fixture
def mock_sensitivity_data():
    """Create mock sensitivity analysis data."""
    data = {
        'shift_type': [
            '2h_minus_0.01h', '2h_minus_0.05h', '2h_minus_0.1h',
            '2h_plus_0.01h', '2h_plus_0.05h', '2h_plus_0.1h',
            '48h_minus_0.01h', '48h_minus_0.05h', '48h_minus_0.1h',
            '48h_plus_0.01h', '48h_plus_0.05h', '48h_plus_0.1h'
        ],
        'comparison': [
            'Immediate vs Delayed', 'Immediate vs Delayed', 'Immediate vs Delayed',
            'Immediate vs Delayed', 'Immediate vs Delayed', 'Immediate vs Delayed',
            'Immediate vs Delayed', 'Immediate vs Delayed', 'Immediate vs Delayed',
            'Immediate vs Delayed', 'Immediate vs Delayed', 'Immediate vs Delayed'
        ],
        'p_value': [
            0.03, 0.04, 0.06,  # 2h shifts (2 significant, 1 not)
            0.02, 0.03, 0.04,  # 2h shifts (all significant)
            0.05, 0.07, 0.08,  # 48h shifts (1 significant, 2 not)
            0.04, 0.03, 0.02   # 48h shifts (all significant)
        ],
        'significant': [
            True, True, False,
            True, True, True,
            True, False, False,
            True, True, True
        ]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)

def test_load_sensitivity_results_missing_file(temp_dir):
    """Test that load_sensitivity_results raises FileNotFoundError for missing file."""
    config = generate_default_config()
    config['paths']['processed_data'] = temp_dir
    
    with pytest.raises(FileNotFoundError):
        load_sensitivity_results(config)

def test_calculate_significance_stability(mock_sensitivity_data):
    """Test calculation of significance stability."""
    # Expected: 8 out of 12 shifts are significant for "Immediate vs Delayed"
    # Stability = 8/12 = 0.6667
    
    results = calculate_significance_stability(mock_sensitivity_data)
    
    assert results['total_shifts'] == 12
    assert results['significant_count'] == 8
    assert abs(results['stability_proportion'] - (8/12)) < 1e-6
    assert abs(results['stability_percentage'] - (8/12 * 100)) < 1e-4
    assert results['target_comparison'] == "Immediate vs Delayed"
    assert 'breakdown' in results
    assert len(results['breakdown']) == 12

def test_calculate_significance_stability_empty_df():
    """Test that empty DataFrame raises ValueError."""
    empty_df = pd.DataFrame(columns=['comparison', 'p_value', 'significant'])
    
    with pytest.raises(ValueError):
        calculate_significance_stability(empty_df)

def test_calculate_significance_stability_no_target_comparison(mock_sensitivity_data):
    """Test that missing target comparison raises ValueError."""
    with pytest.raises(ValueError):
        calculate_significance_stability(
            mock_sensitivity_data, 
            target_comparison="Nonexistent Comparison"
        )

def test_save_stability_report(mock_sensitivity_data, temp_dir):
    """Test saving stability report to CSV."""
    results = calculate_significance_stability(mock_sensitivity_data)
    
    config = generate_default_config()
    config['paths']['processed_data'] = temp_dir
    
    output_path = save_stability_report(results, config)
    
    assert output_path.exists()
    assert output_path.name == 'significance_stability_report.csv'
    
    # Verify content
    df = pd.read_csv(output_path)
    assert len(df) == 1
    assert df.iloc[0]['metric'] == 'significance_stability'
    assert df.iloc[0]['total_shifts'] == 12
    assert df.iloc[0]['significant_count'] == 8
    assert abs(df.iloc[0]['stability_proportion'] - (8/12)) < 1e-6

def test_stability_interpretation():
    """Test that stability interpretation is correct based on proportion."""
    # High stability (>= 0.9)
    high_stability = {
        'stability_proportion': 0.95,
        'target_comparison': 'Test'
    }
    # Moderate stability (>= 0.7, < 0.9)
    moderate_stability = {
        'stability_proportion': 0.8,
        'target_comparison': 'Test'
    }
    # Low stability (< 0.7)
    low_stability = {
        'stability_proportion': 0.5,
        'target_comparison': 'Test'
    }
    
    # Test high
    config = generate_default_config()
    with tempfile.TemporaryDirectory() as temp_dir:
        config['paths']['processed_data'] = temp_dir
        save_stability_report(high_stability, config)
        df = pd.read_csv(Path(temp_dir) / 'significance_stability_report.csv')
        assert df.iloc[0]['interpretation'] == 'High stability'
    
    # Test moderate
    with tempfile.TemporaryDirectory() as temp_dir:
        config['paths']['processed_data'] = temp_dir
        save_stability_report(moderate_stability, config)
        df = pd.read_csv(Path(temp_dir) / 'significance_stability_report.csv')
        assert df.iloc[0]['interpretation'] == 'Moderate stability'
    
    # Test low
    with tempfile.TemporaryDirectory() as temp_dir:
        config['paths']['processed_data'] = temp_dir
        save_stability_report(low_stability, config)
        df = pd.read_csv(Path(temp_dir) / 'significance_stability_report.csv')
        assert df.iloc[0]['interpretation'] == 'Low stability'