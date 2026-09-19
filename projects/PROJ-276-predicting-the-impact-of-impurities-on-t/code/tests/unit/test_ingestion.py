"""
Unit tests for ingestion logic, specifically filtering and validation.
"""

import pytest
import pandas as pd
import numpy as np
from code.src.ingestion.preprocess import filter_valid_entries
from code.src.ingestion.download_supercon import validate_impurity_coverage


class TestDataFiltering:
    """Tests for data filtering logic."""

    def test_filter_missing_tc(self):
        """Test that rows with missing Tc are dropped."""
        df = pd.DataFrame({
            "tc": [10.0, np.nan, 20.0],
            "impurity_c_atomic_pct": [1.0, 2.0, 3.0]
        })
        result = filter_valid_entries(df)
        assert len(result) == 2
        assert not result["tc"].isna().any()

    def test_filter_missing_impurity(self):
        """Test that rows with missing impurities are dropped."""
        df = pd.DataFrame({
            "tc": [10.0, 20.0, 30.0],
            "impurity_c_atomic_pct": [1.0, np.nan, 3.0]
        })
        result = filter_valid_entries(df)
        assert len(result) == 2
        # Check that the row with NaN impurity is gone
        assert 1 not in result.index

    def test_filter_both_missing(self):
        """Test that rows with both missing are dropped."""
        df = pd.DataFrame({
            "tc": [np.nan, 20.0],
            "impurity_c_atomic_pct": [np.nan, 3.0]
        })
        result = filter_valid_entries(df)
        assert len(result) == 1

    def test_all_valid(self):
        """Test that valid rows are kept."""
        df = pd.DataFrame({
            "tc": [10.0, 20.0],
            "impurity_c_atomic_pct": [1.0, 2.0]
        })
        result = filter_valid_entries(df)
        assert len(result) == 2


class TestSuperConImpurityValidation:
    """Tests for SuperCon impurity coverage validation."""

    def test_valid_coverage(self):
        """Test dataset with >50% impurity coverage passes."""
        # Create a dataframe with 10 rows, 6 have impurities
        data = {
            "tc": [10] * 10,
            "impurity_c_weight_pct": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0] + [np.nan] * 4
        }
        df = pd.DataFrame(data)
        # 6/10 = 60% > 50%
        assert validate_impurity_coverage(df) is True

    def test_invalid_coverage(self):
        """Test dataset with <50% impurity coverage fails."""
        # Create a dataframe with 10 rows, 4 have impurities
        data = {
            "tc": [10] * 10,
            "impurity_c_weight_pct": [1.0, 2.0, 3.0, 4.0] + [np.nan] * 6
        }
        df = pd.DataFrame(data)
        # 4/10 = 40% < 50%
        assert validate_impurity_coverage(df) is False

    def test_edge_case_50(self):
        """Test dataset with exactly 50% impurity coverage."""
        # 5 out of 10
        data = {
            "tc": [10] * 10,
            "impurity_c_weight_pct": [1.0, 2.0, 3.0, 4.0, 5.0] + [np.nan] * 5
        }
        df = pd.DataFrame(data)
        # 5/10 = 50% -> Should be False (>50% required)
        assert validate_impurity_coverage(df) is False