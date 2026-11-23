import pandas as pd
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code.model_training import stratified_split, save_splits
from code.config import load_config

class TestStratifiedSplit:
    def test_stratified_split_produces_correct_sizes(self):
        """Test that stratified split produces the correct ratio of data."""
        # Create a dummy dataset with balanced classes
        data = {
            'feature1': list(range(100)),
            'feature2': list(range(100, 200)),
            'target': list(range(200, 300)),
            'family': ['A'] * 50 + ['B'] * 50
        }
        df = pd.DataFrame(data)
        
        train, val, test = stratified_split(df, 'target', 'family')
        
        # Expected sizes based on config: 0.7, 0.15, 0.15
        expected_train = 70
        expected_val = 15
        expected_test = 15
        
        assert len(train) == expected_train
        assert len(val) == expected_val
        assert len(test) == expected_test
        
        # Check that all data is accounted for
        assert len(train) + len(val) + len(test) == len(df)

    def test_stratified_split_preserves_distribution(self):
        """Test that the split preserves the distribution of the stratification column."""
        data = {
            'feature1': list(range(120)),
            'feature2': list(range(120, 240)),
            'target': list(range(240, 360)),
            'family': ['A'] * 60 + ['B'] * 40 + ['C'] * 20
        }
        df = pd.DataFrame(data)
        
        train, val, test = stratified_split(df, 'target', 'family')
        
        # Check that the relative proportions are roughly preserved
        train_dist = train['family'].value_counts(normalize=True)
        val_dist = val['family'].value_counts(normalize=True)
        test_dist = test['family'].value_counts(normalize=True)
        original_dist = df['family'].value_counts(normalize=True)
        
        # Allow some tolerance due to rounding
        tolerance = 0.05
        
        for family in ['A', 'B', 'C']:
            assert abs(train_dist.get(family, 0) - original_dist[family]) < tolerance
            assert abs(val_dist.get(family, 0) - original_dist[family]) < tolerance
            assert abs(test_dist.get(family, 0) - original_dist[family]) < tolerance

    def test_stratified_split_fallback_on_failure(self):
        """Test that the function falls back to non-stratified split when stratification fails."""
        # Create a dataset with a class that has only 1 sample
        data = {
            'feature1': list(range(10)),
            'feature2': list(range(10, 20)),
            'target': list(range(20, 30)),
            'family': ['A'] * 9 + ['B']  # 'B' has only 1 sample
        }
        df = pd.DataFrame(data)
        
        # This should not raise an exception but log a warning
        with patch('code.model_training.logger') as mock_logger:
            train, val, test = stratified_split(df, 'target', 'family')
            
            # Check that a warning was logged
            assert any('Stratified split failed' in str(call) for call in mock_logger.warning.call_args_list)
            
            # Check that we still get valid splits
            assert len(train) + len(val) + len(test) == len(df)
            assert len(train) > 0
            assert len(val) > 0
            assert len(test) > 0

class TestSaveSplits:
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        # Setup: create test data
        self.train_df = pd.DataFrame({'a': [1, 2, 3]})
        self.val_df = pd.DataFrame({'a': [4, 5]})
        self.test_df = pd.DataFrame({'a': [6, 7, 8]})
        
        # Ensure directories exist
        os.makedirs('data/processed', exist_ok=True)
        
        yield
        
        # Teardown: clean up files
        for file in ['data/processed/train.parquet', 'data/processed/val.parquet', 'data/processed/test.parquet']:
            if os.path.exists(file):
                os.remove(file)

    def test_save_splits_creates_files(self):
        """Test that save_splits creates the expected parquet files."""
        save_splits(self.train_df, self.val_df, self.test_df)
        
        assert os.path.exists('data/processed/train.parquet')
        assert os.path.exists('data/processed/val.parquet')
        assert os.path.exists('data/processed/test.parquet')

    def test_save_splits_saves_correct_data(self):
        """Test that save_splits saves the correct data."""
        save_splits(self.train_df, self.val_df, self.test_df)
        
        loaded_train = pd.read_parquet('data/processed/train.parquet')
        loaded_val = pd.read_parquet('data/processed/val.parquet')
        loaded_test = pd.read_parquet('data/processed/test.parquet')
        
        pd.testing.assert_frame_equal(loaded_train, self.train_df)
        pd.testing.assert_frame_equal(loaded_val, self.val_df)
        pd.testing.assert_frame_equal(loaded_test, self.test_df)
