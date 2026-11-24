"""
Unit tests for the preparation module (code/preparation.py).

These tests verify that after preparation:
* The treatment column is present and binary.
* Its mean is approximately 0.5.
* The outcome column exists and is numeric.
* Correlation between outcome and each covariate lies within the band [0.25, 0.35].
* A sanity t‑test / logistic regression on the permuted data returns a p‑value > 0.5.
"""

import numpy as np
import pandas as pd
import pytest

from preparation import prepare_dataset

@pytest.fixture
def synthetic_dataset():
    # Create a small synthetic dataset with two covariates
    rng = np.random.default_rng(0)
    df = pd.DataFrame({
        "age": rng.normal(50, 10, size=200),
        "sex": rng.integers(0, 2, size=200),
    })
    return df

def test_prepare_adds_treatment_and_outcome(synthetic_dataset):
    prepared = prepare_dataset(synthetic_dataset.copy(), outcome_type="continuous")
    # Treatment column should exist and be binary
    assert "treatment" in prepared.columns
    assert set(prepared["treatment"].unique()) <= {0, 1}
    # Mean should be close to 0.5
    assert abs(prepared["treatment"].mean() - 0.5) < 0.05

    # Outcome column should exist and be numeric
    assert "outcome" in prepared.columns
    assert pd.api.types.is_numeric_dtype(prepared["outcome"])

def test_correlation_band(synthetic_dataset):
    prepared = prepare_dataset(synthetic_dataset.copy(), outcome_type="continuous")
    for cov in ["age", "sex"]:
        corr = np.corrcoef(prepared["outcome"], prepared[cov])[0, 1]
        assert 0.25 <= abs(corr) <= 0.35

def test_null_effect_test(synthetic_dataset):
    prepared = prepare_dataset(synthetic_dataset.copy(), outcome_type="continuous")
    # Perform a two‑sample t‑test on the permuted treatment groups
    from scipy import stats
    group0 = prepared[prepared["treatment"] == 0]["outcome"]
    group1 = prepared[prepared["treatment"] == 1]["outcome"]
    t_stat, p_val = stats.ttest_ind(group0, group1, equal_var=False)
    assert p_val > 0.5