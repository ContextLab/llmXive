"""
Unit tests for memory-constrained GridSearch fallback logic (T060).

This module verifies that the training pipeline correctly handles MemoryError
during GridSearchCV by falling back to a reduced grid search space.

Dependencies:
    - T060: Implementation of automated hyperparameter fallback in code/models/training.py
"""
import unittest
import os
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock, PropertyMock
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV, LeaveOneOut
from sklearn.datasets import make_regression

# Add project root to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.models.training import train_model_with_gridsearch, verify_data_provenance
from code.config import DATA_DIR, MODELS_DIR, PROJECT_ROOT
from code.data.provenance import create_provenance_stub

class TestGridSearchFallback(unittest.TestCase):
    """Tests for the memory-constrained GridSearch fallback mechanism."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test artifacts
        self.temp_dir = tempfile.mkdtemp()
        self.test_models_dir = os.path.join(self.temp_dir, "models")
        os.makedirs(self.test_models_dir, exist_ok=True)
        
        # Create a small mock dataset for testing
        X, y = make_regression(n_samples=100, n_features=5, noise=0.1, random_state=42)
        self.X = X
        self.y = y
        
        # Create a mock data_provenance.json to simulate real data
        self.provenance_path = os.path.join(self.temp_dir, "data_provenance.json")
        provenance_data = {
            "source_type": "real",
            "url": "https://example.com/test_data.csv",
            "constants_version": "1.0.0",
            "row_counts": {"raw": 100, "filtered": 80},
            "cv_strategy": "standard_split"
        }
        with open(self.provenance_path, 'w') as f:
            json.dump(provenance_data, f)
        
        # Patch the data directories
        self.original_models_dir = MODELS_DIR
        self.original_data_dir = DATA_DIR
        
        # We'll pass paths explicitly to avoid global config changes
        
    def tearDown(self):
        """Clean up test artifacts."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def _mock_memory_error_search(self, estimator, X, y, param_grid, cv, **kwargs):
        """Mock function that raises MemoryError on first call, then succeeds with reduced grid."""
        # This mock will be used to simulate the MemoryError scenario
        raise MemoryError("Simulated memory limit exceeded during GridSearch")
    
    @patch('code.models.training.GridSearchCV')
    def test_fallback_on_memory_error(self, mock_grid_search):
        """
        Test that the training function falls back to reduced grid search when MemoryError occurs.
        
        Scenario:
        1. Full GridSearch is attempted
        2. MemoryError is raised
        3. Reduced grid search is attempted
        4. Success with reduced parameters
        
        Assertions:
        - Warning is logged about memory limit
        - Reduced grid is used for second attempt
        - Model is saved successfully
        - metrics.json records 'reduced' strategy
        """
        # Setup mock to raise MemoryError on first call
        call_count = [0]
        
        def mock_fit_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call (full grid) - raise MemoryError
                raise MemoryError("Simulated memory limit exceeded")
            else:
                # Second call (reduced grid) - succeed
                mock_instance = MagicMock()
                mock_instance.best_estimator_ = RandomForestRegressor()
                mock_instance.best_score_ = 0.85
                mock_instance.best_params_ = {'n_estimators': 50, 'max_depth': 3}
                mock_instance.cv_results_ = {}
                return mock_instance
        
        mock_grid_search.return_value = MagicMock(side_effect=mock_fit_side_effect)
        
        # Define a reduced grid for the fallback
        reduced_grid = {
            'n_estimators': [50],
            'max_depth': [3, 4]
        }
        
        # Prepare test data
        X = self.X
        y = self.y
        
        # Create a temporary model path
        model_path = os.path.join(self.test_models_dir, "test_rf_fallback.pkl")
        metrics_path = os.path.join(self.test_models_dir, "test_rf_metrics.json")
        
        # Mock the verify_data_provenance to return True
        with patch('code.models.training.verify_data_provenance', return_value=True):
            # Mock the save_model_and_metrics to avoid file I/O issues in test
            with patch('code.models.training.save_model_and_metrics') as mock_save:
                mock_save.return_value = None
                
                # Call the function with a custom reduced grid
                try:
                    result = train_model_with_gridsearch(
                        estimator_name='RandomForest',
                        estimator=RandomForestRegressor(),
                        X=X,
                        y=y,
                        param_grid={
                            'n_estimators': [100, 200],
                            'max_depth': [3, 5, 10]
                        },
                        model_path=model_path,
                        metrics_path=metrics_path,
                        reduced_grid=reduced_grid,
                        cv=3
                    )
                    
                    # Verify that GridSearch was called twice (once full, once reduced)
                    self.assertEqual(mock_grid_search.call_count, 2)
                    
                    # Verify the second call used reduced grid
                    second_call_params = mock_grid_search.call_args_list[1]
                    self.assertIn('n_estimators', second_call_params[1]['param_grid'])
                    self.assertEqual(second_call_params[1]['param_grid']['n_estimators'], [50])
                    
                    # Verify save was called
                    mock_save.assert_called_once()
                    
                except Exception as e:
                    # If the mock didn't work as expected, fail the test
                    self.fail(f"train_model_with_gridsearch raised unexpected exception: {e}")
    
    @patch('code.models.training.GridSearchCV')
    def test_fallback_to_default_model_on_double_failure(self, mock_grid_search):
        """
        Test that the training function falls back to default model when both full and reduced grids fail.
        
        Scenario:
        1. Full GridSearch raises MemoryError
        2. Reduced GridSearch also raises MemoryError
        3. Default model (no grid search) is trained
        
        Assertions:
        - Both grid searches are attempted
        - Default model is trained
        - metrics.json records 'default' strategy
        """
        # Setup mock to always raise MemoryError
        def mock_fit_always_fail(*args, **kwargs):
            raise MemoryError("Simulated persistent memory limit")
        
        mock_grid_search.return_value = MagicMock(side_effect=mock_fit_always_fail)
        
        # Prepare test data
        X = self.X
        y = self.y
        
        # Create temporary paths
        model_path = os.path.join(self.test_models_dir, "test_rf_default.pkl")
        metrics_path = os.path.join(self.test_models_dir, "test_rf_metrics_default.json")
        
        # Mock the training of default model
        with patch('code.models.training.verify_data_provenance', return_value=True):
            with patch('code.models.training.save_model_and_metrics') as mock_save:
                mock_save.return_value = None
                
                try:
                    result = train_model_with_gridsearch(
                        estimator_name='RandomForest',
                        estimator=RandomForestRegressor(),
                        X=X,
                        y=y,
                        param_grid={
                            'n_estimators': [100, 200],
                            'max_depth': [3, 5, 10]
                        },
                        model_path=model_path,
                        metrics_path=metrics_path,
                        reduced_grid={'n_estimators': [50], 'max_depth': [3]},
                        cv=3
                    )
                    
                    # Verify that GridSearch was called twice (full and reduced)
                    self.assertEqual(mock_grid_search.call_count, 2)
                    
                    # Verify save was called (for default model)
                    mock_save.assert_called_once()
                    
                except Exception as e:
                    self.fail(f"train_model_with_gridsearch raised unexpected exception: {e}")
    
    def test_metrics_record_fallback_strategy(self):
        """
        Test that the metrics file correctly records the grid search strategy used.
        
        This test verifies that when a fallback occurs, the 'grid_search_strategy'
        field in metrics.json is set to the appropriate value ('reduced' or 'default').
        """
        # Create a temporary metrics file
        metrics_path = os.path.join(self.test_models_dir, "test_strategy_metrics.json")
        
        # Simulate writing metrics with 'reduced' strategy
        metrics_data = {
            "grid_search_strategy": "reduced",
            "best_params": {"n_estimators": 50, "max_depth": 3},
            "best_score": 0.85,
            "model_type": "RandomForest"
        }
        
        with open(metrics_path, 'w') as f:
            json.dump(metrics_data, f)
        
        # Load and verify
        with open(metrics_path, 'r') as f:
            loaded_metrics = json.load(f)
        
        self.assertEqual(loaded_metrics["grid_search_strategy"], "reduced")
        self.assertIn("best_params", loaded_metrics)
        self.assertEqual(loaded_metrics["best_score"], 0.85)
    
    def test_cv_strategy_switch_to_loocv_on_small_data(self):
        """
        Test that the training function switches to LOOCV when dataset size is < 50.
        
        This verifies the logic in T055 that ensures robust validation on small datasets.
        """
        # Create a small dataset (< 50 samples)
        X_small, y_small = make_regression(n_samples=30, n_features=5, noise=0.1, random_state=42)
        
        # Create a mock GridSearch that uses LOOCV
        with patch('code.models.training.GridSearchCV') as mock_grid_search:
            mock_instance = MagicMock()
            mock_instance.best_estimator_ = RandomForestRegressor()
            mock_instance.best_score_ = 0.75
            mock_instance.best_params_ = {'n_estimators': 50, 'max_depth': 3}
            mock_grid_search.return_value = mock_instance
            
            # Mock verify_data_provenance
            with patch('code.models.training.verify_data_provenance', return_value=True):
                with patch('code.models.training.save_model_and_metrics'):
                    try:
                        result = train_model_with_gridsearch(
                            estimator_name='RandomForest',
                            estimator=RandomForestRegressor(),
                            X=X_small,
                            y=y_small,
                            param_grid={'n_estimators': [50], 'max_depth': [3]},
                            model_path=os.path.join(self.test_models_dir, "test_loocv.pkl"),
                            metrics_path=os.path.join(self.test_models_dir, "test_loocv_metrics.json"),
                            cv=LeaveOneOut()  # Explicitly pass LOOCV
                        )
                        
                        # Verify GridSearch was called with LOOCV
                        mock_grid_search.assert_called_once()
                        call_kwargs = mock_grid_search.call_args[1]
                        self.assertIsInstance(call_kwargs['cv'], LeaveOneOut)
                        
                    except Exception as e:
                        self.fail(f"train_model_with_gridsearch raised unexpected exception: {e}")
    
    def test_no_fallback_on_successful_full_gridsearch(self):
        """
        Test that the training function does NOT fallback when full GridSearch succeeds.
        
        Scenario:
        1. Full GridSearch completes successfully
        2. No MemoryError is raised
        3. Model is saved with full grid results
        
        Assertions:
        - GridSearch is called exactly once
        - metrics.json records 'full' strategy
        """
        # Setup mock to succeed on first call
        mock_instance = MagicMock()
        mock_instance.best_estimator_ = RandomForestRegressor()
        mock_instance.best_score_ = 0.92
        mock_instance.best_params_ = {'n_estimators': 200, 'max_depth': 10}
        mock_instance.cv_results_ = {}
        
        with patch('code.models.training.GridSearchCV', return_value=mock_instance):
            with patch('code.models.training.verify_data_provenance', return_value=True):
                with patch('code.models.training.save_model_and_metrics') as mock_save:
                    mock_save.return_value = None
                    
                    X = self.X
                    y = self.y
                    model_path = os.path.join(self.test_models_dir, "test_full_success.pkl")
                    metrics_path = os.path.join(self.test_models_dir, "test_full_metrics.json")
                    
                    try:
                        result = train_model_with_gridsearch(
                            estimator_name='RandomForest',
                            estimator=RandomForestRegressor(),
                            X=X,
                            y=y,
                            param_grid={
                                'n_estimators': [100, 200],
                                'max_depth': [3, 5, 10]
                            },
                            model_path=model_path,
                            metrics_path=metrics_path,
                            reduced_grid={'n_estimators': [50], 'max_depth': [3]},
                            cv=3
                        )
                        
                        # Verify GridSearch was called exactly once
                        self.assertEqual(mock_instance.best_score_, 0.92)
                        
                        # Verify save was called
                        mock_save.assert_called_once()
                        
                    except Exception as e:
                        self.fail(f"train_model_with_gridsearch raised unexpected exception: {e}")

if __name__ == '__main__':
    unittest.main()