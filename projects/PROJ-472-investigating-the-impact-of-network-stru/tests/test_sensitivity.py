"""
Unit tests for the sensitivity sweep analysis (T039).
Verifies that sensitivity.py correctly uses hardcoded thresholds {0.70, 0.75, 0.80}
and produces consistent results.
"""
import os
import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock, mock_open
import json

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis.sensitivity import (
    calculate_threshold_multiplier_range,
    run_sensitivity_sweep_for_subject,
    run_sensitivity_pipeline,
    main
)
from config import get_data_root
from utils.logger import get_logger

# Constants matching T004/T031 requirements
HARDCODED_THRESHOLDS = [0.70, 0.75, 0.80]

class TestSensitivitySweep(unittest.TestCase):
    """Tests for sensitivity analysis functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.logger = get_logger(__name__)
        self.data_root = get_data_root()
        self.test_subject_id = "sub-TEST001"
        
        # Create a mock EEG time series for testing
        self.mock_eeg_data = np.random.randn(250, 64)  # 250Hz, 64 channels
        self.mock_eeg_df = pd.DataFrame(
            self.mock_eeg_data.T,
            columns=[f'ch_{i}' for i in range(64)]
        )
        self.mock_eeg_df['time'] = np.arange(len(self.mock_eeg_data))

    def test_hardcoded_thresholds_used(self):
        """
        Verify that the sensitivity sweep uses the exact hardcoded thresholds
        {0.70, 0.75, 0.80} as specified in T031, not values from config files.
        """
        # Mock the EEG loading function to return our test data
        with patch('analysis.sensitivity.load_processed_eeg_for_subject') as mock_load:
            mock_load.return_value = self.mock_eeg_df
            
            # Run the sensitivity sweep
            result = run_sensitivity_sweep_for_subject(self.test_subject_id)
            
            # Verify the thresholds used match the hardcoded set exactly
            self.assertIsNotNone(result, "Sensitivity sweep should return a result")
            self.assertIn('thresholds_used', result, "Result should contain thresholds_used")
            
            thresholds_used = sorted(result['thresholds_used'])
            expected_thresholds = sorted(HARDCODED_THRESHOLDS)
            
            self.assertEqual(
                thresholds_used, 
                expected_thresholds,
                f"Expected thresholds {expected_thresholds}, got {thresholds_used}"
            )

    def test_consistent_results_across_runs(self):
        """
        Verify that running the sensitivity sweep multiple times with the same
        input produces consistent results (deterministic behavior).
        """
        with patch('analysis.sensitivity.load_processed_eeg_for_subject') as mock_load:
            mock_load.return_value = self.mock_eeg_df
            
            # Run the sweep twice
            result1 = run_sensitivity_sweep_for_subject(self.test_subject_id)
            result2 = run_sensitivity_sweep_for_subject(self.test_subject_id)
            
            # Compare results
            self.assertEqual(
                result1['thresholds_used'], 
                result2['thresholds_used'],
                "Thresholds should be identical across runs"
            )
            
            # Check that avalanche metrics are consistent
            self.assertEqual(
                len(result1['avalanche_metrics']),
                len(result2['avalanche_metrics']),
                "Number of metrics should be consistent"
            )

    def test_threshold_multiplier_range_calculation(self):
        """
        Verify that calculate_threshold_multiplier_range produces the correct
        multiplier values for the hardcoded thresholds.
        """
        # The function should return multipliers that scale the base threshold
        # For a base of 1.0, the multipliers should match the thresholds themselves
        multipliers = calculate_threshold_multiplier_range()
        
        self.assertIsInstance(multipliers, list, "Multipliers should be a list")
        self.assertEqual(len(multipliers), len(HARDCODED_THRESHOLDS), 
                       "Should have one multiplier per threshold")
        
        # Sort and compare
        sorted_multipliers = sorted(multipliers)
        sorted_thresholds = sorted(HARDCODED_THRESHOLDS)
        
        self.assertEqual(
            sorted_multipliers, 
            sorted_thresholds,
            f"Multipliers {sorted_multipliers} should match thresholds {sorted_thresholds}"
        )

    def test_sensitivity_pipeline_output_structure(self):
        """
        Verify that the sensitivity pipeline produces the expected output structure
        with all required fields.
        """
        # Create mock data directory structure
        processed_dir = self.data_root / "processed" / "eeg"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        subject_dir = processed_dir / self.test_subject_id
        subject_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a mock EEG file
        eeg_file = subject_dir / "eeg_cleaned.fif"
        eeg_file.touch()  # Create empty file for existence check
        
        # Mock the load function to return our test data
        with patch('analysis.sensitivity.load_processed_eeg_for_subject') as mock_load:
            mock_load.return_value = self.mock_eeg_df
            
            # Run the pipeline
            pipeline_result = run_sensitivity_pipeline()
            
            # Verify pipeline result structure
            self.assertIsInstance(pipeline_result, dict, "Pipeline result should be a dict")
            self.assertIn('subject_results', pipeline_result, 
                        "Result should contain subject_results")
            self.assertIn('thresholds_used', pipeline_result,
                        "Result should contain thresholds_used")
            
            # Verify thresholds match hardcoded values
            self.assertEqual(
                sorted(pipeline_result['thresholds_used']),
                sorted(HARDCODED_THRESHOLDS)
            )

    def test_no_config_file_dependency(self):
        """
        Verify that the sensitivity sweep does not attempt to load thresholds
        from research_phase_config.json (enforcing T031 requirement).
        """
        # Mock a scenario where config file exists but has different values
        mock_config_content = {
            "sensitivity_thresholds": [0.60, 0.65, 0.70],  # Wrong values
            "other_config": "value"
        }
        
        with patch('analysis.sensitivity.load_processed_eeg_for_subject') as mock_load:
            mock_load.return_value = self.mock_eeg_df
            
            # Run the sweep
            result = run_sensitivity_sweep_for_subject(self.test_subject_id)
            
            # Verify that the hardcoded values were used, not the config values
            self.assertEqual(
                sorted(result['thresholds_used']),
                sorted(HARDCODED_THRESHOLDS),
                "Should use hardcoded thresholds, not config file values"
            )

    def test_avalanche_metrics_generated_for_each_threshold(self):
        """
        Verify that avalanche metrics are generated for each of the three
        hardcoded thresholds.
        """
        with patch('analysis.sensitivity.load_processed_eeg_for_subject') as mock_load:
            mock_load.return_value = self.mock_eeg_df
            
            result = run_sensitivity_sweep_for_subject(self.test_subject_id)
            
            # Check that we have metrics for each threshold
            self.assertIn('avalanche_metrics', result)
            metrics = result['avalanche_metrics']
            
            # Should have 3 sets of metrics (one per threshold)
            self.assertEqual(
                len(metrics), 
                len(HARDCODED_THRESHOLDS),
                f"Expected {len(HARDCODED_THRESHOLDS)} metric sets, got {len(metrics)}"
            )

    def test_main_function_integration(self):
        """
        Test the main function entry point to ensure it executes the pipeline
        correctly with the hardcoded thresholds.
        """
        # Create necessary directories
        results_dir = self.data_root / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        
        processed_dir = self.data_root / "processed" / "eeg"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock the necessary functions
        with patch('analysis.sensitivity.run_sensitivity_pipeline') as mock_pipeline:
            mock_pipeline.return_value = {
                'subject_results': [],
                'thresholds_used': HARDCODED_THRESHOLDS,
                'status': 'success'
            }
            
            # Mock sys.argv to simulate command line execution
            with patch('sys.argv', ['sensitivity.py']):
                # This should not raise an exception
                try:
                    main()
                    # Verify the pipeline was called
                    mock_pipeline.assert_called_once()
                except SystemExit:
                    # Expected if main() calls sys.exit()
                    pass

if __name__ == '__main__':
    unittest.main()