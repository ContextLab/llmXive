"""
Unit tests for variable presence validation logic.

This module tests the `validate_variable_presence` function from
`code/utils/validators.py` to ensure it correctly identifies missing
protected attributes, outcomes, and prediction columns in datasets.

Tests cover:
- Valid datasets with all required columns.
- Missing protected attribute.
- Missing outcome column.
- Missing prediction column.
- Multiple missing columns simultaneously.
- Case sensitivity handling.
- Empty dataframe handling.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path to allow imports from code/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.validators import validate_variable_presence, get_required_columns


class TestValidateVariablePresence:
    """Test suite for validate_variable_presence function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.protected_attr = "gender"
        self.outcome = "y"
        self.predictions = "y_pred"
        
        # Create a valid dataframe with all required columns
        self.valid_df = pd.DataFrame({
            self.protected_attr: [0, 1, 0, 1],
            "age": [25, 30, 35, 40],
            self.outcome: [0, 1, 1, 0],
            self.predictions: [0, 1, 0, 1],
            "other_feature": [10, 20, 30, 40]
        })

    def test_get_required_columns_returns_correct_list(self):
        """Test that get_required_columns returns the expected column names."""
        required = get_required_columns(self.protected_attr, self.outcome, self.predictions)
        assert isinstance(required, list)
        assert self.protected_attr in required
        assert self.outcome in required
        assert self.predictions in required
        assert len(required) == 3

    def test_valid_dataframe_returns_true(self):
        """Test that a dataframe with all required columns returns True."""
        result, missing_cols = validate_variable_presence(
            self.valid_df,
            self.protected_attr,
            self.outcome,
            self.predictions
        )
        assert result is True
        assert missing_cols == []

    def test_missing_protected_attribute(self):
        """Test detection of missing protected attribute."""
        df_missing_protected = self.valid_df.drop(columns=[self.protected_attr])
        
        result, missing_cols = validate_variable_presence(
            df_missing_protected,
            self.protected_attr,
            self.outcome,
            self.predictions
        )
        
        assert result is False
        assert self.protected_attr in missing_cols
        assert len(missing_cols) == 1

    def test_missing_outcome(self):
        """Test detection of missing outcome column."""
        df_missing_outcome = self.valid_df.drop(columns=[self.outcome])
        
        result, missing_cols = validate_variable_presence(
            df_missing_outcome,
            self.protected_attr,
            self.outcome,
            self.predictions
        )
        
        assert result is False
        assert self.outcome in missing_cols
        assert len(missing_cols) == 1

    def test_missing_predictions(self):
        """Test detection of missing predictions column."""
        df_missing_predictions = self.valid_df.drop(columns=[self.predictions])
        
        result, missing_cols = validate_variable_presence(
            df_missing_predictions,
            self.protected_attr,
            self.outcome,
            self.predictions
        )
        
        assert result is False
        assert self.predictions in missing_cols
        assert len(missing_cols) == 1

    def test_multiple_missing_columns(self):
        """Test detection of multiple missing columns simultaneously."""
        df_missing_multiple = self.valid_df.drop(columns=[self.protected_attr, self.outcome])
        
        result, missing_cols = validate_variable_presence(
            df_missing_multiple,
            self.protected_attr,
            self.outcome,
            self.predictions
        )
        
        assert result is False
        assert self.protected_attr in missing_cols
        assert self.outcome in missing_cols
        assert len(missing_cols) == 2

    def test_empty_dataframe(self):
        """Test validation on an empty dataframe (should fail due to missing columns)."""
        empty_df = pd.DataFrame()
        
        result, missing_cols = validate_variable_presence(
            empty_df,
            self.protected_attr,
            self.outcome,
            self.predictions
        )
        
        assert result is False
        assert len(missing_cols) == 3
        assert set(missing_cols) == {self.protected_attr, self.outcome, self.predictions}

    def test_dataframe_with_extra_columns(self):
        """Test that extra columns do not affect validation success."""
        df_with_extra = self.valid_df.copy()
        df_with_extra["extra_col_1"] = [1, 2, 3, 4]
        df_with_extra["extra_col_2"] = ["a", "b", "c", "d"]
        
        result, missing_cols = validate_variable_presence(
            df_with_extra,
            self.protected_attr,
            self.outcome,
            self.predictions
        )
        
        assert result is True
        assert missing_cols == []

    def test_case_sensitivity(self):
        """Test that column name matching is case-sensitive."""
        df_case_mismatch = self.valid_df.rename(columns={self.protected_attr: self.protected_attr.upper()})
        
        result, missing_cols = validate_variable_presence(
            df_case_mismatch,
            self.protected_attr,
            self.outcome,
            self.predictions
        )
        
        # Should fail because 'gender' != 'GENDER'
        assert result is False
        assert self.protected_attr in missing_cols

    def test_none_dataframe(self):
        """Test that passing None raises an appropriate error."""
        with pytest.raises((TypeError, AttributeError)):
            validate_variable_presence(
                None,
                self.protected_attr,
                self.outcome,
                self.predictions
            )

    def test_all_missing_columns_in_list(self):
        """Test that all three columns missing returns all in the list."""
        df_empty = pd.DataFrame({"random_col": [1, 2, 3]})
        
        result, missing_cols = validate_variable_presence(
            df_empty,
            self.protected_attr,
            self.outcome,
            self.predictions
        )
        
        assert result is False
        assert len(missing_cols) == 3
        # Order might vary, so check set equality
        assert set(missing_cols) == {self.protected_attr, self.outcome, self.predictions}

    def test_partial_column_names(self):
        """Test validation when column names are substrings of required names."""
        # Create dataframe with columns that are substrings
        df_partial = pd.DataFrame({
            "g": [0, 1],
            "y_outcome": [0, 1],
            "y_predicates": [0, 1]
        })
        
        result, missing_cols = validate_variable_presence(
            df_partial,
            self.protected_attr,
            self.outcome,
            self.predictions
        )
        
        # Should fail because exact names are required
        assert result is False
        assert len(missing_cols) == 3

if __name__ == "__main__":
    pytest.main([__file__, "-v"])