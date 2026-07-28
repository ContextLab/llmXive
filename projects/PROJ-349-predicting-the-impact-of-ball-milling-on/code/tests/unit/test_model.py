import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.model.nested_cv import generate_splits, generate_nested_splits
from src.utils.seed import set_seed

@pytest.fixture
def sample_df_stratified():
    """DataFrame with enough unique values for stratification."""
    set_seed(42)
    n = 1000
    return pd.DataFrame({
        'd50': np.random.uniform(10, 100, n),
        'feature1': np.random.uniform(0, 1, n)
    })

@pytest.fixture
def sample_df_ties():
    """DataFrame with many ties (insufficient unique values for high q)."""
    set_seed(42)
    # Create data with only 3 unique values
    values = np.array([10.0, 20.0, 30.0] * 100) # 300 rows
    np.random.shuffle(values)
    return pd.DataFrame({
        'd50': values,
        'feature1': np.random.uniform(0, 1, len(values))
    })

@pytest.fixture
def sample_df_single_value():
    """DataFrame with only one unique value."""
    set_seed(42)
    n = 100
    return pd.DataFrame({
        'd50': [10.0] * n,
        'feature1': np.random.uniform(0, 1, n)
    })

class TestStratificationFallback:
    def test_splits_are_stratified_by_d50(self, sample_df_stratified):
        """Test that splits are generated correctly when stratification is possible."""
        splits = generate_splits(sample_df_stratified, target_col='d50', n_splits=5, n_repeats=1, random_state=42)
        
        assert len(splits) == 1 * 5, "Should generate 5 splits for 1 repeat."
        
        # Verify stratification: distribution of bins should be roughly equal in train/test
        # This is a soft check; we mainly check that no exception is raised and splits exist.
        for train_idx, test_idx in splits:
            assert len(train_idx) > 0
            assert len(test_idx) > 0
            assert len(train_idx) + len(test_idx) == len(sample_df_stratified)

    def test_stratification_fallback_on_ties(self, sample_df_ties):
        """
        Test that qcut fallback mechanism works when unique values are insufficient.
        Expected behavior:
        1. Try q=10 -> Fail (only 3 unique values)
        2. Try q=5 -> Fail (only 3 unique values)
        3. Try q=2 -> Success (3 unique values >= 2 bins)
        """
        # This should not raise an exception
        splits = generate_splits(
            sample_df_ties, 
            target_col='d50', 
            n_splits=3, 
            n_repeats=1, 
            random_state=42
        )
        
        assert len(splits) == 3, "Should generate 3 splits."
        
        # Verify that splits are valid
        for train_idx, test_idx in splits:
            assert len(train_idx) > 0
            assert len(test_idx) > 0

    def test_fallback_to_random_split_on_extreme_ties(self, sample_df_single_value):
        """
        Test that if even q=2 fails (only 1 unique value), it falls back to random split.
        """
        # This should not raise an exception, but log a warning
        with patch('src.model.nested_cv.logger') as mock_logger:
            splits = generate_splits(
                sample_df_single_value, 
                target_col='d50', 
                n_splits=3, 
                n_repeats=1, 
                random_state=42
            )
            
            # Verify warning was logged
            warning_calls = [call for call in mock_logger.warning.call_args_list 
                             if "Stratification disabled" in str(call)]
            assert len(warning_calls) > 0, "Should log warning about stratification disabled."
            
            assert len(splits) == 3, "Should generate 3 splits even without stratification."
            
            # Verify splits are valid
            for train_idx, test_idx in splits:
                assert len(train_idx) > 0
                assert len(test_idx) > 0

class TestNestedSplits:
    def test_nested_splits_structure(self, sample_df_stratified):
        """Test that nested splits are generated correctly."""
        nested = generate_nested_splits(
            sample_df_stratified, 
            target_col='d50', 
            outer_splits=3, 
            inner_splits=2, 
            n_repeats=1, 
            random_state=42
        )
        
        assert len(nested) == 3, "Should have 3 outer folds."
        
        for inner_splits_list, (outer_train, outer_test) in nested:
            assert len(inner_splits_list) == 2, "Each outer fold should have 2 inner splits."
            assert len(outer_train) + len(outer_test) == len(sample_df_stratified)
            
            for inner_train, inner_test in inner_splits_list:
                # Inner indices must be subset of outer train indices
                assert set(inner_train).issubset(set(outer_train))
                assert set(inner_test).issubset(set(outer_train))
    
    def test_nested_splits_with_ties(self, sample_df_ties):
        """Test nested splits generation when stratification fallback is triggered."""
        # This should not raise an exception
        nested = generate_nested_splits(
            sample_df_ties, 
            target_col='d50', 
            outer_splits=2, 
            inner_splits=2, 
            n_repeats=1, 
            random_state=42
        )
        
        assert len(nested) == 2, "Should have 2 outer folds."
        
        for inner_splits_list, (outer_train, outer_test) in nested:
            assert len(inner_splits_list) == 2
            assert len(outer_train) > 0
            assert len(outer_test) > 0