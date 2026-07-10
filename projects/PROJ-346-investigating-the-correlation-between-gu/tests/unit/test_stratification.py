"""
Unit tests for age stratification logic in code/05_sensitivity.py.

This module verifies that the age stratification logic correctly:
1. Assigns samples to the correct age groups (<40, 40-<60, >=60)
2. Handles edge cases (boundary ages, missing values)
3. Returns stratified dataframes with proper structure
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path to import code modules
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils import get_age_group


class TestAgeStratificationLogic:
    """Tests for the age stratification functionality."""

    def test_age_group_less_than_40(self):
        """Test that ages < 40 are correctly assigned to '<40' group."""
        assert get_age_group(25) == "<40"
        assert get_age_group(39) == "<40"
        assert get_age_group(0) == "<40"
        assert get_age_group(1) == "<40"

    def test_age_group_40_to_59(self):
        """Test that ages >= 40 and < 60 are correctly assigned to '40-<60' group."""
        assert get_age_group(40) == "40-<60"
        assert get_age_group(45) == "40-<60"
        assert get_age_group(59) == "40-<60"

    def test_age_group_60_and_above(self):
        """Test that ages >= 60 are correctly assigned to '>=60' group."""
        assert get_age_group(60) == ">=60"
        assert get_age_group(65) == ">=60"
        assert get_age_group(100) == ">=60"

    def test_age_group_boundary_values(self):
        """Test boundary values at exact thresholds."""
        assert get_age_group(39) == "<40"
        assert get_age_group(40) == "40-<60"
        assert get_age_group(59) == "40-<60"
        assert get_age_group(60) == ">=60"

    def test_age_group_missing_values(self):
        """Test handling of missing/None age values."""
        assert get_age_group(None) is None
        assert get_age_group(np.nan) is None

    def test_stratify_dataframe(self):
        """Test stratification of a DataFrame by age groups."""
        # Create test data
        data = {
            "age": [25, 35, 40, 45, 55, 59, 60, 70, 80],
            "taxon_A": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
            "cognitive_score": [85, 90, 78, 82, 75, 80, 70, 65, 60]
        }
        df = pd.DataFrame(data)

        # Apply stratification
        df["age_group"] = df["age"].apply(get_age_group)

        # Verify grouping
        groups = df.groupby("age_group")
        
        # Check group sizes
        assert len(groups.get_group("<40")) == 2
        assert len(groups.get_group("40-<60")) == 4
        assert len(groups.get_group(">=60")) == 3

        # Verify ages in each group
        assert all(df.loc[df["age_group"] == "<40", "age"] < 40)
        assert all((df.loc[df["age_group"] == "40-<60", "age"] >= 40) & 
                  (df.loc[df["age_group"] == "40-<60", "age"] < 60))
        assert all(df.loc[df["age_group"] == ">=60", "age"] >= 60)

    def test_stratification_with_missing_ages(self):
        """Test stratification handles missing age values correctly."""
        data = {
            "age": [25, None, 40, np.nan, 60, 70],
            "taxon_B": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
        }
        df = pd.DataFrame(data)
        df["age_group"] = df["age"].apply(get_age_group)

        # Verify that rows with missing ages have None in age_group
        assert df.loc[df["age"].isna(), "age_group"].isna().all()

        # Verify non-missing rows are correctly grouped
        assert len(df.loc[df["age_group"] == "<40"]) == 1
        assert len(df.loc[df["age_group"] == "40-<60"]) == 1
        assert len(df.loc[df["age_group"] == ">=60"]) == 2

    def test_stratification_preserves_data(self):
        """Test that stratification preserves all original data columns."""
        data = {
            "age": [25, 45, 65],
            "taxon_X": [1.0, 2.0, 3.0],
            "taxon_Y": [4.0, 5.0, 6.0],
            "cognitive_score": [100, 90, 80]
        }
        df = pd.DataFrame(data)
        original_columns = df.columns.tolist()
        
        df["age_group"] = df["age"].apply(get_age_group)
        
        # All original columns should still be present
        for col in original_columns:
            assert col in df.columns

    def test_empty_dataframe_stratification(self):
        """Test stratification on an empty DataFrame."""
        df = pd.DataFrame(columns=["age", "taxon"])
        df["age_group"] = df["age"].apply(get_age_group)
        
        assert len(df) == 0
        assert "age_group" in df.columns

    def test_single_age_group_stratification(self):
        """Test stratification when all samples fall into one age group."""
        data = {
            "age": [20, 25, 30, 35],
            "taxon": [1.0, 2.0, 3.0, 4.0]
        }
        df = pd.DataFrame(data)
        df["age_group"] = df["age"].apply(get_age_group)
        
        assert len(df["age_group"].unique()) == 1
        assert df["age_group"].iloc[0] == "<40"

    def test_stratification_output_format(self):
        """Test that stratified output maintains proper DataFrame structure."""
        data = {
            "age": [25, 45, 65],
            "value": [1.0, 2.0, 3.0]
        }
        df = pd.DataFrame(data)
        df["age_group"] = df["age"].apply(get_age_group)
        
        # Verify it's still a DataFrame
        assert isinstance(df, pd.DataFrame)
        
        # Verify index is preserved
        assert list(df.index) == [0, 1, 2]
        
        # Verify column types
        assert df["age_group"].dtype == "object"