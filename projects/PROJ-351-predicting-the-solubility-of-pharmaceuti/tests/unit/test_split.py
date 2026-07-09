"""
Unit tests for the quantile binning split logic in code/data/split.py.

These tests verify:
1. That stratified splits are created based on logS quantile bins.
2. That the distribution of logS values is preserved across splits.
3. That the split indices are valid and cover the entire dataset.
"""

import os
import sys
import tempfile
import json
import math
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Add parent directory to path to allow imports from code/
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.split import load_cleaned_data, create_stratified_splits, save_split_indices


def create_temp_csv(data: dict) -> str:
    """Helper to create a temporary CSV file with given data."""
    fd, path = tempfile.mkstemp(suffix='.csv')
    try:
        with os.fdopen(fd, 'w') as tmp:
            df = pd.DataFrame(data)
            df.to_csv(tmp, index=False)
        return path
    except Exception:
        os.close(fd)
        raise


def create_temp_json(data: dict) -> str:
    """Helper to create a temporary JSON file with given data."""
    fd, path = tempfile.mkstemp(suffix='.json')
    try:
        with os.fdopen(fd, 'w') as tmp:
            json.dump(data, tmp)
        return path
    except Exception:
        os.close(fd)
        raise


class TestQuantileBinningSplit:
    """Tests for the quantile binning split logic."""

    def test_create_stratified_splits_basic(self):
        """Test basic creation of stratified splits with uniform data."""
        # Create synthetic data with known logS distribution
        np.random.seed(42)
        n_samples = 1000
        smiles_list = [f"SMILES_{i}" for i in range(n_samples)]
        # Create logS values with a known distribution (normal)
        logS_values = np.random.normal(loc=-3.0, scale=1.5, size=n_samples)

        temp_csv = create_temp_csv({
            'SMILES': smiles_list,
            'logS': logS_values
        })

        try:
            # Load data
            data, _ = load_cleaned_data(temp_csv)

            # Create splits with 3 quantile bins
            train_idx, val_idx, test_idx = create_stratified_splits(
                data,
                train_ratio=0.7,
                val_ratio=0.15,
                test_ratio=0.15,
                n_bins=3,
                random_state=42
            )

            # Verify total coverage
            all_indices = set(train_idx) | set(val_idx) | set(test_idx)
            assert len(all_indices) == n_samples, "Not all indices are covered"

            # Verify no overlap
            assert len(set(train_idx) & set(val_idx)) == 0, "Train and val overlap"
            assert len(set(train_idx) & set(test_idx)) == 0, "Train and test overlap"
            assert len(set(val_idx) & set(test_idx)) == 0, "Val and test overlap"

            # Verify approximate ratios (allowing 5% tolerance)
            assert abs(len(train_idx) / n_samples - 0.7) < 0.05
            assert abs(len(val_idx) / n_samples - 0.15) < 0.05
            assert abs(len(test_idx) / n_samples - 0.15) < 0.05

        finally:
            os.unlink(temp_csv)

    def test_stratification_preserves_distribution(self):
        """Test that stratification preserves logS distribution across splits."""
        # Create data with a skewed distribution
        np.random.seed(123)
        n_samples = 1000
        smiles_list = [f"SMILES_{i}" for i in range(n_samples)]
        # Skewed logS distribution
        logS_values = np.random.exponential(scale=2.0, size=n_samples) - 3.0

        temp_csv = create_temp_csv({
            'SMILES': smiles_list,
            'logS': logS_values
        })

        try:
            data, _ = load_cleaned_data(temp_csv)

            # Create splits
            train_idx, val_idx, test_idx = create_stratified_splits(
                data,
                train_ratio=0.7,
                val_ratio=0.15,
                test_ratio=0.15,
                n_bins=5,
                random_state=123
            )

            # Calculate logS values for each split
            train_logS = data['logS'].iloc[train_idx]
            val_logS = data['logS'].iloc[val_idx]
            test_logS = data['logS'].iloc[test_idx]

            # Calculate mean and std for each split
            train_mean, train_std = train_logS.mean(), train_logS.std()
            val_mean, val_std = val_logS.mean(), val_logS.std()
            test_mean, test_std = test_logS.mean(), test_logS.std()
            overall_mean, overall_std = data['logS'].mean(), data['logS'].std()

            # Each split should have similar mean and std to overall (within 10%)
            assert abs(train_mean - overall_mean) < 0.1 * abs(overall_mean)
            assert abs(val_mean - overall_mean) < 0.1 * abs(overall_mean)
            assert abs(test_mean - overall_mean) < 0.1 * abs(overall_mean)

            # Same for std (avoid division by zero)
            if overall_std > 0:
                assert abs(train_std - overall_std) < 0.1 * overall_std
                assert abs(val_std - overall_std) < 0.1 * overall_std
                assert abs(test_std - overall_std) < 0.1 * overall_std

        finally:
            os.unlink(temp_csv)

    def test_split_indices_with_edge_cases(self):
        """Test split logic with edge cases like small datasets."""
        # Small dataset
        n_samples = 50
        smiles_list = [f"SMILES_{i}" for i in range(n_samples)]
        logS_values = np.random.normal(loc=-3.0, scale=1.5, size=n_samples)

        temp_csv = create_temp_csv({
            'SMILES': smiles_list,
            'logS': logS_values
        })

        try:
            data, _ = load_cleaned_data(temp_csv)

            # Create splits
            train_idx, val_idx, test_idx = create_stratified_splits(
                data,
                train_ratio=0.7,
                val_ratio=0.15,
                test_ratio=0.15,
                n_bins=3,
                random_state=42
            )

            # Verify all indices are within bounds
            assert all(0 <= i < n_samples for i in train_idx)
            assert all(0 <= i < n_samples for i in val_idx)
            assert all(0 <= i < n_samples for i in test_idx)

            # Verify non-empty splits
            assert len(train_idx) > 0
            assert len(val_idx) > 0
            assert len(test_idx) > 0

        finally:
            os.unlink(temp_csv)

    def test_deterministic_splits_with_seed(self):
        """Test that splits are deterministic with the same random seed."""
        np.random.seed(42)
        n_samples = 200
        smiles_list = [f"SMILES_{i}" for i in range(n_samples)]
        logS_values = np.random.normal(loc=-3.0, scale=1.5, size=n_samples)

        temp_csv = create_temp_csv({
            'SMILES': smiles_list,
            'logS': logS_values
        })

        try:
            data, _ = load_cleaned_data(temp_csv)

            # Create splits twice with same seed
            train_idx_1, val_idx_1, test_idx_1 = create_stratified_splits(
                data,
                train_ratio=0.7,
                val_ratio=0.15,
                test_ratio=0.15,
                n_bins=3,
                random_state=42
            )

            train_idx_2, val_idx_2, test_idx_2 = create_stratified_splits(
                data,
                train_ratio=0.7,
                val_ratio=0.15,
                test_ratio=0.15,
                n_bins=3,
                random_state=42
            )

            # Verify splits are identical
            assert train_idx_1 == train_idx_2
            assert val_idx_1 == val_idx_2
            assert test_idx_1 == test_idx_2

        finally:
            os.unlink(temp_csv)

    def test_save_split_indices(self):
        """Test saving and loading split indices."""
        temp_dir = tempfile.mkdtemp()
        try:
            # Create sample indices
            train_idx = [0, 1, 2, 3, 4]
            val_idx = [5, 6, 7]
            test_idx = [8, 9, 10]

            save_split_indices(
                train_idx,
                val_idx,
                test_idx,
                temp_dir,
                "test_split"
            )

            # Verify files were created
            train_file = os.path.join(temp_dir, "test_split_train.json")
            val_file = os.path.join(temp_dir, "test_split_val.json")
            test_file = os.path.join(temp_dir, "test_split_test.json")

            assert os.path.exists(train_file)
            assert os.path.exists(val_file)
            assert os.path.exists(test_file)

            # Verify content
            with open(train_file, 'r') as f:
                loaded_train = json.load(f)
            assert loaded_train == train_idx

            with open(val_file, 'r') as f:
                loaded_val = json.load(f)
            assert loaded_val == val_idx

            with open(test_file, 'r') as f:
                loaded_test = json.load(f)
            assert loaded_test == test_idx

        finally:
            # Cleanup
            for f in [train_file, val_file, test_file]:
                if os.path.exists(f):
                    os.unlink(f)
            os.rmdir(temp_dir)

    def test_quantile_bins_with_equal_distribution(self):
        """Test that quantile bins work correctly with evenly distributed data."""
        # Create evenly distributed logS values
        n_samples = 1000
        smiles_list = [f"SMILES_{i}" for i in range(n_samples)]
        logS_values = np.linspace(-5.0, 5.0, n_samples)

        temp_csv = create_temp_csv({
            'SMILES': smiles_list,
            'logS': logS_values
        })

        try:
            data, _ = load_cleaned_data(temp_csv)

            # Create splits with many bins
            train_idx, val_idx, test_idx = create_stratified_splits(
                data,
                train_ratio=0.7,
                val_ratio=0.15,
                test_ratio=0.15,
                n_bins=10,
                random_state=42
            )

            # Each bin should be represented proportionally in each split
            # Calculate bin assignments
            bins = pd.qcut(data['logS'], q=10, labels=False, duplicates='drop')

            for split_name, split_idx in [('train', train_idx),
                                           ('val', val_idx),
                                           ('test', test_idx)]:
                split_bins = bins.iloc[split_idx]
                # Each bin should have roughly the same representation
                bin_counts = split_bins.value_counts()
                expected_per_bin = len(split_idx) / 10
                for count in bin_counts.values:
                    assert abs(count - expected_per_bin) < expected_per_bin * 0.2

        finally:
            os.unlink(temp_csv)