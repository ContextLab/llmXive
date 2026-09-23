import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd
import sys
import os

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.evaluator import evaluate_model_on_splits, run_repeated_stratified_cv
from code.analyser import aggregate_log_variance

class TestMemoryProfiling(unittest.TestCase):
    def test_evaluate_model_on_splits_logs_memory(self):
        """Test that evaluate_model_on_splits logs memory usage."""
        # Create mock data
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        train_idx = np.arange(80)
        test_idx = np.arange(80, 100)

        with patch('code.evaluator.logger') as mock_logger:
            result = evaluate_model_on_splits(
                X=X, y=y, model_name="LogisticRegression",
                train_idx=train_idx, test_idx=test_idx, dataset_id=1
            )
            
            # Check that logger.info was called with memory usage
            calls = [str(call) for call in mock_logger.info.call_args_list]
            memory_calls = [c for c in calls if "Peak memory usage" in c]
            self.assertGreater(len(memory_calls), 0, "Memory profiling log not found.")

    def test_run_repeated_stratified_cv_logs_memory(self):
        """Test that run_repeated_stratified_cv logs memory usage."""
        X = np.random.rand(200, 5)
        y = np.random.randint(0, 2, 200)

        with patch('code.evaluator.logger') as mock_logger:
            result = run_repeated_stratified_cv(
                X=X, y=y, dataset_id=1, n_splits=2, n_repeats=1, random_state=42
            )
            
            # Check for memory log
            calls = [str(call) for call in mock_logger.info.call_args_list]
            memory_calls = [c for c in calls if "Peak memory usage" in c]
            self.assertGreater(len(memory_calls), 0, "Memory profiling log not found in CV run.")

    def test_aggregate_log_variance_logs_memory(self):
        """Test that aggregate_log_variance logs memory usage."""
        df = pd.DataFrame({
            'dataset_id': [1, 1, 2, 2],
            'model_name': ['LR', 'LR', 'LR', 'LR'],
            'accuracy': [0.9, 0.95, 0.8, 0.85]
        })

        with patch('code.analyser.logger') as mock_logger:
            result = aggregate_log_variance(df)
            
            # Check for memory log
            calls = [str(call) for call in mock_logger.info.call_args_list]
            memory_calls = [c for c in calls if "Peak memory usage" in c]
            self.assertGreater(len(memory_calls), 0, "Memory profiling log not found in aggregation.")

if __name__ == '__main__':
    unittest.main()