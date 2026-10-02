import os
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis import welch_t_test, calculate_cohen_d, bonferroni_correction, calculate_power_and_mdes

RESULTS_DIR = Path("data/results")

@pytest.fixture
def sample_cleaned_data(tmp_path):
    """Create a temporary cleaned dataset for testing."""
    # Create data with known effect size
    # Group 1 (Nostalgia): mean=5, std=1
    # Group 2 (Control): mean=7, std=1
    # Cohen's d should be approx 2.0
    np.random.seed(42)
    n = 50
    nostalgia_pe = np.random.normal(5, 1, n)
    control_pe = np.random.normal(7, 1, n)
    
    data = {
        'stimulus_type': ['nostalgia'] * n + ['control'] * n,
        'perseverative_errors': list(nostalgia_pe) + list(control_pe),
        'categories_completed': [6] * n + [4] * n # Simple difference
    }
    df = pd.DataFrame(data)
    path = tmp_path / "cleaned_dataset.csv"
    df.to_csv(path, index=False)
    return path

def test_welch_t_test_integration(sample_cleaned_data):
    """Test that Welch's t-test runs successfully on cleaned data."""
    df = pd.read_csv(sample_cleaned_data)
    
    nostalgia_group = df[df['stimulus_type'] == 'nostalgia']['perseverative_errors']
    control_group = df[df['stimulus_type'] == 'control']['perseverative_errors']
    
    # Run Welch's t-test
    t_stat, p_value = welch_t_test(nostalgia_group, control_group)
    
    # Verify results
    assert isinstance(t_stat, float), "t-statistic should be a float"
    assert isinstance(p_value, float), "p-value should be a float"
    assert 0 <= p_value <= 1, "p-value should be between 0 and 1"
    
    # With the known effect size, p-value should be very small
    assert p_value < 0.05, "Expected significant difference with large effect size"

def test_cohen_d_calculation(sample_cleaned_data):
    """Test that Cohen's d is calculated correctly."""
    df = pd.read_csv(sample_cleaned_data)
    
    nostalgia_group = df[df['stimulus_type'] == 'nostalgia']['perseverative_errors']
    control_group = df[df['stimulus_type'] == 'control']['perseverative_errors']
    
    cohen_d = calculate_cohen_d(nostalgia_group, control_group)
    
    # Verify results
    assert isinstance(cohen_d, float), "Cohen's d should be a float"
    
    # With means 5 and 7, and std 1, Cohen's d should be approx 2.0
    assert abs(cohen_d - 2.0) < 0.5, "Cohen's d should be approximately 2.0"
    
def test_analysis_output_structure(sample_cleaned_data, tmp_path):
    """Test that the analysis output has the correct structure."""
    df = pd.read_csv(sample_cleaned_data)
    
    nostalgia_group = df[df['stimulus_type'] == 'nostalgia']['perseverative_errors']
    control_group = df[df['stimulus_type'] == 'control']['perseverative_errors']
    
    t_stat, p_value = welch_t_test(nostalgia_group, control_group)
    cohen_d = calculate_cohen_d(nostalgia_group, control_group)
    
    # Create a mock report
    report = {
        'p_values': {'perseverative_errors': p_value},
        'effect_sizes': {'perseverative_errors': {'cohen_d': cohen_d}}
    }
    
    output_path = tmp_path / "test_report.json"
    with open(output_path, 'w') as f:
        json.dump(report, f)
    
    # Verify structure
    with open(output_path, 'r') as f:
        loaded_report = json.load(f)
    
    assert 'p_values' in loaded_report
    assert 'effect_sizes' in loaded_report
    assert 'perseverative_errors' in loaded_report['p_values']
    assert 'perseverative_errors' in loaded_report['effect_sizes']

def test_bonferroni_correction(sample_cleaned_data):
    """Test Bonferroni correction logic."""
    # Simulate raw p-values
    raw_p_values = [0.01, 0.04, 0.08, 0.15]
    n_tests = len(raw_p_values)
    
    corrected_p_values = bonferroni_correction(raw_p_values)
    
    assert len(corrected_p_values) == n_tests
    for p in corrected_p_values:
        assert 0 <= p <= 1, "Corrected p-value must be between 0 and 1"
    
    # The corrected values should be larger than raw values (capped at 1)
    for raw, corr in zip(raw_p_values, corrected_p_values):
        assert corr >= raw, "Bonferroni correction should increase p-values"

def test_power_and_mdes_calculation(sample_cleaned_data):
    """Test power and MDES calculation."""
    df = pd.read_csv(sample_cleaned_data)
    
    nostalgia_group = df[df['stimulus_type'] == 'nostalgia']['perseverative_errors']
    control_group = df[df['stimulus_type'] == 'control']['perseverative_errors']
    
    power, mdes = calculate_power_and_mdes(nostalgia_group, control_group)
    
    assert isinstance(power, float), "Power should be a float"
    assert isinstance(mdes, float), "MDES should be a float"
    assert 0 <= power <= 1, "Power should be between 0 and 1"
    assert mdes > 0, "MDES should be positive"

def test_full_pipeline_integration(sample_cleaned_data, tmp_path):
    """End-to-end integration test for the analysis pipeline."""
    from analysis import run_analysis
    
    df = pd.read_csv(sample_cleaned_data)
    
    # Run the full analysis pipeline
    results = run_analysis(df)
    
    # Verify the structure of the results
    assert 'perseverative_errors' in results
    assert 'categories_completed' in results
    
    # Check for expected keys in each metric
    for metric in ['perseverative_errors', 'categories_completed']:
        assert 't_statistic' in results[metric]
        assert 'p_value' in results[metric]
        assert 'cohen_d' in results[metric]
        assert 'power' in results[metric]
        assert 'mdes' in results[metric]
    
    # Verify types
    assert isinstance(results['perseverative_errors']['p_value'], float)
    assert isinstance(results['categories_completed']['p_value'], float)