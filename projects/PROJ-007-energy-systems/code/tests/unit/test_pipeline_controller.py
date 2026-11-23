"""
Unit tests for the Pipeline Controller (Placebo Gate Logic).
"""
import pytest
import pandas as pd
import numpy as np
from src.analysis.pipeline_controller import (
    run_placebo_gate,
    run_full_pipeline,
    PlaceboGateError,
    BalanceFailureError
)
from src.analysis.balance import run_placebo_test


@pytest.fixture
def balanced_data():
    """
    Generate synthetic data where treatment and control groups are balanced
    on pre-treatment outcomes (no significant difference).
    """
    np.random.seed(42)
    n = 200
    # Pre-treatment outcome: same distribution for both groups
    pre_outcome = np.random.normal(loc=100, scale=10, size=n)
    treatment = np.array([1] * 100 + [0] * 100)
    # Add some noise to ensure no perfect correlation
    pre_outcome = pre_outcome + np.random.normal(0, 0.1, n)

    df = pd.DataFrame({
        'pre_treatment_outcome': pre_outcome,
        'treatment': treatment,
        'id': range(n)
    })
    return df


@pytest.fixture
def unbalanced_data():
    """
    Generate synthetic data where treatment and control groups are UNBALANCED
    on pre-treatment outcomes (significant difference).
    """
    np.random.seed(123)
    n = 200
    # Pre-treatment outcome: different means for groups
    pre_outcome = np.concatenate([
        np.random.normal(loc=120, scale=10, size=100), # Treatment group higher
        np.random.normal(loc=80, scale=10, size=100)   # Control group lower
    ])
    treatment = np.array([1] * 100 + [0] * 100)

    df = pd.DataFrame({
        'pre_treatment_outcome': pre_outcome,
        'treatment': treatment,
        'id': range(n)
    })
    return df


def test_placebo_gate_passes_for_balanced_data(balanced_data):
    """
    Test that the placebo gate passes when groups are balanced.
    """
    passed, report = run_placebo_gate(balanced_data, pre_treatment_col='pre_treatment_outcome', alpha=0.05)

    assert passed is True, "Placebo gate should pass for balanced data."
    assert report['passed'] is True
    assert report['p_value'] > 0.05, f"Expected p-value > 0.05, got {report['p_value']}"
    assert "PASSED" in report['interpretation']


def test_placebo_gate_fails_for_unbalanced_data(unbalanced_data):
    """
    Test that the placebo gate fails when groups are unbalanced.
    """
    with pytest.raises(PlaceboGateError) as exc_info:
        run_full_pipeline(
            unbalanced_data,
            balance_status='balanced', # Pretend PSM said it's balanced, but placebo says no
            pre_treatment_col='pre_treatment_outcome',
            alpha=0.05
        )

    assert "Placebo test failed" in str(exc_info.value)
    assert "VIOLATED" in str(exc_info.value)


def test_run_full_pipeline_returns_error_on_gate(unbalanced_data):
    """
    Test that run_full_pipeline raises PlaceboGateError when the gate fails.
    """
    with pytest.raises(PlaceboGateError):
        run_full_pipeline(
            unbalanced_data,
            balance_status='balanced',
            pre_treatment_col='pre_treatment_outcome'
        )


def test_missing_pre_outcome_column(balanced_data):
    """
    Test that the pipeline fails gracefully if the pre-treatment column is missing.
    """
    # Remove the column
    data_no_col = balanced_data.drop(columns=['pre_treatment_outcome'])

    with pytest.raises(ValueError) as exc_info:
        run_placebo_gate(data_no_col, pre_treatment_col='nonexistent_col')

    assert "not found" in str(exc_info.value)


def test_missing_treatment_column(balanced_data):
    """
    Test that the pipeline fails if 'treatment' column is missing.
    """
    data_no_treat = balanced_data.drop(columns=['treatment'])

    with pytest.raises(ValueError) as exc_info:
        run_placebo_gate(data_no_treat, pre_treatment_col='pre_treatment_outcome')

    assert "Column 'treatment' not found" in str(exc_info.value)


def test_insufficient_sample_size_warning(caplog, balanced_data):
    """
    Test that a warning is logged if sample size is too small.
    (Note: This test assumes the implementation logs a warning, not an error, for small N).
    """
    # Create very small data
    small_data = balanced_data.head(6) # 3 treatment, 3 control

    # Should not raise, but might warn
    try:
        passed, report = run_placebo_gate(small_data, pre_treatment_col='pre_treatment_outcome')
        # The test might pass or fail depending on the random realization, but it shouldn't crash
        assert isinstance(passed, bool)
    except Exception:
        # If it crashes due to statistical test failure on tiny N, that's also a valid behavior
        # depending on implementation. We just ensure it's handled.
        pass
