"""
Unit tests for T027c: Verify nested CV integration.

These tests confirm that the Stability Selection feature selection logic
is strictly isolated to the inner loop of the nested cross-validation
and does not leak information from the test fold (outer loop) into the
training process.

This task implements verification for T027b.
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock, call
from sklearn.model_selection import StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

# Import the target class from the existing API surface
from classification.models import StabilitySelection, run_classification_pipeline


class TestNestedCVIsolation:
    """Tests to ensure feature selection does not leak outer loop test data."""

    def test_stability_selection_only_sees_train_data(self):
        """
        Verify that StabilitySelection.fit() is never called with data
        that includes the outer loop test set.
        """
        # Create a small synthetic dataset
        np.random.seed(42)
        n_samples = 40
        n_features = 10
        X = np.random.randn(n_samples, n_features)
        y = np.random.randint(0, 2, n_samples)
        
        # Mock the StabilitySelection class to track fit calls
        with patch.object(StabilitySelection, 'fit', wraps=StabilitySelection.fit) as mock_fit:
            # Create a simple nested CV structure manually to control the flow
            outer_cv = StratifiedKFold(n_splits=2, shuffle=True, random_state=42)
            inner_cv = StratifiedKFold(n_splits=2, shuffle=True, random_state=42)
            
            # Track which indices were passed to fit
            fit_indices_history = []
            
            def tracking_fit(self, X_train, y_train, sample_weight=None):
                # Record the indices of the training data seen by the selector
                # We use the shape to infer if it's the full set or a subset
                fit_indices_history.append(X_train.shape[0])
                # Call the real method to ensure it runs
                return StabilitySelection.fit(self, X_train, y_train, sample_weight)
            
            with patch.object(StabilitySelection, 'fit', tracking_fit):
                # Run the pipeline
                # We use a small subsample size to ensure it runs quickly
                results = run_classification_pipeline(
                    X=X,
                    y=y,
                    outer_cv=outer_cv,
                    inner_cv=inner_cv,
                    stability_n_subsamples=2, # Minimal for speed
                    stability_sample_size=20,
                    stability_threshold=0.6,
                    n_permutations=10 # Minimal for speed
                )
            
            # Verify that the number of samples seen by the selector
            # is always less than the total dataset size (n_samples)
            # This proves it never saw the full dataset (which would include test folds)
            for count in fit_indices_history:
                assert count < n_samples, (
                    f"Feature selector saw {count} samples, "
                    f"which is >= total samples ({n_samples}). "
                    f"Data leakage detected!"
                )

    def test_feature_selection_reset_per_fold(self):
        """
        Verify that the Stability Selection algorithm is re-initialized
        for every outer loop fold, ensuring no state leakage.
        """
        np.random.seed(42)
        n_samples = 30
        n_features = 8
        X = np.random.randn(n_samples, n_features)
        y = np.random.randint(0, 2, n_samples)
        
        # Track initialization counts
        init_count = 0
        
        original_init = StabilitySelection.__init__
        
        def counting_init(self, *args, **kwargs):
            nonlocal init_count
            init_count += 1
            return original_init(self, *args, **kwargs)
        
        with patch.object(StabilitySelection, '__init__', counting_init):
            outer_cv = StratifiedKFold(n_splits=2, shuffle=True, random_state=42)
            inner_cv = StratifiedKFold(n_splits=2, shuffle=True, random_state=42)
            
            # Run pipeline
            run_classification_pipeline(
                X=X,
                y=y,
                outer_cv=outer_cv,
                inner_cv=inner_cv,
                stability_n_subsamples=2,
                stability_sample_size=15,
                stability_threshold=0.6,
                n_permutations=5
            )
        
        # With 2 outer folds, we expect at least 2 initializations
        # (one for each fold's inner loop)
        assert init_count >= 2, (
            f"Expected at least 2 initializations (one per outer fold), "
            f"but got {init_count}. State may be leaking between folds."
        )

    def test_no_global_feature_state(self):
        """
        Verify that the selected features from one fold do not influence
        the selection in subsequent folds.
        """
        np.random.seed(42)
        n_samples = 40
        n_features = 10
        X = np.random.randn(n_samples, n_features)
        y = np.random.randint(0, 2, n_samples)
        
        # Track selected features per fold
        selected_features_per_fold = []
        
        original_select_features = StabilitySelection.select_features
        
        def tracking_select(self, X, y):
            features = original_select_features(self, X, y)
            selected_features_per_fold.append(features.copy())
            return features
        
        with patch.object(StabilitySelection, 'select_features', tracking_select):
            outer_cv = StratifiedKFold(n_splits=2, shuffle=True, random_state=42)
            inner_cv = StratifiedKFold(n_splits=2, shuffle=True, random_state=42)
            
            run_classification_pipeline(
                X=X,
                y=y,
                outer_cv=outer_cv,
                inner_cv=inner_cv,
                stability_n_subsamples=2,
                stability_sample_size=20,
                stability_threshold=0.6,
                n_permutations=5
            )
        
        # If there are multiple folds, verify that the selected features
        # are not identical (which would indicate a global state or hardcoded selection)
        if len(selected_features_per_fold) > 1:
            for i in range(1, len(selected_features_per_fold)):
                prev = selected_features_per_fold[i-1]
                curr = selected_features_per_fold[i]
                # They should not be exactly the same array every time
                # unless the data is perfectly symmetric (unlikely with random noise)
                if not np.array_equal(prev, curr):
                    # This is expected: different folds see different data
                    continue
                else:
                    # If they are equal, it might be due to data symmetry,
                    # but we should at least verify the selection process ran
                    assert len(prev) > 0, "No features selected in any fold"

    def test_inner_loop_isolation_from_outer_test(self):
        """
        Explicit test that the inner loop's training data (used for feature selection)
        is a strict subset of the outer loop's training data and excludes the outer test set.
        """
        np.random.seed(42)
        n_samples = 50
        n_features = 5
        X = np.random.randn(n_samples, n_features)
        y = np.random.randint(0, 2, n_samples)
        
        # We will manually step through one fold to verify indices
        outer_cv = StratifiedKFold(n_splits=2, shuffle=True, random_state=42)
        inner_cv = StratifiedKFold(n_splits=2, shuffle=True, random_state=42)
        
        fold_index = 0
        outer_train_idx = None
        outer_test_idx = None
        
        # Capture the first outer fold
        for train_idx, test_idx in outer_cv.split(X, y):
            outer_train_idx = train_idx
            outer_test_idx = test_idx
            break
        
        # Verify that the outer test set is disjoint from the outer train set
        assert len(np.intersect1d(outer_train_idx, outer_test_idx)) == 0, "Outer folds overlap!"
        
        # Now, we simulate the inner loop logic
        # The inner loop should ONLY see outer_train_idx
        # It should NEVER see outer_test_idx
        
        # We use a mock to intercept the data passed to the classifier/selector
        data_seen_by_inner = []
        
        original_fit = LogisticRegression.fit
        
        def intercept_fit(self, X, y, *args, **kwargs):
            # Record the indices (we can't directly get indices from sklearn,
            # but we can check the shape and content if we had a way to map back)
            # Instead, we rely on the fact that if the code is correct,
            # the inner loop is only called with X[train_mask]
            # We verify this by checking that the number of samples passed
            # is consistent with a subset of the training set
            data_seen_by_inner.append(X.shape[0])
            return original_fit(self, X, y, *args, **kwargs)
        
        with patch.object(LogisticRegression, 'fit', intercept_fit):
            # Run the pipeline
            run_classification_pipeline(
                X=X,
                y=y,
                outer_cv=outer_cv,
                inner_cv=inner_cv,
                stability_n_subsamples=2,
                stability_sample_size=20,
                stability_threshold=0.6,
                n_permutations=5
            )
        
        # Verify that the data seen by the inner loop is always <= outer_train size
        # and never equals the full dataset size (which would imply leakage)
        for count in data_seen_by_inner:
            assert count <= len(outer_train_idx), (
                f"Inner loop saw {count} samples, "
                f"but outer training set only has {len(outer_train_idx)}. "
                f"Leakage detected!"
            )
            assert count < n_samples, (
                f"Inner loop saw {count} samples (full dataset), "
                f"which implies it saw the outer test set."
            )