import pytest
import pandas as pd
import numpy as np
from src.analysis.balance import (
    run_placebo_test, 
    validate_placebo_results, 
    generate_placebo_report, 
    check_placebo_significance,
    calculate_smd
)

@pytest.fixture
def balanced_data():
    """Create a dataset where treatment and control groups have similar means for pre-treatment outcome."""
    np.random.seed(42)
    n = 200
    # Simulate pre-treatment outcome with same mean for both groups
    pre_outcome = np.concatenate([
        np.random.normal(loc=100, scale=10, size=n//2),
        np.random.normal(loc=100, scale=10, size=n//2)
    ])
    treatment = np.array([1] * (n//2) + [0] * (n//2))
    return pd.DataFrame({
        'pre_treatment': pre_outcome,
        'treatment': treatment
    })

@pytest.fixture
def unbalanced_data():
    """Create a dataset where treatment and control groups have different means for pre-treatment outcome."""
    np.random.seed(42)
    n = 200
    # Simulate pre-treatment outcome with different means
    pre_outcome = np.concatenate([
        np.random.normal(loc=120, scale=10, size=n//2), # Treatment group higher
        np.random.normal(loc=80, scale=10, size=n//2)   # Control group lower
    ])
    treatment = np.array([1] * (n//2) + [0] * (n//2))
    return pd.DataFrame({
        'pre_treatment': pre_outcome,
        'treatment': treatment
    })

def test_placebo_test_passes_for_balanced_data(balanced_data):
    """Test that placebo test passes when groups are balanced."""
    p_val, t_stat, is_balanced = run_placebo_test(balanced_data, 'pre_treatment')
    
    assert is_balanced is True, "Placebo test should pass for balanced data."
    assert p_val > 0.05, f"P-value ({p_val}) should be > 0.05 for balanced data."
    assert t_stat is not None
    assert not np.isnan(t_stat)

def test_placebo_test_fails_for_unbalanced_data(unbalanced_data):
    """Test that placebo test fails when groups are unbalanced."""
    p_val, t_stat, is_balanced = run_placebo_test(unbalanced_data, 'pre_treatment')
    
    assert is_balanced is False, "Placebo test should fail for unbalanced data."
    assert p_val < 0.05, f"P-value ({p_val}) should be < 0.05 for unbalanced data."

def test_validate_placebo_results_logic():
    """Test the validation logic helper function."""
    assert validate_placebo_results(0.10) is True
    assert validate_placebo_results(0.06) is True
    assert validate_placebo_results(0.05) is False # Strictly greater
    assert validate_placebo_results(0.01) is False

def test_generate_placebo_report_structure(balanced_data):
    """Test that the report contains expected keys and structure."""
    report = generate_placebo_report(balanced_data, 'pre_treatment')
    
    expected_keys = [
        'pre_treatment_variable', 'p_value', 't_statistic', 
        'alpha', 'is_balanced', 'status', 'interpretation'
    ]
    
    for key in expected_keys:
        assert key in report, f"Report missing key: {key}"
        
    assert report['status'] in ['PASS', 'FAIL']
    assert isinstance(report['p_value'], float)
    assert isinstance(report['t_statistic'], float)

def test_check_placebo_significance_raises_on_failure(unbalanced_data):
    """Test that check_placebo_significance raises ValueError on failure."""
    with pytest.raises(ValueError) as excinfo:
        check_placebo_significance(unbalanced_data, 'pre_treatment')
    
    assert "Placebo test failed" in str(excinfo.value)
    assert "p=" in str(excinfo.value)

def test_check_placebo_significance_returns_true_on_success(balanced_data):
    """Test that check_placebo_significance returns True on success."""
    result = check_placebo_significance(balanced_data, 'pre_treatment')
    assert result is True

def test_placebo_test_missing_columns_raises():
    """Test that missing columns raise appropriate errors."""
    df = pd.DataFrame({'other_col': [1, 2, 3], 'treatment': [1, 0, 1]})
    
    with pytest.raises(ValueError, match="Column 'pre_treatment' not found"):
        run_placebo_test(df, 'pre_treatment')
        
    with pytest.raises(ValueError, match="Column 'treatment' not found"):
        run_placebo_test(df, 'other_col', treatment_col='nonexistent')

def test_placebo_test_insufficient_data():
    """Test that insufficient data points raise an error."""
    df = pd.DataFrame({
        'pre_treatment': [100, 101],
        'treatment': [1, 0]
    })
    
    # Need at least 2 in each group for t-test, but here we have 1 in each
    # The function checks for < 2, so this should pass the check but fail the t-test logic?
    # Actually, ttest_ind needs at least 2 samples to calculate variance.
    # Let's create a case with exactly 1 in each group.
    df_single = pd.DataFrame({
        'pre_treatment': [100, 101],
        'treatment': [1, 0]
    })
    
    # Wait, 1 in each group is not enough for variance.
    # Let's try 1 in treatment, 1 in control.
    # The check is `if len(treatment_group) < 2 or len(control_group) < 2`
    # So this should raise ValueError.
    
    with pytest.raises(ValueError, match="Insufficient data points"):
        run_placebo_test(df_single, 'pre_treatment')

def test_smd_calculation_consistency():
    """Test that SMD calculation is consistent with known values."""
    df = pd.DataFrame({
        'var': [10, 12, 14, 16, 18, 20, 22, 24],
        'treatment': [1, 1, 1, 1, 0, 0, 0, 0]
    })
    # Treatment mean: 12.5, Control mean: 20.5
    # Treatment std: ~3.02, Control std: ~3.02
    # Pooled std: ~3.02
    # SMD: (12.5 - 20.5) / 3.02 = -2.64 approx
    
    smd = calculate_smd(df)
    assert 'var' in smd
    assert abs(smd['var'] - (-2.64)) < 0.1 # Allow some tolerance

def test_placebo_test_with_alpha_parameter():
    """Test placebo test with different alpha levels."""
    # Create data with p-value around 0.04
    np.random.seed(123)
    n = 100
    # Slight difference
    treatment_group = np.random.normal(loc=100, scale=5, size=n//2)
    control_group = np.random.normal(loc=105, scale=5, size=n//2)
    
    df = pd.DataFrame({
        'outcome': np.concatenate([treatment_group, control_group]),
        'treatment': [1]*(n//2) + [0]*(n//2)
    })
    
    p_val, _, is_balanced = run_placebo_test(df, 'outcome')
    
    # At alpha=0.05, if p < 0.05, it's unbalanced
    # At alpha=0.01, if p > 0.01, it's balanced
    
    assert validate_placebo_results(p_val, alpha=0.05) == (p_val > 0.05)
    assert validate_placebo_results(p_val, alpha=0.01) == (p_val > 0.01)