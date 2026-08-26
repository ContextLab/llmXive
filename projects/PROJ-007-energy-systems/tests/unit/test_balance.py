"""
Unit tests for src/analysis/balance.py.

These tests verify:
1. SMD calculation logic (manual calculation on small dataset).
2. Plot generation (checks for valid figure object).
3. Balance status check logic.
4. Error handling for edge cases.
"""

import pytest
import pandas as pd
import numpy as np
from src.analysis.balance import calculate_smd, plot_balance, check_balance_status


@pytest.fixture
def sample_matched_data():
    """
    Create a small synthetic dataset with known properties for testing SMD.
    Treatment group: mean=10, var=4
    Control group: mean=8, var=4
    Expected SMD = (10-8)/sqrt(4) = 1.0
    """
    np.random.seed(42)
    n_treat = 50
    n_control = 50

    treated = pd.DataFrame({
        'treatment': 1,
        'income': np.random.normal(10, 2, n_treat),
        'age': np.random.normal(35, 5, n_treat),
        'house_value': np.random.normal(200000, 10000, n_treat)
    })

    control = pd.DataFrame({
        'treatment': 0,
        'income': np.random.normal(8, 2, n_control),
        'age': np.random.normal(35, 5, n_control), # Same mean, should be ~0 SMD
        'house_value': np.random.normal(200000, 10000, n_control)
    })

    return pd.concat([treated, control], ignore_index=True)


@pytest.fixture
def balanced_data():
    """Data where means are identical, SMD should be near 0."""
    np.random.seed(123)
    n = 100
    df = pd.DataFrame({
        'treatment': [1]*n + [0]*n,
        'var1': np.random.normal(0, 1, 2*n)
    })
    return df


def test_calculate_smd_known_values(sample_matched_data):
    """Test SMD calculation against a known theoretical value."""
    smd = calculate_smd(sample_matched_data, treatment_col='treatment',
                        covariate_cols=['income'])

    # We expect income SMD to be around 1.0 (based on fixture construction)
    # Allow small tolerance for random sampling variance
    assert 'income' in smd
    assert abs(smd['income'] - 1.0) < 0.2


def test_calculate_smd_balanced(balanced_data):
    """Test that balanced data yields SMD near 0."""
    smd = calculate_smd(balanced_data, treatment_col='treatment')
    # SMD should be small, definitely less than 0.1
    assert abs(smd['var1']) < 0.1


def test_calculate_smd_multiple_columns(sample_matched_data):
    """Test calculation for multiple columns."""
    smd = calculate_smd(sample_matched_data, treatment_col='treatment')
    assert 'income' in smd
    assert 'age' in smd
    assert 'house_value' in smd


def test_calculate_smd_empty_dataframe():
    """Test error handling for empty input."""
    df = pd.DataFrame(columns=['treatment', 'income'])
    with pytest.raises(RuntimeError, match="Input DataFrame is empty"):
        calculate_smd(df)


def test_calculate_smd_missing_treatment_col():
    """Test error handling for missing treatment column."""
    df = pd.DataFrame({'income': [1, 2, 3]})
    with pytest.raises(ValueError, match="Treatment column"):
        calculate_smd(df)


def test_calculate_smd_no_treated_group():
    """Test error handling if treatment group is empty."""
    df = pd.DataFrame({'treatment': [0, 0, 0], 'income': [1, 2, 3]})
    with pytest.raises(RuntimeError, match="No treated observations"):
        calculate_smd(df)


def test_plot_balance_valid_data(sample_matched_data):
    """Test that plot_balance returns a valid figure."""
    smd = calculate_smd(sample_matched_data, treatment_col='treatment')
    fig = plot_balance(smd)
    assert fig is not None
    assert isinstance(fig, plt.Figure)
    plt.close(fig) # Clean up


def test_plot_balance_empty_data():
    """Test error handling for empty SMD dict."""
    with pytest.raises(ValueError, match="SMD data dictionary is empty"):
        plot_balance({})


def test_check_balance_status_pass(balanced_data):
    """Test status check when balance is good."""
    smd = calculate_smd(balanced_data, treatment_col='treatment')
    assert check_balance_status(smd) is True


def test_check_balance_status_fail(sample_matched_data):
    """Test status check when balance is poor (SMD ~ 1.0 > 0.1)."""
    smd = calculate_smd(sample_matched_data, treatment_col='treatment')
    assert check_balance_status(smd) is False
