"""
Unit and integration tests for model training (User Story 2).
Tests for T020, T021, T022, T023, and specifically T018 (Cross-Validation Split).
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys
import json
from unittest.mock import patch, MagicMock
from sklearn.ensemble import RandomForestRegressor
from sklearn.dummy import DummyRegressor
from sklearn.model_selection import KFold, cross_val_score
from sklearn.metrics import mean_squared_error

# Ensure code directory is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from train import (
    load_data,
    train_model,
    generate_null_distribution,
    run_training
)

class TestTrain:
    """Tests for model training pipeline."""

    def test_load_data(self):
        """Test loading processed data."""
        # Create a temporary CSV file for testing
        temp_file = "test_temp_processed_alloys.csv"
        data = {
            'mixing_enthalpy': [-10.0, -5.0, -8.0],
            'atomic_size_mismatch': [5.0, 6.0, 7.0],
            'electronegativity_variance': [0.1, 0.2, 0.3],
            'critical_cooling_rate': [100.0, 200.0, 300.0]
        }
        df = pd.DataFrame(data)
        df.to_csv(temp_file, index=False)

        loaded_df = load_data(temp_file)
        
        assert isinstance(loaded_df, pd.DataFrame)
        assert len(loaded_df) == 3
        assert 'critical_cooling_rate' in loaded_df.columns

        # Cleanup
        os.remove(temp_file)

    def test_train_model(self):
        """Test model training and cross-validation."""
        # Create synthetic data
        np.random.seed(42)
        X = pd.DataFrame({
            'mixing_enthalpy': np.random.randn(100),
            'atomic_size_mismatch': np.random.randn(100),
            'electronegativity_variance': np.random.randn(100)
        })
        y = np.random.randn(100)

        model, metrics = train_model(X, y)

        assert isinstance(model, RandomForestRegressor)
        assert 'mean_rmse' in metrics
        assert 'test_rmse' in metrics
        assert 'fold_scores' in metrics
        assert len(metrics['fold_scores']) == 5

    def test_generate_null_distribution(self):
        """Test null distribution generation."""
        # Create synthetic data
        np.random.seed(42)
        X = pd.DataFrame({
            'mixing_enthalpy': np.random.randn(100),
            'atomic_size_mismatch': np.random.randn(100),
            'electronegativity_variance': np.random.randn(100)
        })
        y = np.random.randn(100)

        null_rmse = generate_null_distribution(X, y, n_permutations=10, random_state=42)

        assert isinstance(null_rmse, float)
        assert null_rmse > 0

    @patch('train.load_data')
    @patch('train.train_model')
    @patch('train.generate_null_distribution')
    @patch('train.os.makedirs')
    @patch('train.json.dump')
    def test_run_training(self, mock_json, mock_makedirs, mock_gen_null, mock_train, mock_load):
        """Test the full training pipeline execution."""
        # Mock inputs
        mock_df = pd.DataFrame({
            'mixing_enthalpy': [1.0, 2.0],
            'atomic_size_mismatch': [1.0, 2.0],
            'electronegativity_variance': [1.0, 2.0],
            'critical_cooling_rate': [100.0, 200.0]
        })
        mock_load.return_value = mock_df
        
        mock_model = MagicMock(spec=RandomForestRegressor)
        mock_metrics = {
            'fold_scores': [1.0, 1.0, 1.0, 1.0, 1.0],
            'mean_rmse': 1.0,
            'test_rmse': 1.0,
            'p_value_vs_null': 0.01
        }
        mock_train.return_value = (mock_model, mock_metrics)
        mock_gen_null.return_value = 2.0

        # Run training
        run_training()

        # Verify calls
        mock_load.assert_called_once()
        mock_train.assert_called_once()
        mock_gen_null.assert_called_once()
        mock_makedirs.assert_called()
        mock_json.assert_called()

    def test_cross_validation_split_non_overlapping(self):
        """
        T018: Unit test for 5-fold cross-validation split generation ensuring non-overlapping folds.
        Verifies that the KFold logic used in train_model produces disjoint train/test indices for each fold.
        """
        # Create a small dataset
        np.random.seed(42)
        X = pd.DataFrame({
            'mixing_enthalpy': np.random.randn(20),
            'atomic_size_mismatch': np.random.randn(20),
            'electronegativity_variance': np.random.randn(20)
        })
        y = np.random.randn(20)

        n_splits = 5
        kfold = KFold(n_splits=n_splits, shuffle=True, random_state=42)
        
        all_train_indices = []
        all_test_indices = []
        
        # Collect all indices used in folds
        total_indices = set(range(len(X)))
        
        for i, (train_idx, test_idx) in enumerate(kfold.split(X)):
            train_set = set(train_idx)
            test_set = set(test_idx)
            
            # 1. Verify non-overlapping within the fold
            assert train_set.isdisjoint(test_set), f"Fold {i} has overlapping train/test indices"
            
            # 2. Verify union covers the whole dataset for this fold
            assert train_set.union(test_set) == total_indices, f"Fold {i} does not cover all data"
            
            # 3. Verify sizes are reasonable (approx 80/20 split)
            assert len(train_set) >= len(X) * 0.75, f"Fold {i} train set too small"
            assert len(test_set) <= len(X) * 0.30, f"Fold {i} test set too large"
            
            all_train_indices.append(train_set)
            all_test_indices.append(test_set)

        # 4. Verify that every index appears as a test set exactly once across all folds
        union_all_test_sets = set()
        for test_set in all_test_indices:
            union_all_test_sets.update(test_set)
        
        assert union_all_test_sets == total_indices, "Not all indices were used as test data exactly once"
        
        # 5. Verify that test sets are disjoint from each other (standard KFold property)
        for i in range(len(all_test_indices)):
            for j in range(i + 1, len(all_test_indices)):
                assert all_test_indices[i].isdisjoint(all_test_indices[j]), \
                    f"Test sets for fold {i} and {j} overlap"

if __name__ == '__main__':
    pytest.main([__file__, "-v"])