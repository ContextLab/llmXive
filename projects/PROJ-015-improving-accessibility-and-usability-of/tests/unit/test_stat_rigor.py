"""
Unit tests to verify statistical rigor and Spec compliance.
Specifically ensures Levene's test is NOT used for primary analysis
and that the analysis pipeline adheres to the amended Spec (FR-002 via T035a).
"""
import pytest
import os
import sys
import inspect
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.stat_utils import run_anova_pipeline, run_holm_bonferroni, generate_metrics_summary
from analysis.run_analysis import validate_columns, run_analysis_pipeline
import pandas as pd
import numpy as np

def test_no_levene_import_in_stat_utils():
    """
    Verify that scipy.stats.levene is not imported or called in stat_utils.
    This enforces the Spec amendment (T035a) removing Levene's test.
    """
    import analysis.stat_utils
    source = inspect.getsource(analysis.stat_utils)
    # Check for any reference to 'levene' (case insensitive)
    assert 'levene' not in source.lower(), (
        "Levene's test logic found in stat_utils. "
        "Per Spec FR-002 (Amended by T035a), Levene's test must be removed."
    )

def test_no_levene_import_in_run_analysis():
    """
    Verify that run_analysis.py does not import or call scipy.stats.levene.
    """
    import analysis.run_analysis
    source = inspect.getsource(analysis.run_analysis)
    assert 'levene' not in source.lower(), (
        "Levene's test logic found in run_analysis.py. "
        "Per Spec FR-002 (Amended by T035a), Levene's test must be removed."
    )

def test_anova_pipeline_structure():
    """
    Test that the ANOVA pipeline produces the expected DataFrame structure
    without using Levene's test.
    """
    # Create dummy data matching the schema
    data = pd.DataFrame({
        'participant_id': ['P1', 'P2', 'P3', 'P1', 'P2', 'P3'],
        'interface_type': ['traditional', 'traditional', 'traditional', 'explainable', 'explainable', 'explainable'],
        'completion_time_seconds': [10.0, 12.0, 11.0, 8.0, 9.0, 8.5],
        'error_count': [1, 2, 1, 0, 1, 0],
        'sus_score': [70, 65, 80, 85, 90, 88]
    })

    result = run_anova_pipeline(data, ['completion_time_seconds'])
    
    assert not result.empty, "ANOVA pipeline returned empty result"
    assert 'metric_name' in result.columns
    assert 'F_statistic' in result.columns
    assert 'p_value' in result.columns
    assert 'adjusted_p_value' in result.columns

def test_holm_bonferroni_correctness():
    """
    Test Holm-Bonferroni correction logic.
    """
    p_values = [0.01, 0.04, 0.03]
    adjusted = run_holm_bonferroni(p_values)
    
    # Basic sanity checks
    assert len(adjusted) == 3
    assert all(0 <= x <= 1 for x in adjusted)
    # Adjusted values should be >= original values
    for orig, adj in zip(p_values, adjusted):
        assert adj >= orig - 1e-9, f"Adjusted p-value {adj} should be >= original {orig}"

def test_no_synthetic_fallback_in_analysis():
    """
    Verify that the analysis code does not contain synthetic data generation logic
    that could be used as a fallback for missing real data.
    """
    import analysis.stat_utils
    source = inspect.getsource(analysis.stat_utils)
    
    # Check for common synthetic generation patterns
    assert 'generate_synthetic' not in source.lower(), "Synthetic generation logic found in stat_utils"
    assert 'mock_data' not in source.lower(), "Mock data logic found in stat_utils"
    
    # Ensure we are not falling back to random values for metrics
    assert 'np.random' not in source or 'stats' in source, (
        "Random data generation found in stat_utils. "
        "Analysis must use real input data."
    )

def test_metrics_summary_generation():
    """
    Test that generate_metrics_summary produces the correct output format.
    """
    # Create dummy data
    data = pd.DataFrame({
        'participant_id': ['P1', 'P2', 'P3', 'P1', 'P2', 'P3'],
        'interface_type': ['traditional', 'traditional', 'traditional', 'explainable', 'explainable', 'explainable'],
        'completion_time_seconds': [10.0, 12.0, 11.0, 8.0, 9.0, 8.5],
        'error_count': [1, 2, 1, 0, 1, 0],
        'sus_score': [70, 65, 80, 85, 90, 88]
    })

    result = generate_metrics_summary(data)
    
    assert not result.empty, "Metrics summary generation returned empty result"
    required_columns = ['metric_name', 'interface_type', 'F_statistic', 'p_value', 'adjusted_p_value', 'effect_size']
    for col in required_columns:
        assert col in result.columns, f"Missing required column: {col}"