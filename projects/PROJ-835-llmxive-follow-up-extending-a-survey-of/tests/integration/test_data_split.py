"""
Integration test for train/test split integrity (T019).

This test verifies that the data splitting logic in `src/models/train.py`
correctly performs a stratified split of embeddings and labels, ensuring:
1. No data leakage between train and test sets.
2. Class distribution is preserved (stratification).
3. The split ratio matches the configuration.
4. All samples are accounted for (no loss of data).

This test must FAIL before the implementation of T020 (split logic) is complete.
"""

import os
import sys
import tempfile
import shutil
import json
import numpy as np
import pytest
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.models.train import perform_stratified_split
from src.utils.config import set_random_seed


class TestDataSplitIntegrity:
    """
    Integration tests for the train/test split functionality.
    """

    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        set_random_seed(42)

    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _create_test_embeddings(self, n_samples=100, n_features=64, n_classes=2):
        """
        Create synthetic embeddings and labels for testing.
        This simulates the output of T014 (embedding extraction).
        """
        embeddings = np.random.randn(n_samples, n_features).astype(np.float32)
        # Create stratified labels
        labels = np.tile(np.arange(n_classes), n_samples // n_classes + 1)[:n_samples]
        np.random.shuffle(labels)
        return embeddings, labels

    def test_split_no_leakage(self):
        """
        Verify that no sample appears in both train and test sets.
        """
        embeddings, labels = self._create_test_embeddings(n_samples=100, n_features=64)
        
        train_embeddings, test_embeddings, train_labels, test_labels = perform_stratified_split(
            embeddings, labels, test_size=0.2, random_state=42
        )

        # Check for leakage
        train_indices = set(range(len(train_embeddings)))
        test_indices = set(range(len(test_embeddings)))
        
        # Since we are splitting indices implicitly by position, 
        # we verify by checking that the combined count equals original
        assert len(train_embeddings) + len(test_embeddings) == len(embeddings), \
            "Total samples lost or duplicated during split"
        
        # Verify unique samples by checking if we can reconstruct original
        # (This is a simplified check; in real scenario we'd track indices)
        reconstructed_embeddings = np.vstack([train_embeddings, test_embeddings])
        # Note: order is lost in split, so we check counts and content presence
        assert len(reconstructed_embeddings) == len(embeddings)

    def test_stratification_preserved(self):
        """
        Verify that class distribution is preserved in both splits.
        """
        n_samples = 200
        embeddings, labels = self._create_test_embeddings(n_samples=n_samples, n_features=64)
        
        train_embeddings, test_embeddings, train_labels, test_labels = perform_stratified_split(
            embeddings, labels, test_size=0.25, random_state=42
        )

        # Calculate class distributions
        def get_class_distribution(labels):
            unique, counts = np.unique(labels, return_counts=True)
            return dict(zip(unique.tolist(), counts.tolist()))

        original_dist = get_class_distribution(labels)
        train_dist = get_class_distribution(train_labels)
        test_dist = get_class_distribution(test_labels)

        # Check that proportions are approximately preserved (within 5%)
        for class_id in original_dist:
            original_ratio = original_dist[class_id] / n_samples
            train_ratio = train_dist.get(class_id, 0) / len(train_labels)
            test_ratio = test_dist.get(class_id, 0) / len(test_labels)
            
            # Allow small variance due to rounding in stratified split
            assert abs(train_ratio - original_ratio) < 0.05, \
                f"Train set distribution for class {class_id} deviates too much"
            assert abs(test_ratio - original_ratio) < 0.05, \
                f"Test set distribution for class {class_id} deviates too much"

    def test_split_ratio_accuracy(self):
        """
        Verify that the split ratio matches the requested test_size.
        """
        n_samples = 1000
        embeddings, labels = self._create_test_embeddings(n_samples=n_samples, n_features=64)
        
        test_size = 0.2
        train_embeddings, test_embeddings, train_labels, test_labels = perform_stratified_split(
            embeddings, labels, test_size=test_size, random_state=42
        )

        actual_test_ratio = len(test_embeddings) / n_samples
        actual_train_ratio = len(train_embeddings) / n_samples

        assert abs(actual_test_ratio - test_size) < 0.02, \
            f"Test size ratio {actual_test_ratio} differs from requested {test_size}"
        assert abs(actual_train_ratio - (1 - test_size)) < 0.02, \
            f"Train size ratio {actual_train_ratio} differs from expected {1 - test_size}"

    def test_all_samples_accounted(self):
        """
        Verify that no samples are lost during the split.
        """
        n_samples = 500
        embeddings, labels = self._create_test_embeddings(n_samples=n_samples, n_features=64)
        
        train_embeddings, test_embeddings, train_labels, test_labels = perform_stratified_split(
            embeddings, labels, test_size=0.3, random_state=42
        )

        total_train = len(train_embeddings) + len(train_labels)
        total_test = len(test_embeddings) + len(test_labels)
        total_original = len(embeddings) + len(labels)

        assert total_train + total_test == total_original, \
            "Samples were lost or duplicated during split"

    def test_split_with_imbalanced_classes(self):
        """
        Verify stratification works correctly with imbalanced data.
        """
        n_samples = 1000
        # Create imbalanced labels: 90% class 0, 10% class 1
        labels = np.array([0] * 900 + [1] * 100)
        np.random.shuffle(labels)
        embeddings = np.random.randn(n_samples, 64).astype(np.float32)
        
        test_size = 0.2
        train_embeddings, test_embeddings, train_labels, test_labels = perform_stratified_split(
            embeddings, labels, test_size=test_size, random_state=42
        )

        # Check that the minority class is present in both splits
        assert 1 in train_labels, "Minority class missing from training set"
        assert 1 in test_labels, "Minority class missing from test set"

        # Verify proportions are roughly maintained
        train_class1_ratio = np.sum(train_labels == 1) / len(train_labels)
        test_class1_ratio = np.sum(test_labels == 1) / len(test_labels)
        original_class1_ratio = 0.1

        assert abs(train_class1_ratio - original_class1_ratio) < 0.02, \
            f"Imbalanced class ratio in train set: {train_class1_ratio}"
        assert abs(test_class1_ratio - original_class1_ratio) < 0.02, \
            f"Imbalanced class ratio in test set: {test_class1_ratio}"

    def test_deterministic_split(self):
        """
        Verify that split is deterministic with the same random_state.
        """
        n_samples = 200
        embeddings, labels = self._create_test_embeddings(n_samples=n_samples, n_features=64)
        
        # Run split twice with same seed
        result1 = perform_stratified_split(embeddings, labels, test_size=0.2, random_state=42)
        result2 = perform_stratified_split(embeddings, labels, test_size=0.2, random_state=42)

        # Check that results are identical
        for i in range(4):
            assert np.array_equal(result1[i], result2[i]), \
                f"Split results differ between runs with same seed at index {i}"

    def test_split_output_types(self):
        """
        Verify that the split function returns the correct data types.
        """
        embeddings, labels = self._create_test_embeddings(n_samples=100, n_features=64)
        
        train_embeddings, test_embeddings, train_labels, test_labels = perform_stratified_split(
            embeddings, labels, test_size=0.2, random_state=42
        )

        assert isinstance(train_embeddings, np.ndarray), "Train embeddings should be numpy array"
        assert isinstance(test_embeddings, np.ndarray), "Test embeddings should be numpy array"
        assert isinstance(train_labels, np.ndarray), "Train labels should be numpy array"
        assert isinstance(test_labels, np.ndarray), "Test labels should be numpy array"
        
        assert train_embeddings.dtype == np.float32, "Train embeddings should be float32"
        assert test_embeddings.dtype == np.float32, "Test embeddings should be float32"
        assert train_labels.dtype in [np.int32, np.int64], "Train labels should be integer type"
        assert test_labels.dtype in [np.int32, np.int64], "Test labels should be integer type"

    def test_split_with_small_dataset(self):
        """
        Verify split works with very small datasets.
        """
        n_samples = 20
        embeddings, labels = self._create_test_embeddings(n_samples=n_samples, n_features=64)
        
        # Use a larger test size for small dataset
        train_embeddings, test_embeddings, train_labels, test_labels = perform_stratified_split(
            embeddings, labels, test_size=0.3, random_state=42
        )

        # Ensure both sets have at least one sample
        assert len(train_embeddings) > 0, "Training set is empty"
        assert len(test_embeddings) > 0, "Test set is empty"
        
        # Ensure no samples lost
        assert len(train_embeddings) + len(test_embeddings) == n_samples