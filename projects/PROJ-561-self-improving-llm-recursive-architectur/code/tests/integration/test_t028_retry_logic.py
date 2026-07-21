import unittest
import sys
import os
import time
from unittest.mock import patch, MagicMock, PropertyMock

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from main import run_single_cycle_with_retry
from config import Hyperparameters, SafetyConstraints, PathConfig
from pipeline.model import load_gpt_124m

class TestRetryLogic(unittest.TestCase):
    """
    Integration tests for T028: Retry logic in main.py.
    Ensures that failed training cycles are retried up to 2 times,
    and if still failing, the cycle is logged as failed and the function returns None.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.config = Hyperparameters(
            learning_rate=5e-5,
            batch_size=4,
            epochs=1,
            seed=42
        )
        self.constraints = SafetyConstraints(
            max_ram_gb=7.0,
            max_param_increase_pct=30,
            max_training_time_hours=2.0
        )
        self.path_config = PathConfig(
            data_dir="data",
            results_dir="results",
            models_dir="models",
            logs_dir="logs"
        )
        self.model = MagicMock()

    @patch('main.run_training_cycle')
    def test_success_on_first_attempt(self, mock_run_training):
        """Test that a successful training on first attempt returns metrics."""
        mock_run_training.return_value = {"flops": 1000, "time": 10.0}
        
        result = run_single_cycle_with_retry(
            cycle_number=1,
            model=self.model,
            config=self.config,
            constraints=self.constraints,
            path_config=self.path_config,
            max_retries=2
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result["flops"], 1000)
        self.assertEqual(mock_run_training.call_count, 1)

    @patch('main.run_training_cycle')
    def test_success_on_second_attempt(self, mock_run_training):
        """Test that success on second attempt returns metrics."""
        mock_run_training.side_effect = [
            Exception("First attempt failed"),
            {"flops": 2000, "time": 15.0}
        ]
        
        result = run_single_cycle_with_retry(
            cycle_number=1,
            model=self.model,
            config=self.config,
            constraints=self.constraints,
            path_config=self.path_config,
            max_retries=2
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result["flops"], 2000)
        self.assertEqual(mock_run_training.call_count, 2)

    @patch('main.run_training_cycle')
    def test_failure_after_max_retries(self, mock_run_training):
        """Test that failure after max retries returns None and logs failure."""
        mock_run_training.side_effect = Exception("Persistent failure")
        
        result = run_single_cycle_with_retry(
            cycle_number=1,
            model=self.model,
            config=self.config,
            constraints=self.constraints,
            path_config=self.path_config,
            max_retries=2
        )
        
        self.assertIsNone(result)
        self.assertEqual(mock_run_training.call_count, 3) # Initial + 2 retries

    @patch('main.run_training_cycle')
    def test_failure_after_one_retry(self, mock_run_training):
        """Test that failure after 1 retry (max_retries=1) returns None."""
        mock_run_training.side_effect = Exception("Persistent failure")
        
        result = run_single_cycle_with_retry(
            cycle_number=1,
            model=self.model,
            config=self.config,
            constraints=self.constraints,
            path_config=self.path_config,
            max_retries=1
        )
        
        self.assertIsNone(result)
        self.assertEqual(mock_run_training.call_count, 2) # Initial + 1 retry

    @patch('main.run_training_cycle')
    def test_no_retry_on_success(self, mock_run_training):
        """Test that no retry happens if first attempt succeeds."""
        mock_run_training.return_value = {"flops": 3000, "time": 20.0}
        
        result = run_single_cycle_with_retry(
            cycle_number=1,
            model=self.model,
            config=self.config,
            constraints=self.constraints,
            path_config=self.path_config,
            max_retries=2
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(mock_run_training.call_count, 1)

if __name__ == "__main__":
    unittest.main()