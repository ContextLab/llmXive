"""
Unit tests for quantile binning split logic in code/data/split.py.

These tests verify the stratified split logic based on logS quantiles.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.split import create_stratified_splits, load_cleaned_data


class TestQuantileBinningSplitLogic:
    """Tests for the quantile binning and stratified split logic."""

    def test_create_stratified_splits_basic(self):
        """Test basic functionality of stratified split with known data."""
        # Create a simple synthetic dataset for testing the logic
        # Note: In real usage, this would come from load_cleaned_data
        n_samples = 1000
        np.random.seed(42)
        
        # Create data with distinct logS values to ensure quantile binning works
        logS_values = np.random.normal(loc=0, scale=2, size=n_samples)
        smiles_list = [f"SMILES_{i}" for i in range(n_samples)]
        
        df = pd.DataFrame({
            'smiles': smiles_list,
            'logS': logS_values
        })
        
        # Perform stratified split
        train_idx, val_idx, test_idx = create_stratified_splits(
            df, 
            logS_col='logS',
            n_bins=10,
            train_ratio=0.8,
            val_ratio=0.1,
            test_ratio=0.1,
            random_state=42
        )
        
        # Verify splits are non-overlapping
        assert len(set(train_idx) & set(val_idx)) == 0
        assert len(set(train_idx) & set(test_idx)) == 0
        assert len(set(val_idx) & set(test_idx)) == 0
        
        # Verify total count matches
        assert len(train_idx) + len(val_idx) + len(test_idx) == n_samples
        
        # Verify approximate ratios (allowing for rounding)
        assert 0.75 * n_samples <= len(train_idx) <= 0.85 * n_samples
        assert 0.08 * n_samples <= len(val_idx) <= 0.12 * n_samples
        assert 0.08 * n_samples <= len(test_idx) <= 0.12 * n_samples

    def test_stratification_preserves_distribution(self):
        """Test that the stratified split preserves the logS distribution."""
        np.random.seed(123)
        
        # Create data with known distribution
        n_samples = 2000
        logS_values = np.random.normal(loc=0, scale=1.5, size=n_samples)
        smiles_list = [f"SMILES_{i}" for i in range(n_samples)]
        
        df = pd.DataFrame({
            'smiles': smiles_list,
            'logS': logS_values
        })
        
        train_idx, val_idx, test_idx = create_stratified_splits(
            df,
            logS_col='logS',
            n_bins=20,
            train_ratio=0.8,
            val_ratio=0.1,
            test_ratio=0.1,
            random_state=123
        )
        
        # Calculate mean and std for each split
        train_logS = df.loc[train_idx, 'logS']
        val_logS = df.loc[val_idx, 'logS']
        test_logS = df.loc[test_idx, 'logS']
        
        # The means should be very close (within 0.1 std deviation)
        overall_std = df['logS'].std()
        
        assert abs(train_logS.mean() - df['logS'].mean()) < 0.1 * overall_std
        assert abs(val_logS.mean() - df['logS'].mean()) < 0.1 * overall_std
        assert abs(test_logS.mean() - df['logS'].mean()) < 0.1 * overall_std
        
        # The stds should also be similar
        assert abs(train_logS.std() - df['logS'].std()) < 0.2 * overall_std
        assert abs(val_logS.std() - df['logS'].std()) < 0.2 * overall_std
        assert abs(test_logS.std() - df['logS'].std()) < 0.2 * overall_std

    def test_quantile_binning_edge_cases(self):
        """Test edge cases in quantile binning."""
        # Test with small dataset
        np.random.seed(456)
        n_samples = 50
        logS_values = np.random.normal(loc=0, scale=1, size=n_samples)
        smiles_list = [f"SMILES_{i}" for i in range(n_samples)]
        
        df = pd.DataFrame({
            'smiles': smiles_list,
            'logS': logS_values
        })
        
        # Should work with small dataset
        train_idx, val_idx, test_idx = create_stratified_splits(
            df,
            logS_col='logS',
            n_bins=5,  # Fewer bins for small dataset
            train_ratio=0.8,
            val_ratio=0.1,
            test_ratio=0.1,
            random_state=456
        )
        
        assert len(train_idx) > 0
        assert len(val_idx) > 0
        assert len(test_idx) > 0
        assert len(train_idx) + len(val_idx) + len(test_idx) == n_samples

    def test_stratified_split_with_duplicate_values(self):
        """Test that duplicate logS values are handled correctly."""
        # Create data with many duplicate values
        n_samples = 100
        logS_values = np.repeat([0.0, 1.0, 2.0], n_samples // 3)
        # Add one extra if needed
        if len(logS_values) < n_samples:
            logS_values = np.append(logS_values, 0.0)
        
        smiles_list = [f"SMILES_{i}" for i in range(len(logS_values))]
        
        df = pd.DataFrame({
            'smiles': smiles_list,
            'logS': logS_values
        })
        
        # Should handle duplicates without error
        train_idx, val_idx, test_idx = create_stratified_splits(
            df,
            logS_col='logS',
            n_bins=10,
            train_ratio=0.8,
            val_ratio=0.1,
            test_ratio=0.1,
            random_state=789
        )
        
        # Verify no overlap
        assert len(set(train_idx) & set(val_idx)) == 0
        assert len(set(train_idx) & set(test_idx)) == 0
        assert len(set(val_idx) & set(test_idx)) == 0

    def test_stratified_split_reproducibility(self):
        """Test that the split is reproducible with the same random state."""
        np.random.seed(999)
        n_samples = 500
        logS_values = np.random.normal(loc=0, scale=2, size=n_samples)
        smiles_list = [f"SMILES_{i}" for i in range(n_samples)]
        
        df = pd.DataFrame({
            'smiles': smiles_list,
            'logS': logS_values
        })
        
        # Run twice with same seed
        train_idx_1, val_idx_1, test_idx_1 = create_stratified_splits(
            df,
            logS_col='logS',
            n_bins=10,
            train_ratio=0.8,
            val_ratio=0.1,
            test_ratio=0.1,
            random_state=999
        )
        
        train_idx_2, val_idx_2, test_idx_2 = create_stratified_splits(
            df,
            logS_col='logS',
            n_bins=10,
            train_ratio=0.8,
            val_ratio=0.1,
            test_ratio=0.1,
            random_state=999
        )
        
        # Results should be identical
        assert list(train_idx_1) == list(train_idx_2)
        assert list(val_idx_1) == list(val_idx_2)
        assert list(test_idx_1) == list(test_idx_2)

    def test_stratified_split_different_ratios(self):
        """Test split with different ratio configurations."""
        np.random.seed(555)
        n_samples = 1000
        logS_values = np.random.normal(loc=0, scale=1, size=n_samples)
        smiles_list = [f"SMILES_{i}" for i in range(n_samples)]
        
        df = pd.DataFrame({
            'smiles': smiles_list,
            'logS': logS_values
        })
        
        # Test with 60/20/20 split
        train_idx, val_idx, test_idx = create_stratified_splits(
            df,
            logS_col='logS',
            n_bins=10,
            train_ratio=0.6,
            val_ratio=0.2,
            test_ratio=0.2,
            random_state=555
        )
        
        assert abs(len(train_idx) / n_samples - 0.6) < 0.05
        assert abs(len(val_idx) / n_samples - 0.2) < 0.05
        assert abs(len(test_idx) / n_samples - 0.2) < 0.05

    def test_invalid_input_handling(self):
        """Test that the function handles invalid inputs gracefully."""
        # Empty dataframe
        df_empty = pd.DataFrame({'smiles': [], 'logS': []})
        
        with pytest.raises((ValueError, IndexError)):
            create_stratified_splits(
                df_empty,
                logS_col='logS',
                n_bins=10,
                train_ratio=0.8,
                val_ratio=0.1,
                test_ratio=0.1,
                random_state=123
            )
        
        # DataFrame with missing logS values (should be handled by preprocessing,
        # but let's test the split function's behavior)
        df_nan = pd.DataFrame({
            'smiles': ['SMILES_1', 'SMILES_2', 'SMILES_3'],
            'logS': [1.0, np.nan, 3.0]
        })
        
        # The function should either handle NaN or fail gracefully
        # depending on implementation details
        try:
            train_idx, val_idx, test_idx = create_stratified_splits(
                df_nan,
                logS_col='logS',
                n_bins=10,
                train_ratio=0.8,
                val_ratio=0.1,
                test_ratio=0.1,
                random_state=123
            )
            # If it succeeds, ensure NaN is not in the splits
            nan_indices = df_nan[df_nan['logS'].isna()].index.tolist()
            assert not any(idx in nan_indices for idx in train_idx + val_idx + test_idx)
        except (ValueError, KeyError):
            # Expected if the function doesn't handle NaN internally
            pass

    def test_bin_count_effect_on_stratification(self):
        """Test that different bin counts affect stratification quality."""
        np.random.seed(777)
        n_samples = 1000
        logS_values = np.random.normal(loc=0, scale=2, size=n_samples)
        smiles_list = [f"SMILES_{i}" for i in range(n_samples)]
        
        df = pd.DataFrame({
            'smiles': smiles_list,
            'logS': logS_values
        })
        
        # Test with few bins
        train_idx_few, _, _ = create_stratified_splits(
            df,
            logS_col='logS',
            n_bins=3,
            train_ratio=0.8,
            val_ratio=0.1,
            test_ratio=0.1,
            random_state=777
        )
        
        # Test with many bins
        train_idx_many, _, _ = create_stratified_splits(
            df,
            logS_col='logS',
            n_bins=50,
            train_ratio=0.8,
            val_ratio=0.1,
            test_ratio=0.1,
            random_state=777
        )
        
        # Both should produce valid splits
        assert len(train_idx_few) > 0
        assert len(train_idx_many) > 0
        
        # The mean logS should be similar in both cases (within tolerance)
        train_logS_few = df.loc[train_idx_few, 'logS']
        train_logS_many = df.loc[train_idx_many, 'logS']
        
        # They should be reasonably close to the overall mean
        overall_mean = df['logS'].mean()
        assert abs(train_logS_few.mean() - overall_mean) < 0.5
        assert abs(train_logS_many.mean() - overall_mean) < 0.5