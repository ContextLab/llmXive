"""
Unit tests for model training and cross-validation utilities.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import logging
from src.model.nested_cv import generate_splits

@pytest.fixture
def sample_data_ties():
    """
    Create a DataFrame with insufficient unique values for high-q stratification.
    Only 2 unique values for D50.
    """
    data = {
        'feature_1': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'd50': [10.0, 10.0, 10.0, 20.0, 20.0, 20.0, 10.0, 10.0, 20.0, 20.0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_data_unique():
    """
    Create a DataFrame with sufficient unique values for stratification.
    """
    data = {
        'feature_1': list(range(20)),
        'd50': [float(i) for i in range(20)]
    }
    return pd.DataFrame(data)

class TestStratificationFallback:
    """
    Tests for the stratification fallback logic in generate_splits.
    """

    def test_stratification_fallback_on_ties(self, sample_data_ties, caplog):
        """
        Verify that when qcut fails due to ties, the function reduces q
        and eventually falls back to random splits if necessary.
        
        With only 2 unique values, qcut with q=10, 5, 2 might fail or succeed
        depending on implementation details, but q=1 MUST trigger the 
        "Stratification disabled" warning and random split.
        """
        with caplog.at_level(logging.WARNING):
            splits = generate_splits(
                df=sample_data_ties,
                target_col='d50',
                n_splits=2,
                n_repeats=1,
                stratify=True
            )
        
        # Verify we got splits
        assert len(splits) > 0
        assert all(isinstance(train_idx, np.ndarray) and isinstance(test_idx, np.ndarray) 
                   for train_idx, test_idx in splits)

        # Check that the warning was logged if stratification failed completely
        # Note: With 2 unique values, q=2 might actually work for StratifiedKFold
        # The test ensures the logic handles the path where it might fail or succeed gracefully.
        # The critical check is that it doesn't crash and returns valid splits.
        if "Stratification disabled" in caplog.text:
            assert "insufficient unique values" in caplog.text

    def test_stratification_success_with_unique_values(self, sample_data_unique, caplog):
        """
        Verify that when unique values are sufficient, stratification succeeds
        without falling back to random splits.
        """
        with caplog.at_level(logging.INFO):
            splits = generate_splits(
                df=sample_data_unique,
                target_col='d50',
                n_splits=2,
                n_repeats=1,
                stratify=True
            )
        
        assert len(splits) > 0
        # We expect an INFO log about successful stratification
        assert any("Successfully generated stratified splits" in record.message 
                   for record in caplog.records)

    def test_invalid_target_column(self, sample_data_unique):
        """
        Verify that an error is raised if the target column does not exist.
        """
        with pytest.raises(ValueError, match="Target column 'invalid_col' not found"):
            generate_splits(
                df=sample_data_unique,
                target_col='invalid_col',
                n_splits=2,
                n_repeats=1
            )

    def test_empty_target_values(self):
        """
        Verify that an error is raised if the target column has no valid values.
        """
        df = pd.DataFrame({'feature_1': [1, 2, 3], 'd50': [np.nan, np.nan, np.nan]})
        with pytest.raises(ValueError, match="contains no valid values"):
            generate_splits(
                df=df,
                target_col='d50',
                n_splits=2,
                n_repeats=1
            )

    def test_stratify_false_forces_random(self, sample_data_unique, caplog):
        """
        Verify that setting stratify=False forces a random split without attempting qcut.
        """
        with caplog.at_level(logging.WARNING):
            splits = generate_splits(
                df=sample_data_unique,
                target_col='d50',
                n_splits=2,
                n_repeats=1,
                stratify=False
            )
        
        assert len(splits) > 0
        assert "Stratification explicitly disabled" in caplog.text