"""
Unit tests for the Sensitivity Analysis Wrapper (T031).

These tests verify the wrapper logic without running the full heavy pipeline.
"""

import unittest
import os
import sys
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from analysis.sensitivity_wrapper import (
    run_sensitivity_iteration,
    run_sensitivity_analysis
)

class TestSensitivityWrapper(unittest.TestCase):

    def setUp(self):
        """Create a temporary config file for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.temp_dir.name, 'config.yaml')
        self.output_csv_path = os.path.join(self.temp_dir.name, 'results.csv')
        
        # Create a mock config
        mock_config = {
            'preprocessing': {
                'smoothing_kernel': 6.0
            },
            'analysis': {
                'roi_mask_threshold': 0.5
            }
        }
        with open(self.config_path, 'w') as f:
            yaml.dump(mock_config, f)

    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()

    @patch('analysis.sensitivity_wrapper.run_roi_extraction')
    @patch('analysis.sensitivity_wrapper.run_group_analysis')
    @patch('analysis.sensitivity_wrapper.generate_summary_statistics')
    def test_run_sensitivity_iteration_success(
        self, mock_gen_stats, mock_run_group, mock_run_roi
    ):
        """Test that a successful iteration returns correct metrics."""
        # Mock return values
        mock_run_roi.return_value = None # Assuming it writes files
        mock_run_group.return_value = None
        mock_gen_stats.return_value = [
            {'roi': 'VS', 'event': 'reward', 'mean': 1.5, 't_stat': 2.1, 'p_value': 0.04},
            {'roi': 'OFC', 'event': 'reward', 'mean': 1.2, 't_stat': 1.8, 'p_value': 0.08}
        ]

        result = run_sensitivity_iteration(
            smoothing_kernel=8.0,
            mask_threshold=0.3,
            config_path=self.config_path,
            output_dir=Path(self.temp_dir.name)
        )

        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['smoothing_kernel'], 8.0)
        self.assertEqual(result['mask_threshold'], 0.3)
        self.assertIn('VS_reward_mean', result)
        self.assertEqual(result['VS_reward_mean'], 1.5)

        # Verify config was updated and restored
        with open(self.config_path, 'r') as f:
            final_config = yaml.safe_load(f)
        self.assertEqual(final_config['preprocessing']['smoothing_kernel'], 6.0) # Original value
        self.assertEqual(final_config['analysis']['roi_mask_threshold'], 0.5) # Original value

    @patch('analysis.sensitivity_wrapper.run_roi_extraction')
    def test_run_sensitivity_iteration_failure(self, mock_run_roi):
        """Test that a failed iteration is handled gracefully."""
        mock_run_roi.side_effect = Exception("Simulated failure")

        result = run_sensitivity_iteration(
            smoothing_kernel=4.0,
            mask_threshold=0.5,
            config_path=self.config_path,
            output_dir=Path(self.temp_dir.name)
        )

        self.assertEqual(result['status'], 'failed')
        self.assertIn('error', result)
        self.assertEqual(result['smoothing_kernel'], 4.0)

    @patch('analysis.sensitivity_wrapper.run_sensitivity_iteration')
    def test_run_sensitivity_analysis_loop(self, mock_iter):
        """Test that the main loop iterates over all combinations."""
        mock_iter.return_value = {'status': 'success', 'smoothing_kernel': 4.0, 'mask_threshold': 0.3}

        kernels = [4.0, 6.0]
        thresholds = [0.3, 0.5]

        results = run_sensitivity_analysis(
            smoothing_kernels=kernels,
            mask_thresholds=thresholds,
            config_path=self.config_path,
            output_csv_path=self.output_csv_path
        )

        # Should be 2 * 2 = 4 iterations
        self.assertEqual(len(results), 4)
        
        # Verify CSV was created
        self.assertTrue(os.path.exists(self.output_csv_path))

        # Verify iteration calls
        self.assertEqual(mock_iter.call_count, 4)

if __name__ == '__main__':
    unittest.main()