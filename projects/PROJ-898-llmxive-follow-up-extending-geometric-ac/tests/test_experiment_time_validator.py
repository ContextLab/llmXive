"""
Tests for ExperimentTimeValidator (T008b)
"""
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

from experiment_time_validator import ExperimentTimeValidator, BudgetResult, CI_TIME_LIMIT_SECONDS
from config import Config, ExperimentConfig


class TestExperimentTimeValidator(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.profile_path = os.path.join(self.temp_dir, "solver_profile.csv")
        
        # Create a mock config
        self.mock_config = Config(
            topology={},
            solver={},
            experiment=ExperimentConfig(
                trial_count=10,
                steps_per_trial=50,
                seed=42,
                timeout_limits=300
            )
        )

    def tearDown(self):
        """Clean up test files."""
        if os.path.exists(self.profile_path):
            os.remove(self.profile_path)

    def test_calculate_budget_within_limit(self):
        """Test calculation when total time is within 6 hours."""
        # Create mock profile data: 100ms per step
        df = pd.DataFrame({'latency_ms': [100.0] * 10})
        df.to_csv(self.profile_path, index=False)

        validator = ExperimentTimeValidator()
        # Mock load_config to return our mock config
        with patch('experiment_time_validator.load_config', return_value=self.mock_config):
            result = validator.calculate_budget()

        # 10 trials * 50 steps * 0.1s = 50 seconds
        expected_total = 10 * 50 * 0.1
        
        self.assertAlmostEqual(result.total_estimated_time_seconds, expected_total, places=1)
        self.assertTrue(result.within_budget)
        self.assertGreater(result.time_remaining_seconds, 0)

    def test_calculate_budget_exceeds_limit(self):
        """Test calculation when total time exceeds 6 hours."""
        # Create mock profile data: 10000ms (10s) per step
        # 10 trials * 50 steps * 10s = 5000s > 21600s (6h) -> Wait, 5000s < 21600s. 
        # Let's increase trials to exceed.
        # 100 trials * 50 steps * 10s = 50000s > 21600s
        df = pd.DataFrame({'latency_ms': [10000.0] * 10})
        df.to_csv(self.profile_path, index=False)

        # Update mock config for more trials
        mock_config_large = Config(
            topology={},
            solver={},
            experiment=ExperimentConfig(
                trial_count=100,
                steps_per_trial=50,
                seed=42,
                timeout_limits=300
            )
        )

        validator = ExperimentTimeValidator()
        with patch('experiment_time_validator.load_config', return_value=mock_config_large):
            result = validator.calculate_budget()

        self.assertFalse(result.within_budget)
        self.assertLess(result.time_remaining_seconds, 0)

    def test_validate_and_abort_exits_on_failure(self):
        """Test that validate_and_abort exits with code 1 when budget exceeded."""
        # Create mock profile data that exceeds budget
        df = pd.DataFrame({'latency_ms': [10000.0] * 10})
        df.to_csv(self.profile_path, index=False)

        mock_config_large = Config(
            topology={},
            solver={},
            experiment=ExperimentConfig(
                trial_count=100,
                steps_per_trial=50,
                seed=42,
                timeout_limits=300
            )
        )

        validator = ExperimentTimeValidator()
        with patch('experiment_time_validator.load_config', return_value=mock_config_large):
            with self.assertRaises(SystemExit) as context:
                validator.validate_and_abort()
            
            self.assertEqual(context.exception.code, 1)

    def test_file_not_found_error(self):
        """Test that FileNotFoundError is raised if profile data missing."""
        validator = ExperimentTimeValidator()
        # Ensure file does not exist
        if os.path.exists(self.profile_path):
            os.remove(self.profile_path)
        
        with self.assertRaises(FileNotFoundError):
            validator.load_profile_data()

    def test_max_trials_calculation(self):
        """Test that max_trials_allowed is calculated correctly."""
        df = pd.DataFrame({'latency_ms': [1000.0] * 10}) # 1s per step
        df.to_csv(self.profile_path, index=False)

        mock_config = Config(
            topology={},
            solver={},
            experiment=ExperimentConfig(
                trial_count=1000, # High count
                steps_per_trial=10,
                seed=42,
                timeout_limits=300
            )
        )

        validator = ExperimentTimeValidator()
        with patch('experiment_time_validator.load_config', return_value=mock_config):
            result = validator.calculate_budget()

        # 1s * 10 steps * X trials <= 21600s
        # 10 * X <= 21600 => X <= 2160
        expected_max = int(CI_TIME_LIMIT_SECONDS / (1.0 * 10))
        self.assertEqual(result.max_trials_allowed, expected_max)


if __name__ == '__main__':
    unittest.main()
