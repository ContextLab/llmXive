"""
Unit tests for stratified split logic in code/data/split.py.

This test suite verifies that the perform_stratified_split function:
1. Correctly splits data into train and test sets.
2. Maintains label balance (stratification) across splits.
3. Handles edge cases like small datasets or single-class data gracefully.
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from data.split import perform_stratified_split


class TestStratifiedSplit:
    """Tests for the perform_stratified_split function."""

    def test_stratified_split_preserves_label_ratio(self):
        """Test that the train/test split preserves the original label distribution."""
        # Create a dataset with known label distribution (70% class 0, 30% class 1)
        n_samples = 1000
        n_features = 10
        labels = np.array([0] * 700 + [1] * 300)
        features = np.random.rand(n_samples, n_features)
        species_ids = [f"species_{i}" for i in range(n_samples)]

        df = pd.DataFrame(features, columns=[f"feature_{i}" for i in range(n_features)])
        df["species_id"] = species_ids
        df["label"] = labels

        train_df, test_df = perform_stratified_split(df, test_size=0.2, random_state=42)

        # Check original distribution
        original_ratio = labels.mean()

        # Check train distribution
        train_ratio = train_df["label"].mean()

        # Check test distribution
        test_ratio = test_df["label"].mean()

        # Allow for small floating point differences (stratification isn't perfect with small counts)
        # With 300 positive samples and 20% test size, we expect ~60 positive in test.
        # Ratio should be close to 0.3
        assert abs(train_ratio - original_ratio) < 0.02, f"Train ratio {train_ratio} differs too much from original {original_ratio}"
        assert abs(test_ratio - original_ratio) < 0.02, f"Test ratio {test_ratio} differs too much from original {original_ratio}"

    def test_split_sizes(self):
        """Test that the split sizes match the requested test_size."""
        n_samples = 500
        n_features = 5
        labels = np.random.randint(0, 2, n_samples)
        features = np.random.rand(n_samples, n_features)
        species_ids = [f"species_{i}" for i in range(n_samples)]

        df = pd.DataFrame(features, columns=[f"feature_{i}" for i in range(n_features)])
        df["species_id"] = species_ids
        df["label"] = labels

        test_size = 0.25
        train_df, test_df = perform_stratified_split(df, test_size=test_size, random_state=42)

        expected_test_count = int(n_samples * test_size)
        expected_train_count = n_samples - expected_test_count

        assert len(test_df) == expected_test_count, f"Test set size {len(test_df)} != expected {expected_test_count}"
        assert len(train_df) == expected_train_count, f"Train set size {len(train_df)} != expected {expected_train_count}"

    def test_split_no_data_leakage(self):
        """Test that there is no overlap between train and test sets."""
        n_samples = 200
        n_features = 5
        labels = np.random.randint(0, 2, n_samples)
        features = np.random.rand(n_samples, n_features)
        species_ids = [f"species_{i}" for i in range(n_samples)]

        df = pd.DataFrame(features, columns=[f"feature_{i}" for i in range(n_features)])
        df["species_id"] = species_ids
        df["label"] = labels

        train_df, test_df = perform_stratified_split(df, test_size=0.2, random_state=42)

        train_ids = set(train_df["species_id"].tolist())
        test_ids = set(test_df["species_id"].tolist())

        # Check intersection is empty
        assert len(train_ids.intersection(test_ids)) == 0, "Found overlapping species IDs between train and test sets"

        # Check union equals original
        assert len(train_ids.union(test_ids)) == n_samples, "Union of train and test IDs does not equal original dataset size"

    def test_small_dataset_fallback(self):
        """Test behavior with a very small dataset (should fallback or handle gracefully)."""
        # Create a tiny dataset
        df = pd.DataFrame({
            "feature_1": [1.0, 2.0, 3.0, 4.0],
            "species_id": ["sp1", "sp2", "sp3", "sp4"],
            "label": [0, 0, 1, 1]
        })

        # With only 4 samples, standard stratified split might fail or produce very small sets.
        # The function should handle this without crashing.
        train_df, test_df = perform_stratified_split(df, test_size=0.25, random_state=42)

        assert len(train_df) > 0, "Train set is empty"
        assert len(test_df) > 0, "Test set is empty"
        assert len(train_df) + len(test_df) == 4, "Total samples mismatch"

    def test_single_class_dataset(self):
        """Test behavior when the dataset contains only one class."""
        df = pd.DataFrame({
            "feature_1": [1.0, 2.0, 3.0, 4.0, 5.0],
            "species_id": ["sp1", "sp2", "sp3", "sp4", "sp5"],
            "label": [0, 0, 0, 0, 0]
        })

        # Stratified split on single class should still work (just split the single class)
        train_df, test_df = perform_stratified_split(df, test_size=0.2, random_state=42)

        assert len(train_df) > 0
        assert len(test_df) > 0
        assert train_df["label"].unique().tolist() == [0]
        assert test_df["label"].unique().tolist() == [0]

    def test_random_state_reproducibility(self):
        """Test that the same random_state produces the same split."""
        df = pd.DataFrame({
            "feature_1": np.random.rand(100),
            "feature_2": np.random.rand(100),
            "species_id": [f"sp_{i}" for i in range(100)],
            "label": np.random.randint(0, 2, 100)
        })

        train1, test1 = perform_stratified_split(df, test_size=0.2, random_state=123)
        train2, test2 = perform_stratified_split(df, test_size=0.2, random_state=123)

        # Compare species IDs
        assert set(train1["species_id"].tolist()) == set(train2["species_id"].tolist())
        assert set(test1["species_id"].tolist()) == set(test2["species_id"].tolist())

        # Compare values (order might differ if not sorted, so compare sets of tuples)
        train1_sorted = train1.sort_values("species_id").reset_index(drop=True)
        train2_sorted = train2.sort_values("species_id").reset_index(drop=True)
        pd.testing.assert_frame_equal(train1_sorted, train2_sorted)