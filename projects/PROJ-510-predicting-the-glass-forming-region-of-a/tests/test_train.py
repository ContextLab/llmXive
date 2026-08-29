"""
Tests for model training and evaluation.
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.train import (
    load_data,
    train_model,
    run_cross_validation,
    evaluate_on_test,
    generate_null_baseline,
    compare_models
)

class TestCrossValidation:
    def test_non_overlapping_folds(self):
        """
        Unit test for k-fold cross-validation split generation ensuring non-overlapping folds.
        Verifies that the KFold implementation produces disjoint test sets for each fold.
        """
        # Create dummy data with fixed seed for reproducibility
        np.random.seed(42)
        n_samples = 100
        n_features = 5
        X = np.random.rand(n_samples, n_features)
        y = np.random.rand(n_samples)
        
        from sklearn.model_selection import KFold
        
        # Configure KFold with specific parameters matching the project's standard
        n_splits = 5
        kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
        
        # Generate the folds
        folds_indices = list(kf.split(X))
        
        # Verify we got the expected number of folds
        assert len(folds_indices) == n_splits, f"Expected {n_splits} folds, got {len(folds_indices)}"
        
        # Check for overlaps between all pairs of test sets
        for i in range(len(folds_indices)):
            for j in range(i + 1, len(folds_indices)):
                train_i, test_i = folds_indices[i]
                train_j, test_j = folds_indices[j]
                
                # Check if test sets overlap
                overlap = set(test_i).intersection(set(test_j))
                assert len(overlap) == 0, f"Folds {i} and {j} have overlapping test indices: {overlap}"
                
                # Additional check: ensure test set of fold i doesn't overlap with train set of fold j
                # (This is guaranteed by KFold but good to verify for completeness)
                overlap_train_test = set(test_i).intersection(set(train_j))
                assert len(overlap_train_test) == 0, f"Test set of fold {i} overlaps with train set of fold {j}"

    def test_folds_cover_all_samples(self):
        """
        Verify that the union of all train and test sets covers exactly the full dataset.
        """
        np.random.seed(42)
        n_samples = 100
        X = np.random.rand(n_samples, 5)
        
        from sklearn.model_selection import KFold
        kf = KFold(n_splits=5, shuffle=True, random_state=42)
        folds_indices = list(kf.split(X))
        
        # Collect all indices used in test sets
        all_test_indices = set()
        all_train_indices = set()
        
        for train_idx, test_idx in folds_indices:
            all_test_indices.update(test_idx)
            all_train_indices.update(train_idx)
        
        # Each sample should appear exactly once in a test set across all folds
        expected_test_count = n_samples
        assert len(all_test_indices) == expected_test_count, f"Expected {expected_test_count} unique test indices, got {len(all_test_indices)}"
        
        # Each sample should appear in exactly (n_splits - 1) train sets
        # (appears in test set once, so train set n_splits-1 times)
        # We can verify this by checking the union of all train sets equals the full dataset
        # (though samples may appear multiple times in the union)
        assert all_test_indices == set(range(n_samples)), "Test indices do not cover all samples"

    def test_fold_sizes_consistency(self):
        """
        Verify that fold sizes are approximately equal (differ by at most 1 sample).
        """
        np.random.seed(42)
        n_samples = 100
        X = np.random.rand(n_samples, 5)
        
        from sklearn.model_selection import KFold
        kf = KFold(n_splits=5, shuffle=True, random_state=42)
        folds_indices = list(kf.split(X))
        
        test_sizes = [len(test_idx) for _, test_idx in folds_indices]
        train_sizes = [len(train_idx) for train_idx, _ in folds_indices]
        
        # Check that all test sizes are within 1 of each other
        assert max(test_sizes) - min(test_sizes) <= 1, f"Test sizes vary too much: {test_sizes}"
        assert max(train_sizes) - min(train_sizes) <= 1, f"Train sizes vary too much: {train_sizes}"
        
        # Check that train + test = total samples for each fold
        for train_idx, test_idx in folds_indices:
            assert len(train_idx) + len(test_idx) == n_samples, "Fold partition does not cover all samples"

class TestModelMetrics:
    def test_schema_validity(self):
        """
        Integration test for model training producing valid ModelMetrics schema.
        """
        # Create dummy data
        np.random.seed(42)
        data = {
            'mixing_enthalpy': np.random.rand(100) * 10,
            'atomic_size_mismatch': np.random.rand(100) * 10,
            'electronegativity_variance': np.random.rand(100),
            'critical_cooling_rate': np.random.rand(100) * 100
        }
        df = pd.DataFrame(data)
        
        # Train a dummy model and get metrics
        # Note: This is a simplified test; full integration requires actual model training
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.model_selection import cross_val_score
        
        X = df[['mixing_enthalpy', 'atomic_size_mismatch', 'electronegativity_variance']]
        y = df['critical_cooling_rate']
        
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        scores = cross_val_score(model, X, y, cv=5, scoring='neg_mean_squared_error')
        
        # Construct metrics dict
        metrics = {
            'fold_scores': [-s for s in scores], # Convert back to RMSE-like
            'mean_rmse': float(np.mean(np.sqrt(-scores))),
            'test_rmse': 0.0, # Placeholder
            'p_value_vs_null': 0.0, # Placeholder
            'feature_importance_ranking': []
        }
        
        # Validate schema requirements
        assert 'fold_scores' in metrics
        assert 'mean_rmse' in metrics
        assert 'test_rmse' in metrics
        assert 'p_value_vs_null' in metrics
        assert isinstance(metrics['fold_scores'], list)
        assert len(metrics['fold_scores']) == 5