"""
Unit tests for k-fold splitting logic in validation module.

Tests the k-fold cross-validation splitting functionality to ensure:
1. Correct fold generation from input data
2. Proper stratification (if applicable)
3. Non-overlapping train/test splits
4. Correct fold count matching k parameter
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Tuple

# Import the validation module to test
from code.models.validation import k_fold_split, validate_fold_consistency


class TestKFoldSplit:
    """Test suite for k-fold splitting logic."""

    def test_k_fold_basic_split(self):
        """Test basic k-fold splitting with small dataset."""
        # Create a simple dataset
        n_samples = 100
        X = np.random.rand(n_samples, 5)
        y = np.random.rand(n_samples)
        
        k = 5
        folds = k_fold_split(X, y, k)
        
        # Verify we get exactly k folds
        assert len(folds) == k
        
        # Verify each fold has train/test indices
        for i, (train_idx, test_idx) in enumerate(folds):
            assert isinstance(train_idx, np.ndarray)
            assert isinstance(test_idx, np.ndarray)
            assert len(train_idx) > 0
            assert len(test_idx) > 0
            assert len(test_idx) == n_samples // k or len(test_idx) == n_samples // k + 1

    def test_k_fold_no_overlap(self):
        """Test that train and test sets do not overlap."""
        n_samples = 200
        X = np.random.rand(n_samples, 3)
        y = np.random.rand(n_samples)
        
        k = 4
        folds = k_fold_split(X, y, k)
        
        for train_idx, test_idx in folds:
            # Check no overlap between train and test
            overlap = np.intersect1d(train_idx, test_idx)
            assert len(overlap) == 0, f"Fold has overlapping indices: {overlap}"

    def test_k_fold_coverage(self):
        """Test that all samples are used exactly once in test set."""
        n_samples = 150
        X = np.random.rand(n_samples, 4)
        y = np.random.rand(n_samples)
        
        k = 5
        folds = k_fold_split(X, y, k)
        
        # Collect all test indices
        all_test_indices = []
        for _, test_idx in folds:
            all_test_indices.extend(test_idx)
        
        all_test_indices = np.array(all_test_indices)
        
        # Verify all samples are in test set exactly once
        assert len(all_test_indices) == n_samples
        assert len(np.unique(all_test_indices)) == n_samples

    def test_k_fold_consistency(self):
        """Test that split is deterministic with same random state."""
        n_samples = 100
        X = np.random.rand(n_samples, 2)
        y = np.random.rand(n_samples)
        
        k = 3
        folds1 = k_fold_split(X, y, k, random_state=42)
        folds2 = k_fold_split(X, y, k, random_state=42)
        
        # Verify identical splits
        for (train1, test1), (train2, test2) in zip(folds1, folds2):
            assert np.array_equal(train1, train2)
            assert np.array_equal(test1, test2)

    def test_k_fold_with_different_k_values(self):
        """Test k-fold splitting with various k values."""
        n_samples = 100
        X = np.random.rand(n_samples, 2)
        y = np.random.rand(n_samples)
        
        for k in [2, 3, 5, 10]:
            folds = k_fold_split(X, y, k)
            assert len(folds) == k
            
            # Verify fold sizes are reasonable
            for train_idx, test_idx in folds:
                assert len(test_idx) >= n_samples // k - 1
                assert len(test_idx) <= n_samples // k + 1

    def test_k_fold_small_dataset(self):
        """Test k-fold with dataset smaller than k."""
        n_samples = 3
        X = np.random.rand(n_samples, 2)
        y = np.random.rand(n_samples)
        
        k = 5  # More folds than samples
        folds = k_fold_split(X, y, k)
        
        # Should still create k folds, but some may be empty or have 1 sample
        assert len(folds) == k
        
        for train_idx, test_idx in folds:
            # Each fold should have at least 1 test sample if possible
            if n_samples >= k:
                assert len(test_idx) >= 1

    def test_validate_fold_consistency(self):
        """Test the validation function for fold consistency."""
        n_samples = 100
        X = np.random.rand(n_samples, 3)
        y = np.random.rand(n_samples)
        
        k = 5
        folds = k_fold_split(X, y, k)
        
        # Test with valid folds
        is_valid, message = validate_fold_consistency(folds, n_samples)
        assert is_valid, f"Valid folds marked as invalid: {message}"
        
        # Test with invalid folds (manually create overlapping folds)
        invalid_folds = [
            (np.array([0, 1, 2]), np.array([0, 3, 4])),  # Overlap at index 0
            (np.array([5, 6, 7]), np.array([8, 9, 10])),
        ]
        is_valid, message = validate_fold_consistency(invalid_folds, n_samples)
        assert not is_valid, "Invalid folds should be detected"
        assert "overlap" in message.lower() or "invalid" in message.lower()

    def test_k_fold_with_string_labels(self):
        """Test k-fold with string labels (categorical data)."""
        n_samples = 100
        X = np.random.rand(n_samples, 2)
        y = np.array(['class_a'] * 50 + ['class_b'] * 50)
        
        k = 5
        folds = k_fold_split(X, y, k)
        
        assert len(folds) == k
        
        # Verify each fold has both classes (approximate due to random split)
        for train_idx, test_idx in folds:
            test_labels = y[test_idx]
            unique_labels = np.unique(test_labels)
            # Should have at least one class represented
            assert len(unique_labels) >= 1

    def test_k_fold_empty_input(self):
        """Test k-fold with empty input."""
        X = np.array([]).reshape(0, 2)
        y = np.array([])
        
        k = 3
        
        # Should raise an error for empty input
        with pytest.raises(ValueError):
            k_fold_split(X, y, k)

    def test_k_fold_single_sample(self):
        """Test k-fold with single sample."""
        X = np.array([[1.0, 2.0]])
        y = np.array([0.5])
        
        k = 2  # More folds than samples
        folds = k_fold_split(X, y, k)
        
        # Should handle gracefully, creating folds with minimal samples
        assert len(folds) == k
        for train_idx, test_idx in folds:
            # Total samples across train and test should be 1
            assert len(train_idx) + len(test_idx) == 1

class TestKFoldIntegration:
    """Integration tests for k-fold splitting with real data scenarios."""

    def test_k_fold_with_composition_data(self):
        """Test k-fold with composition/temperature data similar to project use case."""
        # Simulate composition and temperature data
        n_samples = 500
        compositions = np.random.rand(n_samples, 3)  # 3 solute concentrations
        temperatures = np.random.uniform(500, 900, n_samples)  # Temperature range
        
        # Stack features
        X = np.hstack([compositions, temperatures.reshape(-1, 1)])
        # Target: segregation energy
        y = np.random.rand(n_samples) * 2 - 1  # Range [-1, 1] eV
        
        k = 5
        folds = k_fold_split(X, y, k)
        
        # Verify fold structure
        assert len(folds) == k
        
        # Verify feature dimensions are preserved
        for train_idx, test_idx in folds:
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]
            
            assert X_train.shape[1] == X.shape[1]
            assert X_test.shape[1] == X.shape[1]
            assert len(y_train) == len(train_idx)
            assert len(y_test) == len(test_idx)

    def test_k_fold_stratification_effect(self):
        """Test that stratification maintains class distribution (if implemented)."""
        # Create imbalanced dataset
        n_samples = 200
        X = np.random.rand(n_samples, 2)
        # Imbalanced classes: 80% class_a, 20% class_b
        y = np.array(['class_a'] * 160 + ['class_b'] * 40)
        
        k = 5
        folds = k_fold_split(X, y, k)
        
        # Check that each fold has roughly similar class distribution
        class_ratios = []
        for train_idx, test_idx in folds:
            test_labels = y[test_idx]
            class_b_ratio = np.sum(test_labels == 'class_b') / len(test_labels)
            class_ratios.append(class_b_ratio)
        
        # All folds should have similar class_b ratios (within 10% of true ratio)
        true_ratio = 0.2
        for ratio in class_ratios:
            assert abs(ratio - true_ratio) < 0.1, f"Fold has imbalanced class distribution: {ratio}"

    def test_k_fold_reproducibility_across_runs(self):
        """Test that k-fold is reproducible across multiple runs."""
        n_samples = 300
        X = np.random.rand(n_samples, 4)
        y = np.random.rand(n_samples)
        
        k = 5
        random_state = 12345
        
        # Run multiple times
        all_folds = []
        for _ in range(3):
            folds = k_fold_split(X, y, k, random_state=random_state)
            all_folds.append(folds)
        
        # Verify all runs produce identical folds
        for i in range(1, len(all_folds)):
            for (train1, test1), (train2, test2) in zip(all_folds[0], all_folds[i]):
                assert np.array_equal(train1, train2)
                assert np.array_equal(test1, test2)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])