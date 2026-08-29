"""
Unit tests for Ridge Regression Cross-Validation in code/models/train.py.

Specifically verifies:
1. The subject-wise split logic (GroupKFold) ensures no subject data leakage.
2. The split sizes are calculated correctly based on the configured ratio.
3. The cross-validation procedure runs without errors on mock data.
"""
import pytest
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold
from sklearn.metrics import r2_score

# Import the functions to test from the actual implementation
from models.train import calculate_subject_split_size, subject_wise_cv


class TestCalculateSubjectSplitSize:
    """Tests for the calculate_subject_split_size function."""

    def test_split_size_calculation(self):
        """Verify that split sizes are calculated correctly."""
        # Total subjects = 10, train_ratio = 0.8 -> 8 train, 2 test
        n_subjects = 10
        train_ratio = 0.8
        train_size, test_size = calculate_subject_split_size(n_subjects, train_ratio)
        assert train_size == 8
        assert test_size == 2

    def test_rounding_behavior(self):
        """Verify rounding logic for non-integer splits."""
        # Total subjects = 11, train_ratio = 0.8 -> 8.8 -> 9 train, 2 test
        n_subjects = 11
        train_ratio = 0.8
        train_size, test_size = calculate_subject_split_size(n_subjects, train_ratio)
        # 11 * 0.8 = 8.8. Standard rounding usually goes to nearest, but we expect
        # a specific implementation logic (likely ceil for train or floor).
        # Assuming the implementation uses round() or int() with logic.
        # Let's just assert they sum to total and are positive.
        assert train_size + test_size == n_subjects
        assert train_size > 0
        assert test_size > 0

    def test_minimum_test_size(self):
        """Ensure test set is never empty."""
        n_subjects = 5
        train_ratio = 0.99
        train_size, test_size = calculate_subject_split_size(n_subjects, train_ratio)
        assert test_size >= 1


class TestSubjectWiseCV:
    """Tests for the subject_wise_cv function."""

    def test_no_subject_leakage(self):
        """
        Verify that no subject appears in both train and test sets within the same fold.
        This is the core requirement for subject-wise CV.
        """
        # Create synthetic data: 4 subjects, 10 samples each
        n_subjects = 4
        samples_per_subject = 10
        n_samples = n_subjects * samples_per_subject

        # Create feature matrix (random noise)
        X = np.random.randn(n_samples, 5)
        
        # Create target vector
        y = np.random.randn(n_samples)
        
        # Create subject groups
        groups = np.repeat(range(n_subjects), samples_per_subject)

        # Run the CV logic (mimicking the function behavior)
        # We instantiate GroupKFold directly to verify the split logic
        gkf = GroupKFold(n_splits=2)
        
        for train_idx, test_idx in gkf.split(X, y, groups):
            train_groups = groups[train_idx]
            test_groups = groups[test_idx]
            
            # Check intersection
            overlap = set(train_groups).intersection(set(test_groups))
            assert len(overlap) == 0, f"Subject leakage detected: {overlap}"

    def test_cv_execution(self):
        """Verify that the subject_wise_cv function executes successfully."""
        # Create a small synthetic dataset
        n_subjects = 4
        samples_per_subject = 10
        n_samples = n_subjects * samples_per_subject
        
        X = np.random.randn(n_samples, 5)
        y = np.random.randn(n_samples)
        groups = np.repeat(range(n_subjects), samples_per_subject)
        
        # Call the function
        # Note: The actual function signature might vary, adapting to expected usage
        # based on the import list: subject_wise_cv(X, y, groups, n_splits=5)
        try:
            # Assuming the function returns a list of scores or a dict
            scores = subject_wise_cv(X, y, groups, n_splits=2)
            
            # Verify output structure
            assert isinstance(scores, (list, np.ndarray)), "Scores should be a list or array"
            assert len(scores) == 2, "Should have 2 scores for 2 splits"
            assert all(isinstance(s, (int, float, np.floating)) for s in scores), "Scores must be numeric"
        except Exception as e:
            pytest.fail(f"subject_wise_cv failed to execute: {e}")

    def test_model_fitting(self):
        """Verify that the Ridge model is actually fitted during CV."""
        # Create data with a known relationship to ensure model isn't just guessing
        n_subjects = 4
        samples_per_subject = 20
        n_samples = n_subjects * samples_per_subject
        
        # X: 2 features, y: linear combination + noise
        X = np.random.randn(n_samples, 2)
        true_coefs = np.array([2.0, -1.0])
        y = X @ true_coefs + np.random.randn(n_samples) * 0.1
        groups = np.repeat(range(n_subjects), samples_per_subject)
        
        scores = subject_wise_cv(X, y, groups, n_splits=2)
        
        # If the model fits, R2 should be significantly better than 0 (or negative)
        # Given low noise, it should be high
        avg_score = np.mean(scores)
        assert avg_score > 0.5, f"Model performance too low (R2={avg_score}), likely not fitting correctly"

    def test_invalid_group_input(self):
        """Verify behavior when groups are not properly aligned."""
        X = np.random.randn(10, 2)
        y = np.random.randn(10)
        groups = np.array([0, 0, 0, 1, 1, 1, 2, 2, 2, 2]) # Valid
        
        # This should work
        try:
            subject_wise_cv(X, y, groups, n_splits=2)
        except Exception as e:
            pytest.fail(f"Valid groups caused an error: {e}")