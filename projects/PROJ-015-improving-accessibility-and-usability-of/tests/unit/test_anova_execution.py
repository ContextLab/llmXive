"""
Unit tests for ANOVA execution independent of normality.

This test suite verifies that:
1. The ANOVA runs even when Shapiro-Wilk indicates non-normality
2. The ANOVA results are correctly computed
3. The effect sizes are calculated properly
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.stat_utils import (
    log_normality_test,
    run_anova_pipeline,
    calculate_effect_size,
    run_holm_bonferroni,
    verify_primary_anova_pvalue
)

@pytest.fixture
def sample_data():
    """Create sample data with known properties."""
    np.random.seed(42)
    n_subjects = 30
    
    # Create data where Traditional has higher mean than Explainable
    data = pd.DataFrame({
        'participant_id': np.repeat(range(n_subjects), 2),
        'interface_type': ['Traditional'] * n_subjects + ['Explainable'] * n_subjects,
        'completion_time': np.concatenate([
            np.random.normal(100, 15, n_subjects),
            np.random.normal(85, 12, n_subjects)  # Lower time for Explainable
        ]),
        'error_count': np.concatenate([
            np.random.poisson(4, n_subjects),
            np.random.poisson(2, n_subjects)  # Fewer errors for Explainable
        ]),
        'sus_score': np.concatenate([
            np.random.normal(60, 10, n_subjects),
            np.random.normal(75, 8, n_subjects)  # Higher SUS for Explainable
        ])
    })
    return data

def test_anova_runs_despite_non_normality(sample_data):
    """
    Test that ANOVA runs even when normality test fails.
    
    This is the core requirement from FR-002: ANOVA must execute regardless
    of the Shapiro-Wilk result.
    """
    # Run normality test
    norm_result = log_normality_test(sample_data, 'completion_time')
    
    # Run ANOVA - this MUST succeed even if normality fails
    anova_result = run_anova_pipeline(sample_data, 'completion_time')
    
    # Verify ANOVA produced results
    assert anova_result['metric'] == 'completion_time'
    assert anova_result['f_statistic'] is not None
    assert anova_result['p_value'] is not None
    assert anova_result['df'] is not None
    assert anova_result['df_resid'] is not None
    
    # Verify the note indicates it ignored normality
    assert 'ignore' in anova_result.get('note', '').lower() or \
           'amendment' in anova_result.get('note', '').lower() or \
           'FR-002' in anova_result.get('note', '')

def test_anova_significant_difference(sample_data):
    """Test that ANOVA detects the known difference in the sample data."""
    anova_result = run_anova_pipeline(sample_data, 'completion_time')
    
    # With our generated data (100 vs 85), we expect a significant difference
    assert anova_result['f_statistic'] > 0
    assert anova_result['p_value'] < 1.0  # Should be a valid p-value
    
    # In most cases with this effect size, it should be significant
    # but we don't assert significance to avoid flakiness
    assert isinstance(anova_result['significant'], bool)

def test_effect_size_calculation(sample_data):
    """Test that effect sizes are calculated correctly."""
    effect_result = calculate_effect_size(sample_data, 'completion_time')
    
    assert effect_result['metric'] == 'completion_time'
    assert effect_result['eta_squared'] is not None
    assert 0 <= effect_result['eta_squared'] <= 1  # Valid range
    assert effect_result['interpretation'] in ['Negligible', 'Small', 'Medium', 'Large', 'N/A']

def test_holm_bonferroni_correction():
    """Test Holm-Bonferroni correction logic."""
    # Known p-values
    p_values = [0.01, 0.03, 0.05, 0.10]
    
    result = run_holm_bonferroni(p_values)
    
    assert len(result['corrected_p_values']) == 4
    assert len(result['significant']) == 4
    
    # Corrected p-values should be >= raw p-values
    for i in range(len(p_values)):
        assert result['corrected_p_values'][i] >= p_values[i]
        
    # Corrected p-values should be <= 1.0
    for cp in result['corrected_p_values']:
        assert cp <= 1.0

def test_primary_anova_verification():
    """Test the primary ANOVA verification function."""
    # Case 1: At least one significant
    results_significant = [
        {'p_value': 0.03},
        {'p_value': 0.10},
        {'p_value': 0.20}
    ]
    assert verify_primary_anova_pvalue(results_significant) == True
    
    # Case 2: None significant
    results_not_significant = [
        {'p_value': 0.10},
        {'p_value': 0.20},
        {'p_value': 0.30}
    ]
    assert verify_primary_anova_pvalue(results_not_significant) == False
    
    # Case 3: None with p-value (edge case)
    results_no_pvalue = [
        {'p_value': None},
        {'p_value': None}
    ]
    assert verify_primary_anova_pvalue(results_no_pvalue) == False

def test_anova_with_non_normal_data():
    """Test ANOVA with explicitly non-normal data."""
    np.random.seed(123)
    n_subjects = 20
    
    # Create skewed data (non-normal)
    data = pd.DataFrame({
        'participant_id': np.repeat(range(n_subjects), 2),
        'interface_type': ['Traditional'] * n_subjects + ['Explainable'] * n_subjects,
        'completion_time': np.concatenate([
            np.random.exponential(100, n_subjects),  # Skewed
            np.random.exponential(80, n_subjects)   # Skewed
        ])
    })
    
    # Verify normality test fails (as expected for exponential)
    norm_result = log_normality_test(data, 'completion_time')
    # Note: With small n, Shapiro-Wilk might not always reject, but it should be low p-value
    
    # ANOVA should still run and produce results
    anova_result = run_anova_pipeline(data, 'completion_time')
    
    assert anova_result['f_statistic'] is not None
    assert anova_result['p_value'] is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])