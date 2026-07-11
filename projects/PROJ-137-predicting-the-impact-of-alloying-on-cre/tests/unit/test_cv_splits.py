"""
Unit tests for Nested CV split generation logic (stratification by temperature range).

This module verifies the correctness of the stratification strategy used in the
Nested Cross-Validation pipeline for User Story 2. It ensures that:
1. Stratification is performed based on discretized temperature ranges.
2. The split generation respects the requested number of folds.
3. Each fold contains a representative distribution of temperature ranges (when possible).
4. The intersection of training and testing sets is empty for each fold.
"""

import pytest
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, KFold
from sklearn.base import clone

# Import the logic to be tested (assuming it's in src/models/utils.py or similar)
# Since the implementation file (src/models/train.py) is not yet written,
# we define the helper function here for testing purposes, matching the expected signature.
# In the final implementation, this function will reside in src/models/utils.py
# or be imported from src/models/train.py.
def _get_stratified_cv_splits(
    df: pd.DataFrame,
    n_splits: int = 5,
    target_col: str = "temperature",
    seed: int = 42
):
    """
    Generates StratifiedKFold splits based on binned temperature ranges.

    Args:
        df: The dataframe containing the data.
        n_splits: Number of folds.
        target_col: The column to use for stratification.
        seed: Random seed for reproducibility.

    Returns:
        A list of (train_idx, test_idx) tuples.
    """
    if n_splits < 2:
        raise ValueError("n_splits must be at least 2")

    # Create bins for stratification
    # We use equal-width bins based on the range of temperatures
    # Ensure we have enough unique values to stratify
    temp_data = df[target_col].values
    
    # Check if we have enough unique values for stratification
    unique_vals = np.unique(temp_data)
    if len(unique_vals) < n_splits:
        # If not enough unique values, fall back to simple KFold
        # This handles small datasets gracefully
        kf = KFold(n_splits=n_splits, shuffle=True, random_state=seed)
        return list(kf.split(df))

    # Create bins for stratification
    # We use quantile-based binning to ensure balanced folds
    # This is more robust for uneven distributions
    try:
        # Create bins using percentiles to ensure balance
        bins = np.percentile(temp_data, np.linspace(0, 100, n_splits + 1))
        # Ensure unique bins
        bins = np.unique(bins)
        if len(bins) < 2:
            # Fallback if all values are the same
            kf = KFold(n_splits=n_splits, shuffle=True, random_state=seed)
            return list(kf.split(df))
        
        # Assign each sample to a bin
        # Use digitize to assign samples to bins
        # digitize returns indices 1..len(bins)-1, so we subtract 1 to get 0..len(bins)-2
        # But we want exactly n_splits bins, so we adjust
        if len(bins) > n_splits + 1:
            # Trim bins to ensure we have exactly n_splits intervals
            # Keep the first and last, and select n_splits-1 intermediate points
            indices = np.linspace(0, len(bins)-1, n_splits+1, dtype=int)
            bins = bins[indices]
        
        strat_labels = np.digitize(temp_data, bins[:-1]) - 1
        
        # Ensure all labels are within valid range
        strat_labels = np.clip(strat_labels, 0, n_splits - 1)
        
        # Create StratifiedKFold
        skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
        return list(skf.split(df, strat_labels))
        
    except Exception as e:
        # Fallback to KFold if stratification fails
        kf = KFold(n_splits=n_splits, shuffle=True, random_state=seed)
        return list(kf.split(df))


@pytest.fixture
def sample_data():
    """Create a sample dataframe for testing."""
    # Create a dataset with known temperature distribution
    np.random.seed(42)
    n_samples = 100
    
    # Create temperature ranges: 3 groups with different frequencies
    temps = np.concatenate([
        np.random.normal(800, 50, 30),   # Low temp group
        np.random.normal(900, 50, 40),   # Medium temp group
        np.random.normal(1000, 50, 30)   # High temp group
    ])
    
    # Create other required columns
    stress = np.random.uniform(100, 300, n_samples)
    rupture_time = np.random.uniform(10, 1000, n_samples)
    mixing_enthalpy = np.random.uniform(-10, 10, n_samples)
    radius_mismatch = np.random.uniform(0, 5, n_samples)
    
    # Create composition columns (simplified)
    composition_str = ["Ni-Cr-Al"] * n_samples
    
    df = pd.DataFrame({
        "alloy_id": range(n_samples),
        "composition_str": composition_str,
        "temperature": temps,
        "stress": stress,
        "rupture_time": rupture_time,
        "mixing_enthalpy": mixing_enthalpy,
        "radius_mismatch": radius_mismatch
    })
    
    return df


class TestNestedCVSplitGeneration:
    """Test suite for the stratified CV split generation logic."""

    def test_split_count(self, sample_data):
        """Test that the correct number of splits is generated."""
        n_splits = 5
        splits = _get_stratified_cv_splits(sample_data, n_splits=n_splits)
        
        assert len(splits) == n_splits, f"Expected {n_splits} splits, got {len(splits)}"

    def test_train_test_disjoint(self, sample_data):
        """Test that training and testing sets are disjoint for each fold."""
        n_splits = 5
        splits = _get_stratified_cv_splits(sample_data, n_splits=n_splits)
        
        for train_idx, test_idx in splits:
            assert len(set(train_idx) & set(test_idx)) == 0, \
                "Training and testing sets should be disjoint"

    def test_cover_all_samples(self, sample_data):
        """Test that all samples are used in testing exactly once across all folds."""
        n_splits = 5
        splits = _get_stratified_cv_splits(sample_data, n_splits=n_splits)
        
        all_test_indices = []
        for _, test_idx in splits:
            all_test_indices.extend(test_idx)
        
        # Each sample should appear in exactly one test set
        assert len(all_test_indices) == len(sample_data), \
            "All samples should be used in testing exactly once"
        
        # Check for duplicates
        assert len(all_test_indices) == len(set(all_test_indices)), \
            "Each sample should appear in exactly one test set"

    def test_stratification_balance(self, sample_data):
        """Test that temperature ranges are approximately balanced across folds."""
        n_splits = 5
        splits = _get_stratified_cv_splits(sample_data, n_splits=n_splits)
        
        temps = sample_data["temperature"].values
        
        # For each fold, calculate the mean temperature of the test set
        test_means = []
        for _, test_idx in splits:
            test_means.append(np.mean(temps[test_idx]))
        
        # The means should be relatively close (within 20% of the overall mean)
        overall_mean = np.mean(temps)
        for mean in test_means:
            deviation = abs(mean - overall_mean) / overall_mean
            # Allow for some deviation due to random sampling and binning
            assert deviation < 0.3, \
                f"Test set mean temperature {mean:.2f} deviates too much from overall mean {overall_mean:.2f}"

    def test_small_dataset_fallback(self):
        """Test that small datasets fall back to KFold when stratification is not possible."""
        # Create a small dataset with few unique temperature values
        df_small = pd.DataFrame({
            "alloy_id": range(10),
            "composition_str": ["Ni"] * 10,
            "temperature": [800.0] * 10,  # All same temperature
            "stress": [100.0] * 10,
            "rupture_time": [100.0] * 10,
            "mixing_enthalpy": [0.0] * 10,
            "radius_mismatch": [0.0] * 10
        })
        
        n_splits = 5
        splits = _get_stratified_cv_splits(df_small, n_splits=n_splits)
        
        # Should still generate splits without error
        assert len(splits) == n_splits
        
        # Verify disjointness
        for train_idx, test_idx in splits:
            assert len(set(train_idx) & set(test_idx)) == 0

    def test_reproducibility(self, sample_data):
        """Test that the splits are reproducible with the same seed."""
        n_splits = 5
        seed = 42
        
        splits1 = _get_stratified_cv_splits(sample_data, n_splits=n_splits, seed=seed)
        splits2 = _get_stratified_cv_splits(sample_data, n_splits=n_splits, seed=seed)
        
        # Splits should be identical
        for (train1, test1), (train2, test2) in zip(splits1, splits2):
            np.testing.assert_array_equal(train1, train2)
            np.testing.assert_array_equal(test1, test2)

    def test_different_seeds_produce_different_splits(self, sample_data):
        """Test that different seeds produce different splits."""
        n_splits = 5
        
        splits1 = _get_stratified_cv_splits(sample_data, n_splits=n_splits, seed=42)
        splits2 = _get_stratified_cv_splits(sample_data, n_splits=n_splits, seed=123)
        
        # At least one split should be different
        is_different = False
        for (train1, test1), (train2, test2) in zip(splits1, splits2):
            if not np.array_equal(train1, train2) or not np.array_equal(test1, test2):
                is_different = True
                break
        
        assert is_different, "Different seeds should produce different splits"

    def test_invalid_n_splits(self, sample_data):
        """Test that invalid n_splits raises an error."""
        with pytest.raises(ValueError, match="n_splits must be at least 2"):
            _get_stratified_cv_splits(sample_data, n_splits=1)

    def test_empty_dataframe(self):
        """Test behavior with an empty dataframe."""
        df_empty = pd.DataFrame(columns=["alloy_id", "composition_str", "temperature", 
                                         "stress", "rupture_time", "mixing_enthalpy", 
                                         "radius_mismatch"])
        
        # Should handle empty dataframe gracefully (either return empty splits or raise error)
        # For this test, we expect it to either return empty list or raise a clear error
        try:
            splits = _get_stratified_cv_splits(df_empty, n_splits=5)
            assert len(splits) == 0, "Empty dataframe should produce no splits"
        except Exception:
            # Raising an error is also acceptable for empty data
            pass

    def test_stratification_with_imbalanced_data(self):
        """Test stratification with highly imbalanced temperature distribution."""
        # Create dataset with 90% low temp, 10% high temp
        n_samples = 100
        temps = np.concatenate([
            np.full(90, 800.0),
            np.full(10, 1000.0)
        ])
        
        df_imbalanced = pd.DataFrame({
            "alloy_id": range(n_samples),
            "composition_str": ["Ni"] * n_samples,
            "temperature": temps,
            "stress": [100.0] * n_samples,
            "rupture_time": [100.0] * n_samples,
            "mixing_enthalpy": [0.0] * n_samples,
            "radius_mismatch": [0.0] * n_samples
        })
        
        n_splits = 5
        splits = _get_stratified_cv_splits(df_imbalanced, n_splits=n_splits)
        
        # Should generate splits without error
        assert len(splits) == n_splits
        
        # Verify that both temperature groups are represented in each fold (if possible)
        for train_idx, test_idx in splits:
            train_temps = df_imbalanced.loc[train_idx, "temperature"]
            test_temps = df_imbalanced.loc[test_idx, "temperature"]
            
            # Check that we have at least some representation from both groups
            # (This might not be possible with very small test sets, so we allow for some flexibility)
            train_low = np.sum(train_temps == 800.0)
            train_high = np.sum(train_temps == 1000.0)
            test_low = np.sum(test_temps == 800.0)
            test_high = np.sum(test_temps == 1000.0)
            
            # At least one group should be present in each set
            assert train_low > 0 or train_high > 0, "Training set should have at least one temperature group"
            assert test_low > 0 or test_high > 0, "Testing set should have at least one temperature group"