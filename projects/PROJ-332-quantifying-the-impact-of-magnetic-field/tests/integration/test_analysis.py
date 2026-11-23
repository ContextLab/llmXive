"""
Integration Tests for Analysis Pipeline.

This module contains integration tests to verify the end-to-end analysis workflow.
"""
import pytest
import pandas as pd
import numpy as np
from analysis.correlation import run_correlation_analysis, check_power_sufficiency
from analysis.power_analysis import run_power_analysis
from analysis.report_generator import generate_final_report

def test_hypothesis_not_supported_flag():
    """
    Integration test for "Hypothesis Not Supported" flag logic.
    """
    # Create data with no correlation
    np.random.seed(42)
    x = np.random.normal(0, 1, 50)
    y = np.random.normal(0, 1, 50)
    df = pd.DataFrame({'x': x, 'y': y, 'mode': ['H-mode'] * 25 + ['L-mode'] * 25})
    
    # Run analysis
    corr_results = run_correlation_analysis(df)
    power_results = run_power_analysis(df)
    collinearity_results = {'collinearity_flag': False, 'excluded_variables': []}
    
    # Generate report
    report = generate_final_report(corr_results, power_results, collinearity_results, [])
    
    # Check hypothesis status
    if report['p_value'] >= 0.05:
        assert report['hypothesis_status'] == 'Not Supported'

def test_full_pipeline_with_realistic_data():
    """
    Integration test with realistic synthetic data.
    """
    np.random.seed(42)
    n = 50
    x = np.linspace(0, 1, n)
    y = -0.5 * x + np.random.normal(0, 0.1, n)  # Negative correlation
    df = pd.DataFrame({
        'island_width': x,
        'tau_e': y,
        'confinement_mode': ['H-mode'] * 25 + ['L-mode'] * 25
    })
    
    # Run power analysis
    power_results = run_power_analysis(df)
    assert power_results['sample_size'] == n
    
    # Run correlation
    corr_results = run_correlation_analysis(df)
    assert corr_results['r'] < 0, "Correlation should be negative"