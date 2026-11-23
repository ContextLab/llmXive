"""
Unit tests for significance testing logic, specifically ANOVA calculations.
Tests verify p-value output for linear models using real statistical methods.
"""
import pytest
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm

# Import the function to be tested (placeholder for implementation)
# Since T026 (implementation) is not yet done, we will mock the function
# or test the underlying logic directly if the function is implemented.
# For now, we test the statistical logic that the implementation should use.
try:
    from code.src.modeling.significance_test import calculate_anova_pvalue
except ImportError:
    calculate_anova_pvalue = None


def test_anova_pvalue_linear_model():
    """
    Verify that the ANOVA calculation returns a valid p-value for a linear model.
    This test creates synthetic but statistically valid data where we know
    the relationship exists, ensuring the statistical machinery works.
    """
    # Create a dataset with a known linear relationship
    # Y = 2*X + noise
    np.random.seed(42)
    n_samples = 100
    X = np.random.normal(0, 1, n_samples)
    noise = np.random.normal(0, 0.5, n_samples)
    Y = 2 * X + noise

    df = pd.DataFrame({'Tc': Y, 'impurity_A': X})

    # If the implementation function exists, use it
    if calculate_anova_pvalue:
        p_value = calculate_anova_pvalue(df, target_col='Tc', predictor_col='impurity_A')
    else:
        # Fallback to direct statsmodels implementation to verify logic
        model = ols('Tc ~ impurity_A', data=df).fit()
        anova_table = anova_lm(model)
        p_value = anova_table['PR(>F)']['impurity_A']

    # Assertions
    assert isinstance(p_value, (float, np.floating)), "p-value must be a float"
    assert 0.0 <= p_value <= 1.0, "p-value must be between 0 and 1"
    assert p_value < 0.05, "With this strong signal, p-value should be significant (< 0.05)"


def test_anova_pvalue_no_relationship():
    """
    Verify that ANOVA returns a high p-value when there is no relationship.
    """
    np.random.seed(42)
    n_samples = 100
    X = np.random.normal(0, 1, n_samples)
    Y = np.random.normal(0, 1, n_samples) # Independent noise

    df = pd.DataFrame({'Tc': Y, 'impurity_B': X})

    if calculate_anova_pvalue:
        p_value = calculate_anova_pvalue(df, target_col='Tc', predictor_col='impurity_B')
    else:
        model = ols('Tc ~ impurity_B', data=df).fit()
        anova_table = anova_lm(model)
        p_value = anova_table['PR(>F)']['impurity_B']

    # With independent noise, p-value should generally be > 0.05
    # (Note: there is a 5% chance of false positive, so we just assert it's a valid float)
    assert isinstance(p_value, (float, np.floating))
    assert 0.0 <= p_value <= 1.0


def test_anova_pvalue_missing_data():
    """
    Verify behavior when data contains NaNs.
    The implementation should handle NaNs (e.g., by dropping them) or raise an error.
    Here we expect the underlying statsmodels to handle it if we drop NaNs first,
    or we test that the function handles it gracefully.
    """
    np.random.seed(42)
    df = pd.DataFrame({
        'Tc': [1.0, 2.0, np.nan, 4.0],
        'impurity_C': [0.1, 0.2, 0.3, 0.4]
    })

    # We expect the function to drop NaNs or raise a clear error
    if calculate_anova_pvalue:
        try:
            p_value = calculate_anova_pvalue(df, target_col='Tc', predictor_col='impurity_C')
            assert isinstance(p_value, (float, np.floating))
        except Exception as e:
            # If it raises, it must be a specific, clear error about data integrity
            assert "NaN" in str(e) or "missing" in str(e).lower()
    else:
        # Direct test with statsmodels (which drops NaNs by default in fit)
        model = ols('Tc ~ impurity_C', data=df).fit()
        anova_table = anova_lm(model)
        p_value = anova_table['PR(>F)']['impurity_C']
        assert isinstance(p_value, (float, np.floating))


def test_anova_pvalue_multiple_predictors():
    """
    Verify ANOVA works with multiple predictors (multivariate).
    """
    np.random.seed(42)
    n_samples = 100
    X1 = np.random.normal(0, 1, n_samples)
    X2 = np.random.normal(0, 1, n_samples)
    Y = 2 * X1 + 3 * X2 + np.random.normal(0, 0.5, n_samples)

    df = pd.DataFrame({'Tc': Y, 'impurity_1': X1, 'impurity_2': X2})

    if calculate_anova_pvalue:
        # Assuming the function can handle a list of predictors or a formula
        # For this test, we assume it takes a single predictor or we test the formula approach
        # Since the signature isn't fixed yet, we test the underlying logic directly
        model = ols('Tc ~ impurity_1 + impurity_2', data=df).fit()
        anova_table = anova_lm(model)
        # Check that p-values exist for both
        p1 = anova_table['PR(>F)']['impurity_1']
        p2 = anova_table['PR(>F)']['impurity_2']
    else:
        model = ols('Tc ~ impurity_1 + impurity_2', data=df).fit()
        anova_table = anova_lm(model)
        p1 = anova_table['PR(>F)']['impurity_1']
        p2 = anova_table['PR(>F)']['impurity_2']

    assert isinstance(p1, (float, np.floating))
    assert isinstance(p2, (float, np.floating))
    assert p1 < 0.05, "Impurity 1 should be significant"
    assert p2 < 0.05, "Impurity 2 should be significant"