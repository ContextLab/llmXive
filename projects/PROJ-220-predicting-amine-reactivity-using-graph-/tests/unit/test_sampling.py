"""
Unit tests for the sampling module (T011b).

Verifies FR-008 sampling functionality:
- Correct size reduction
- Stratified sampling logic
- Error handling for invalid inputs
- Logging of sampling strategy
"""
import logging
from io import StringIO

import numpy as np
import pandas as pd
import pytest

import sys
import os
# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.utils.sampling import sample_dataset


class TestSampleDataset:
    """Test suite for sample_dataset function."""

    @pytest.fixture
    def sample_df(self):
        """Create a sample DataFrame for testing."""
        return pd.DataFrame({
            'id': range(100),
            'value': np.random.rand(100),
            'category': np.random.choice(['A', 'B', 'C'], 100)
        })

    @pytest.fixture
    def sample_list(self):
        """Create a sample list of dicts for testing."""
        return [
            {'id': i, 'value': np.random.rand()} 
            for i in range(50)
        ]

    def test_target_size_reduction(self, sample_df):
        """Test that target_size correctly reduces the dataset."""
        target = 50
        result = sample_dataset(sample_df, target_size=target, seed=42)
        
        assert len(result) == target
        assert len(result) < len(sample_df)
        # Check that original is not modified
        assert len(sample_df) == 100

    def test_fraction_reduction(self, sample_df):
        """Test that sample_fraction correctly reduces the dataset."""
        fraction = 0.5
        result = sample_dataset(sample_df, sample_fraction=fraction, seed=42)
        
        expected_size = int(len(sample_df) * fraction)
        assert len(result) == expected_size
        assert len(result) < len(sample_df)

    def test_list_input_conversion(self, sample_list):
        """Test that list input is converted to DataFrame."""
        result = sample_dataset(sample_list, target_size=20, seed=42)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 20
        assert 'id' in result.columns
        assert 'value' in result.columns

    def test_stratified_sampling(self, sample_df):
        """Test stratified sampling preserves proportions."""
        # Create a dataset with known proportions
        df = pd.DataFrame({
            'id': range(100),
            'value': np.random.rand(100),
            'category': ['A'] * 50 + ['B'] * 30 + ['C'] * 20
        })
        
        # Sample 50%
        result = sample_dataset(df, sample_fraction=0.5, stratify_by='category', seed=42)
        
        # Check proportions are roughly preserved (allowing for sampling variance)
        proportions = result['category'].value_counts(normalize=True)
        original_proportions = df['category'].value_counts(normalize=True)
        
        # Allow 10% tolerance
        assert abs(proportions['A'] - original_proportions['A']) < 0.1
        assert abs(proportions['B'] - original_proportions['B']) < 0.1
        assert abs(proportions['C'] - original_proportions['C']) < 0.1

    def test_stratify_column_not_found(self, sample_df):
        """Test error when stratify column doesn't exist."""
        with pytest.raises(ValueError, match="not found in dataset"):
            sample_dataset(sample_df, target_size=50, stratify_by='nonexistent_col')

    def test_invalid_target_size(self, sample_df):
        """Test error when target_size is invalid."""
        with pytest.raises(ValueError, match="target_size must be positive"):
            sample_dataset(sample_df, target_size=0)
        
        with pytest.raises(ValueError, match="target_size must be positive"):
            sample_dataset(sample_df, target_size=-5)

    def test_invalid_fraction(self, sample_df):
        """Test error when sample_fraction is invalid."""
        with pytest.raises(ValueError, match="sample_fraction must be between"):
            sample_dataset(sample_df, sample_fraction=0.0)
        
        with pytest.raises(ValueError, match="sample_fraction must be between"):
            sample_dataset(sample_df, sample_fraction=1.5)

    def test_no_reduction_needed(self, sample_df):
        """Test that original dataset is returned if target is larger."""
        result = sample_dataset(sample_df, target_size=200, seed=42)
        
        assert len(result) == len(sample_df)
        # Should be same data (though potentially different index, so check values)
        assert result.equals(sample_df) or result.reset_index(drop=True).equals(sample_df.reset_index(drop=True))

    def test_logging_strategy(self, sample_df, caplog):
        """Test that sampling strategy is logged."""
        caplog.set_level(logging.INFO)
        
        result = sample_dataset(sample_df, target_size=50, seed=42)
        
        # Check that log message contains expected info
        assert any("Dataset sampling applied" in record.message for record in caplog.records)
        assert any("target_size=50" in record.message for record in caplog.records)
        assert any("Reduction:" in record.message for record in caplog.records)

    def test_reproducibility(self, sample_df):
        """Test that same seed produces same result."""
        result1 = sample_dataset(sample_df, target_size=50, seed=123)
        result2 = sample_dataset(sample_df, target_size=50, seed=123)
        
        # Check if results are identical
        assert result1.equals(result2)

    def test_single_row_result(self, sample_df):
        """Test edge case where sample size is 1."""
        # Force a very small fraction
        result = sample_dataset(sample_df, sample_fraction=0.005, seed=42)
        assert len(result) >= 1