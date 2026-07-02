"""
Unit tests for the construct validity checks in code/validity.py.
"""
import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Ensure code/ is in path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from validity import check_construct_validity
from exceptions import MathematicalCouplingError

class TestConstructValidity:
    """Tests for the check_construct_validity function."""

    def test_coupling_detection_raises_error_on_identical_variables(self):
        """
        Verify that the validity module raises MathematicalCouplingError
        when inputs are identical.
        """
        # Create a dataframe with identical columns
        data = {
            "baseline_anxiety": [10, 20, 30, 40, 50],
            "anxiety_score": [10, 20, 30, 40, 50],  # Identical
            "age": [25, 30, 35, 40, 45]
        }
        df = pd.DataFrame(data)

        with pytest.raises(MathematicalCouplingError) as exc_info:
            check_construct_validity(df, "baseline_anxiety", "anxiety_score")

        assert "Mathematical coupling detected" in str(exc_info.value)
        assert "identical" in str(exc_info.value).lower()

    def test_high_correlation_raises_error(self):
        """
        Verify that near-perfect correlation raises an error.
        """
        # Create a dataframe with near-perfect correlation
        data = {
            "baseline_anxiety": [10.0, 20.0, 30.0, 40.0, 50.0],
            "anxiety_score": [10.1, 20.1, 30.1, 40.1, 50.1],  # Slight noise, but r ~ 1.0
            "age": [25, 30, 35, 40, 45]
        }
        df = pd.DataFrame(data)

        # Default tolerance is 0.99, correlation should be > 0.99
        with pytest.raises(MathematicalCouplingError):
            check_construct_validity(df, "baseline_anxiety", "anxiety_score")

    def test_distinct_constructs_passes(self):
        """
        Verify that distinct constructs with low correlation pass the check.
        """
        # Create a dataframe with low correlation
        np.random.seed(42)
        data = {
            "baseline_anxiety": np.random.randint(1, 100, 100),
            "anxiety_score": np.random.randint(1, 100, 100),  # Random, low correlation expected
            "age": np.random.randint(18, 65, 100)
        }
        df = pd.DataFrame(data)

        # This should return True and not raise an error
        result = check_construct_validity(df, "baseline_anxiety", "anxiety_score")
        assert result is True

    def test_missing_columns_raises_error(self):
        """
        Verify that missing columns raise a ValueError.
        """
        data = {
            "age": [25, 30, 35],
            "gender": ["M", "F", "M"]
        }
        df = pd.DataFrame(data)

        with pytest.raises(ValueError) as exc_info:
            check_construct_validity(df, "baseline_anxiety", "anxiety_score")

        assert "Required columns missing" in str(exc_info.value)
