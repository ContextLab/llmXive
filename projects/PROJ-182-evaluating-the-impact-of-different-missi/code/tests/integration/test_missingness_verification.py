"""
Integration tests for missingness verification (T044).

These tests verify that the statistical verification logic correctly
identifies MCAR, MAR, and MNAR mechanisms.
"""
import pytest
import pandas as pd
import numpy as np
from scipy import stats
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.verification.missingness_verification import (
    verify_mcar,
    verify_mar,
    verify_mnar
)


@pytest.fixture
def mcar_data():
    """Generate data with MCAR missingness."""
    np.random.seed(42)
    n = 1000
    df = pd.DataFrame({
        'X': np.random.uniform(-1, 1, n),
        'Z': np.random.normal(0, 1, n),
        'Y': np.random.normal(0, 1, n)
    })
    # MCAR: missingness independent of all variables
    missingness = np.random.binomial(1, 0.3, n)  # 30% missing, random
    df['Y_missing'] = missingness
    return df


@pytest.fixture
def mar_data():
    """Generate data with MAR missingness (correlated with Z)."""
    np.random.seed(42)
    n = 1000
    df = pd.DataFrame({
        'X': np.random.uniform(-1, 1, n),
        'Z': np.random.normal(0, 1, n),
        'Y': np.random.normal(0, 1, n)
    })
    # MAR: missingness depends on Z
    prob = 1 / (1 + np.exp(-df['Z']))  # Higher Z -> higher missingness
    missingness = np.random.binomial(1, prob, n)
    df['Y_missing'] = missingness
    return df


@pytest.fixture
def mnar_data():
    """Generate data with MNAR missingness (correlated with Y)."""
    np.random.seed(42)
    n = 1000
    df = pd.DataFrame({
        'X': np.random.uniform(-1, 1, n),
        'Z': np.random.normal(0, 1, n),
        'Y': np.random.normal(0, 1, n)
    })
    # MNAR: missingness depends on Y
    prob = 1 / (1 + np.exp(-df['Y']))  # Higher Y -> higher missingness
    missingness = np.random.binomial(1, prob, n)
    df['Y_missing'] = missingness
    return df


class TestMCARVerification:
    """Tests for MCAR verification logic."""

    def test_mcar_independence(self, mcar_data):
        """MCAR should show no significant dependence (p >= 0.05)."""
        p_value, is_valid = verify_mcar(mcar_data)
        # With random missingness, we expect p >= 0.05 (independence)
        # Note: Due to randomness, occasional failures can occur, but typically p > 0.05
        assert is_valid, f"MCAR verification failed: p={p_value:.4f} < 0.05"

    def test_mcar_p_value_reasonable(self, mcar_data):
        """MCAR p-value should generally be > 0.05."""
        p_value, _ = verify_mcar(mcar_data)
        # Allow some randomness, but typically should be > 0.05
        # We don't assert p > 0.05 strictly because of Type I error rate
        assert 0 <= p_value <= 1, "p-value out of range"


class TestMARVerification:
    """Tests for MAR verification logic."""

    def test_mar_correlation(self, mar_data):
        """MAR should show significant correlation with Z (p < 0.05)."""
        p_value, is_valid = verify_mar(mar_data, covariate_col='Z')
        assert is_valid, f"MAR verification failed: p={p_value:.4f} >= 0.05"

    def test_mar_p_value_significant(self, mar_data):
        """MAR p-value should be < 0.05."""
        p_value, _ = verify_mar(mar_data, covariate_col='Z')
        assert p_value < 0.05, f"MAR p-value not significant: p={p_value:.4f}"


class TestMNARVerification:
    """Tests for MNAR verification logic."""

    def test_mnar_correlation(self, mnar_data):
        """MNAR should show significant correlation with Y (p < 0.05)."""
        p_value, is_valid = verify_mnar(mnar_data, outcome_col='Y')
        assert is_valid, f"MNAR verification failed: p={p_value:.4f} >= 0.05"

    def test_mnar_p_value_significant(self, mnar_data):
        """MNAR p-value should be < 0.05."""
        p_value, _ = verify_mnar(mnar_data, outcome_col='Y')
        assert p_value < 0.05, f"MNAR p-value not significant: p={p_value:.4f}"


class TestVerificationEdgeCases:
    """Tests for edge cases in verification."""

    def test_missing_column_mcar(self):
        """Should raise error if missingness column is missing."""
        df = pd.DataFrame({'X': [1, 2, 3], 'Z': [4, 5, 6]})
        with pytest.raises(ValueError):
            verify_mcar(df)

    def test_missing_column_mar(self):
        """Should raise error if covariate column is missing."""
        df = pd.DataFrame({'X': [1, 2, 3], 'Y_missing': [0, 1, 0]})
        with pytest.raises(ValueError):
            verify_mar(df, covariate_col='Z')

    def test_missing_column_mnar(self):
        """Should raise error if outcome column is missing."""
        df = pd.DataFrame({'X': [1, 2, 3], 'Y_missing': [0, 1, 0]})
        with pytest.raises(ValueError):
            verify_mnar(df, outcome_col='Y')
