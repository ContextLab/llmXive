"""
Test suite for calculate_flip_rate.py (T034)
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path
project_root = Path(__file__).parent.parent
code_dir = project_root / "code"
sys.path.insert(0, str(code_dir))

from calculate_flip_rate import (
    calculate_significance_flip_rate,
    save_flip_rate_report,
    load_flip_rate_config
)

@pytest.fixture
def sample_baseline():
    """Create a sample baseline DataFrame."""
    data = {
        'comparison': ['Immediate_vs_Delayed', 'Immediate_vs_Variable', 'Delayed_vs_Variable'],
        'p_value': [0.03, 0.15, 0.01],
        'effect_size': [0.35, 0.12, 0.45]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_sensitivity():
    """Create a sample sensitivity DataFrame with some flips."""
    data = {
        'comparison': [
            'Immediate_vs_Delayed', 'Immediate_vs_Delayed',
            'Immediate_vs_Variable', 'Immediate_vs_Variable',
            'Delayed_vs_Variable', 'Delayed_vs_Variable'
        ],
        'run_id': [
            'shift_2h_plus_0.01', 'shift_2h_minus_0.01',
            'shift_48h_plus_0.01', 'shift_48h_minus_0.01',
            'shift_2h_plus_0.01', 'shift_2h_minus_0.01'
        ],
        'p_value': [
            0.06,  # Flip: 0.03 -> 0.06 (sig -> not sig)
            0.04,  # No flip: 0.03 -> 0.04 (sig -> sig)
            0.12,  # No flip: 0.15 -> 0.12 (not sig -> not sig)
            0.18,  # No flip: 0.15 -> 0.18 (not sig -> not sig)
            0.02,  # No flip: 0.01 -> 0.02 (sig -> sig)
            0.09   # Flip: 0.01 -> 0.09 (sig -> not sig)
        ]
    }
    return pd.DataFrame(data)

def test_calculate_flip_rate_basic(sample_baseline, sample_sensitivity):
    """Test basic flip rate calculation."""
    flip_rate, details = calculate_significance_flip_rate(
        sample_baseline, 
        sample_sensitivity, 
        threshold=0.05
    )
    
    # Expected flips: 
    # 1. Immediate_vs_Delayed: 0.03 (sig) -> 0.06 (not sig) = FLIP
    # 2. Immediate_vs_Delayed: 0.03 (sig) -> 0.04 (sig) = NO FLIP
    # 3. Immediate_vs_Variable: 0.15 (not sig) -> 0.12 (not sig) = NO FLIP
    # 4. Immediate_vs_Variable: 0.15 (not sig) -> 0.18 (not sig) = NO FLIP
    # 5. Delayed_vs_Variable: 0.01 (sig) -> 0.02 (sig) = NO FLIP
    # 6. Delayed_vs_Variable: 0.01 (sig) -> 0.09 (not sig) = FLIP
    # Total: 2 flips out of 6 comparisons
    
    expected_rate = 2 / 6
    assert abs(flip_rate - expected_rate) < 1e-6
    assert len(details) == 6
    assert details['flip'].sum() == 2

def test_calculate_flip_rate_no_flips():
    """Test when no flips occur."""
    baseline = pd.DataFrame({
        'comparison': ['A_vs_B'],
        'p_value': [0.01]
    })
    sensitivity = pd.DataFrame({
        'comparison': ['A_vs_B', 'A_vs_B'],
        'run_id': ['run1', 'run2'],
        'p_value': [0.02, 0.03]
    })
    
    flip_rate, details = calculate_significance_flip_rate(
        baseline, sensitivity, threshold=0.05
    )
    
    assert flip_rate == 0.0
    assert all(not f for f in details['flip'])

def test_calculate_flip_rate_all_flips():
    """Test when all comparisons flip."""
    baseline = pd.DataFrame({
        'comparison': ['A_vs_B'],
        'p_value': [0.01]
    })
    sensitivity = pd.DataFrame({
        'comparison': ['A_vs_B', 'A_vs_B'],
        'run_id': ['run1', 'run2'],
        'p_value': [0.06, 0.07]  # Both flip from sig to not sig
    })
    
    flip_rate, details = calculate_significance_flip_rate(
        baseline, sensitivity, threshold=0.05
    )
    
    assert flip_rate == 1.0
    assert all(f for f in details['flip'])

def test_calculate_flip_rate_empty_baseline():
    """Test with empty baseline raises error."""
    baseline = pd.DataFrame(columns=['comparison', 'p_value'])
    sensitivity = pd.DataFrame({
        'comparison': ['A_vs_B'],
        'run_id': ['run1'],
        'p_value': [0.05]
    })
    
    with pytest.raises(ValueError, match="Baseline results DataFrame is empty"):
        calculate_significance_flip_rate(baseline, sensitivity)

def test_calculate_flip_rate_empty_sensitivity():
    """Test with empty sensitivity raises error."""
    baseline = pd.DataFrame({
        'comparison': ['A_vs_B'],
        'p_value': [0.05]
    })
    sensitivity = pd.DataFrame(columns=['comparison', 'run_id', 'p_value'])
    
    with pytest.raises(ValueError, match="Sensitivity results DataFrame is empty"):
        calculate_significance_flip_rate(baseline, sensitivity)

def test_save_flip_rate_report(tmp_path, sample_baseline, sample_sensitivity):
    """Test saving flip rate report."""
    flip_rate, details = calculate_significance_flip_rate(
        sample_baseline, sample_sensitivity, threshold=0.05
    )
    
    output_file = tmp_path / "test_flip_rate_report.csv"
    save_flip_rate_report(flip_rate, details, output_file)
    
    assert output_file.exists()
    report_df = pd.read_csv(output_file)
    assert 'metric' in report_df.columns
    assert report_df.loc[0, 'metric'] == 'significance_flip_rate'
    assert abs(report_df.loc[0, 'value'] - flip_rate) < 1e-6
    
    # Check detailed file was also created
    detailed_file = tmp_path / "test_flip_rate_report_details.csv"
    assert detailed_file.exists()

def test_load_flip_rate_config():
    """Test loading configuration."""
    config = load_flip_rate_config()
    assert 'sensitivity' in config
    assert 'threshold' in config['sensitivity']
    assert isinstance(config['sensitivity']['threshold'], float)