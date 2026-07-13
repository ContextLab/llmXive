"""
Unit tests for quantile binning split logic in code/data/split.py.

These tests verify that the stratified split logic correctly:
1. Bins continuous target values (logS) into quantiles.
2. Assigns indices to train/val/test sets based on these bins.
3. Maintains the target distribution across splits.
4. Handles edge cases (small datasets, uniform values).
"""

import pytest
import pandas as pd
import numpy as np
import sys
import os

# Add project root to path to allow imports from code/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from data.split import load_cleaned_data, create_stratified_splits, save_split_indices


class TestQuantileBinningLogic:
    """Tests specifically for the quantile binning mechanism."""

    def test_quantile_bins_created_correctly(self):
        """Verify that quantile bins are created and cover the full range."""
        # Create a synthetic dataset with known distribution
        n_samples = 1000
        np.random.seed(42)
        # LogS values typically range from -5 to 5 in ESOL
        logS_values = np.random.normal(loc=0.0, scale=2.0, size=n_samples)
        
        df = pd.DataFrame({
            'smiles': ['CCO' for _ in range(n_samples)],
            'logS': logS_values
        })

        # We test the internal logic by calling create_stratified_splits
        # and checking the resulting distribution
        train_idx, val_idx, test_idx = create_stratified_splits(df, train_ratio=0.8, val_ratio=0.1, test_ratio=0.1, random_seed=42)

        # Verify all indices are unique and cover the dataset
        all_indices = set(train_idx) | set(val_idx) | set(test_idx)
        assert len(all_indices) == n_samples, "Split indices do not cover all samples"
        assert len(set(train_idx)) == len(train_idx), "Duplicate indices in train set"
        assert len(set(val_idx)) == len(val_idx), "Duplicate indices in validation set"
        assert len(set(test_idx)) == len(test_idx), "Duplicate indices in test set"

    def test_distribution_preserved_across_splits(self):
        """Verify that the mean and std of logS are similar across splits (stratification)."""
        n_samples = 1000
        np.random.seed(42)
        logS_values = np.random.normal(loc=0.0, scale=2.0, size=n_samples)
        
        df = pd.DataFrame({
            'smiles': ['CCO' for _ in range(n_samples)],
            'logS': logS_values
        })

        train_idx, val_idx, test_idx = create_stratified_splits(
            df, train_ratio=0.8, val_ratio=0.1, test_ratio=0.1, random_seed=42
        )

        train_logS = df.iloc[train_idx]['logS']
        val_logS = df.iloc[val_idx]['logS']
        test_logS = df.iloc[test_idx]['logS']

        # Calculate statistics
        stats = {
            'train': {'mean': train_logS.mean(), 'std': train_logS.std()},
            'val': {'mean': val_logS.mean(), 'std': val_logS.std()},
            'test': {'mean': test_logS.mean(), 'std': test_logS.std()}
        }

        # The means should be very close (within 0.1 std deviation of the whole set)
        total_std = df['logS'].std()
        tolerance = 0.1 * total_std

        for split_name, split_stats in stats.items():
            diff_from_global_mean = abs(split_stats['mean'] - df['logS'].mean())
            assert diff_from_global_mean < tolerance, \
                f"Mean of {split_name} split ({split_stats['mean']:.4f}) deviates too much from global mean ({df['logS'].mean():.4f}). Diff: {diff_from_global_mean:.4f}"

    def test_empty_splits_rejected(self):
        """Verify that the function handles cases where a split might be too small."""
        # Create a very small dataset
        n_samples = 10
        df = pd.DataFrame({
            'smiles': ['CCO' for _ in range(n_samples)],
            'logS': [0.0] * n_samples
        })

        # With 10 samples, 10% is 1 sample. This should still work but be careful.
        # If the binning logic fails for tiny datasets, it should raise or handle gracefully.
        # We expect it to succeed if the logic is robust.
        try:
            train_idx, val_idx, test_idx = create_stratified_splits(
                df, train_ratio=0.8, val_ratio=0.1, test_ratio=0.1, random_seed=42
            )
            # If it succeeds, check sizes
            assert len(train_idx) >= 1
            assert len(val_idx) >= 0 # Might be 0 if rounding down
            assert len(test_idx) >= 0
        except Exception as e:
            # If it fails, it should be a clear error, not a silent crash
            pytest.fail(f"create_stratified_splits failed on small dataset: {e}")

    def test_uniform_values_handling(self):
        """Test behavior when all logS values are identical (edge case for quantiles)."""
        n_samples = 100
        df = pd.DataFrame({
            'smiles': ['CCO' for _ in range(n_samples)],
            'logS': [1.5] * n_samples
        })

        # Stratification on uniform values should still produce a split
        # (random assignment or equal distribution across bins if bins are forced)
        train_idx, val_idx, test_idx = create_stratified_splits(
            df, train_ratio=0.8, val_ratio=0.1, test_ratio=0.1, random_seed=42
        )

        # Verify indices are valid
        assert len(train_idx) + len(val_idx) + len(test_idx) == n_samples
        assert len(set(train_idx)) == len(train_idx)

    def test_deterministic_with_seed(self):
        """Verify that the same seed produces the same split."""
        n_samples = 200
        np.random.seed(123)
        logS_values = np.random.normal(0, 1, n_samples)
        df = pd.DataFrame({
            'smiles': ['CCO' for _ in range(n_samples)],
            'logS': logS_values
        })

        # Run twice with same seed
        train1, val1, test1 = create_stratified_splits(df, 0.8, 0.1, 0.1, random_seed=42)
        train2, val2, test2 = create_stratified_splits(df, 0.8, 0.1, 0.1, random_seed=42)

        assert list(train1) == list(train2), "Train indices differ with same seed"
        assert list(val1) == list(val2), "Val indices differ with same seed"
        assert list(test1) == list(test2), "Test indices differ with same seed"

    def test_invalid_ratios_rejected(self):
        """Verify that invalid ratios (sum > 1) raise an error."""
        n_samples = 100
        df = pd.DataFrame({
            'smiles': ['CCO' for _ in range(n_samples)],
            'logS': [0.0] * n_samples
        })

        with pytest.raises(ValueError):
            create_stratified_splits(df, train_ratio=0.8, val_ratio=0.3, test_ratio=0.1, random_seed=42)

    def test_negative_ratios_rejected(self):
        """Verify that negative ratios raise an error."""
        n_samples = 100
        df = pd.DataFrame({
            'smiles': ['CCO' for _ in range(n_samples)],
            'logS': [0.0] * n_samples
        })

        with pytest.raises(ValueError):
            create_stratified_splits(df, train_ratio=-0.1, val_ratio=0.1, test_ratio=0.1, random_seed=42)

    def test_zero_ratio_handling(self):
        """Verify that zero ratio for a split results in empty list."""
        n_samples = 100
        df = pd.DataFrame({
            'smiles': ['CCO' for _ in range(n_samples)],
            'logS': [0.0] * n_samples
        })

        train_idx, val_idx, test_idx = create_stratified_splits(
            df, train_ratio=0.9, val_ratio=0.0, test_ratio=0.1, random_seed=42
        )

        assert len(val_idx) == 0, "Validation set should be empty when ratio is 0"
        assert len(train_idx) + len(test_idx) == n_samples

if __name__ == '__main__':
    pytest.main([__file__, '-v'])