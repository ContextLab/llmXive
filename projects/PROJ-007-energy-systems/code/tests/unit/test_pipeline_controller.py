"""
Unit tests for the Pipeline Controller (Placebo Gate).
"""
import pytest
import pandas as pd
import numpy as np
from src.analysis.pipeline_controller import run_placebo_gate, run_full_pipeline, PlaceboGateError

def generate_balanced_data(n=200):
    """Generate synthetic data where treatment and control are balanced."""
    np.random.seed(42)
    df = pd.DataFrame({
        'income': np.random.normal(50000, 10000, n),
        'housing_type': np.random.choice(['rent', 'own'], n),
        'location': np.random.choice(['urban', 'rural'], n),
        'treatment': np.random.binomial(1, 0.3, n),
        'energy_cost_burden': np.random.normal(0.1, 0.02, n),
        'pre_treatment_outcome': np.random.normal(0.1, 0.02, n) # Same distribution for both
    })
    return df

def generate_unbalanced_data(n=200):
    """Generate synthetic data where treatment has significantly higher pre-outcome."""
    np.random.seed(42)
    df = pd.DataFrame({
        'income': np.random.normal(50000, 10000, n),
        'housing_type': np.random.choice(['rent', 'own'], n),
        'location': np.random.choice(['urban', 'rural'], n),
        'treatment': np.random.binomial(1, 0.3, n),
        'energy_cost_burden': np.random.normal(0.1, 0.02, n),
        'pre_treatment_outcome': np.where(
            df['treatment'] == 1,
            np.random.normal(0.2, 0.02, n), # Higher for treatment
            np.random.normal(0.1, 0.02, n)  # Lower for control
        )
    })
    return df

def test_placebo_gate_passes_for_balanced_data():
    """Test that the pipeline passes when data is balanced."""
    df = generate_balanced_data()
    result = run_full_pipeline(
        df,
        pre_outcome_col='pre_treatment_outcome',
        covariates=['income', 'housing_type', 'location']
    )
    assert result['status'] == 'PASS', f"Expected PASS, got {result['status']}. Message: {result['message']}"
    assert result['p_value'] is not None
    assert result['p_value'] >= 0.05

def test_placebo_gate_fails_for_unbalanced_data():
    """Test that the pipeline gates (raises error) when data is unbalanced."""
    df = generate_unbalanced_data()
    with pytest.raises(PlaceboGateError) as excinfo:
        run_placebo_gate(
            df,
            pre_outcome_col='pre_treatment_outcome',
            covariates=['income', 'housing_type', 'location']
        )
    assert "significant" in str(excinfo.value).lower() or "failed" in str(excinfo.value).lower()

def test_run_full_pipeline_returns_error_on_gate():
    """Test that run_full_pipeline returns a GATED status instead of raising."""
    df = generate_unbalanced_data()
    result = run_full_pipeline(
        df,
        pre_outcome_col='pre_treatment_outcome',
        covariates=['income', 'housing_type', 'location']
    )
    assert result['status'] == 'GATED'
    assert "significant" in result['message'].lower()

def test_missing_pre_outcome_column():
    """Test that missing pre_outcome column raises an error."""
    df = generate_balanced_data()
    df = df.drop(columns=['pre_treatment_outcome'])
    with pytest.raises(ValueError, match="Pre-treatment outcome column"):
        run_placebo_gate(df, pre_outcome_col='pre_treatment_outcome')