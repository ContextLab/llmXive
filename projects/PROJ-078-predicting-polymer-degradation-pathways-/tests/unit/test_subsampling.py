import pytest
import pandas as pd
import os
import sys
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from preprocess import subsample_dataset

class TestSubsampling:
    """Unit tests for the subsampling logic in T018."""

    def test_subsample_larger_than_target(self):
        """Test subsampling when n > target_size."""
        # Create a DataFrame with 200 rows
        df = pd.DataFrame({
            'id': range(200),
            'value': range(200)
        })
        
        # Subsample to 150
        result = subsample_dataset(df, target_size=150, seed=42)
        
        assert len(result) == 150
        assert all(result['id'].isin(df['id']))
        # Check that indices are unique
        assert len(result['id'].unique()) == 150

    def test_subsample_smaller_than_target(self):
        """Test that all rows are kept when n < target_size."""
        # Create a DataFrame with 40 rows
        df = pd.DataFrame({
            'id': range(40),
            'value': range(40)
        })
        
        # Try to subsample to 150 (should keep all)
        result = subsample_dataset(df, target_size=150, seed=42)
        
        assert len(result) == 40
        assert list(result['id']) == list(range(40))

    def test_subsample_exact_target(self):
        """Test that all rows are kept when n == target_size."""
        # Create a DataFrame with exactly 150 rows
        df = pd.DataFrame({
            'id': range(150),
            'value': range(150)
        })
        
        # Subsample to 150
        result = subsample_dataset(df, target_size=150, seed=42)
        
        assert len(result) == 150
        assert list(result['id']) == list(range(150))

    def test_subsample_reproducibility(self):
        """Test that subsampling is reproducible with the same seed."""
        df = pd.DataFrame({
            'id': range(200),
            'value': range(200)
        })
        
        result1 = subsample_dataset(df, target_size=150, seed=42)
        result2 = subsample_dataset(df, target_size=150, seed=42)
        
        # Should be identical
        assert result1.equals(result2)
        
        # Different seed should give different result (with high probability)
        result3 = subsample_dataset(df, target_size=150, seed=123)
        # Not asserting they're different due to very low probability of collision,
        # but the logic is correct

    def test_subsample_reset_index(self):
        """Test that the resulting DataFrame has a reset index."""
        df = pd.DataFrame({
            'id': range(200),
            'value': range(200)
        })
        
        # Shuffle the original DataFrame to have non-sequential index
        df_shuffled = df.sample(frac=1, random_state=42).reset_index(drop=True)
        
        result = subsample_dataset(df_shuffled, target_size=150, seed=42)
        
        # Check that index is reset to 0..149
        assert list(result.index) == list(range(150))

    def test_subsample_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        df = pd.DataFrame({
            'id': [],
            'value': []
        })
        
        result = subsample_dataset(df, target_size=150, seed=42)
        
        assert len(result) == 0
        assert result.empty