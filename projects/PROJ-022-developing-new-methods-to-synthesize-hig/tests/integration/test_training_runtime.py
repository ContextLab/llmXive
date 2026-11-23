"""
Integration test for model training runtime fallback (T018).

This test verifies that the training module correctly handles runtime constraints
by reducing model complexity (max_depth) when the training process exceeds the
expected duration, as specified in FR-003 and the complexity tracking plan.

It mocks the heavy computation (descriptor calculation and model fitting) to
simulate a timeout condition without actually waiting for hours, ensuring the
fallback logic (max_depth 10 -> 6 -> 4) is triggered and the model is saved
successfully with the reduced parameters.
"""

import os
import sys
import time
import unittest
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import timedelta
import tempfile
import shutil

# Add project root to path to allow imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pandas as pd
import numpy as np

# Import the module under test
# Note: We assume the training module is at code/modeling/train_model.py
# and follows the API surface provided in the prompt context or standard project structure.
# Since the prompt API surface didn't explicitly list train_model.py, we import it
# dynamically or assume standard location based on tasks.md.
# Based on tasks.md: T021 implements code/modeling/train_model.py
try:
    from modeling.train_model import train_model, get_training_budget_seconds
except ImportError:
    # Fallback if the module isn't built yet, but the test should still define the logic
    # However, per instructions, we must implement the test against the real code.
    # We will assume the code exists as per T021 being the implementation task.
    # If T021 is not done, this test would fail to import, which is expected behavior
    # in a real CI/CD pipeline if dependencies aren't met.
    # For this task, we mock the import to ensure the test logic itself is valid.
    raise ImportError(
        "Cannot import modeling.train_model. Ensure T021 (train_model.py) is implemented "
        "or the module exists in code/modeling/."
    )


class TestTrainingRuntimeFallback(unittest.TestCase):
    """Test suite for runtime fallback logic in model training."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_model_path = os.path.join(self.temp_dir, "test_model.pkl")
        self.output_metrics_path = os.path.join(self.temp_dir, "test_metrics.json")
        
        # Create a dummy standardized dataset
        # Based on T016 output: data/processed/standardized_polymers.csv
        self.dummy_data = pd.DataFrame({
            'smiles': ['CCO', 'CC(=O)O', 'c1ccccc1', 'CC(C)(C)C'],
            'permeability_barrer': [10.0, 20.0, 30.0, 40.0],
            'selectivity': [2.0, 3.0, 4.0, 5.0],
            'polymer_class': ['alcohol', 'acid', 'aromatic', 'alkane']
        })

    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch('modeling.train_model.calculate_descriptors')
    @patch('modeling.train_model.RandomForestRegressor')
    def test_runtime_fallback_triggers(self, mock_rf_class, mock_calc_desc):
        """
        Test that if training takes too long, the model parameters are reduced.
        
        This simulates the scenario where the initial training attempt (max_depth=10)
        would exceed the time budget, forcing a fallback to max_depth=6, then 4.
        """
        # Setup mock for descriptor calculation to return dummy features
        mock_df = pd.DataFrame({
            'vdw_volume': [10, 20, 30, 40],
            'h_bond_count': [1, 2, 3, 4],
            'molecular_weight': [46, 60, 78, 58]
        })
        mock_calc_desc.return_value = mock_df

        # Setup mock for RandomForestRegressor
        mock_instance = MagicMock()
        mock_instance.fit = MagicMock()
        mock_instance.score = MagicMock(return_value=0.5)
        mock_instance.feature_importances_ = np.array([0.1, 0.2, 0.3])
        mock_rf_class.return_value = mock_instance

        # Mock time.sleep to simulate long-running process
        # We want the first attempt to "take too long"
        call_count = 0
        def slow_fit(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call: simulate exceeding budget
                # In real code, this would be detected by checking time elapsed
                # Here we rely on the logic in train_model to handle the timeout
                # We will mock the time check to force a retry
                pass
            # Just return quickly in mock
            return None

        mock_instance.fit.side_effect = slow_fit

        # Mock the time check logic to force fallback
        # We patch the internal logic that checks elapsed time
        with patch('modeling.train_model.time.time') as mock_time:
            start_time = 1000.0
            # Simulate time passing such that the first attempt fails the budget
            mock_time.side_effect = [start_time, start_time + 70, start_time + 10] 
            # 70 seconds > 60s budget -> fallback
            
            # We also need to mock the budget check or the function that raises the timeout
            # Since we can't easily mock the internal time check without seeing the code,
            # we will assume the function `train_model` has logic to catch a timeout or check time.
            # A better approach for an integration test of fallback logic is to mock the
            # 'fit' method to raise a custom TimeoutError if it simulates taking too long.
            
            # Let's re-approach: Mock the fit method to raise a custom exception
            # that the training loop catches to trigger fallback.
            
            # Actually, the prompt says: "if runtime > 60m, reduce max_depth".
            # This implies the code measures runtime.
            # We will mock the time module to make the first iteration look like it took > 60s.
            
            # Reset mocks
            mock_rf_class.reset_mock()
            call_count = 0

            # We need to ensure the function under test actually checks time.
            # Since we don't have the source of train_model.py yet (T021),
            # we assume it implements the logic:
            # try: fit(); if time > budget: reduce depth; else: break
            
            # To test this robustly, we will mock the `time.time` calls to force the condition.
            # We need to know how many times time.time is called.
            # Let's assume it's called at start and end of fit.
            
            # Simulate:
            # Iteration 1 (depth=10): start=0, end=70 (70s > 60s limit) -> Fallback
            # Iteration 2 (depth=6): start=70, end=71 (1s < 60s) -> Success
            
            time_sequence = [0.0, 70.0, 70.0, 71.0]
            mock_time.side_effect = time_sequence

            try:
                result = train_model(
                    data=self.dummy_data,
                    target_col='permeability_barrer',
                    output_model_path=self.output_model_path,
                    output_metrics_path=self.output_metrics_path,
                    budget_seconds=60  # 60 second budget
                )
            except Exception as e:
                # If the code doesn't handle the timeout gracefully, the test fails.
                # But the task is to test the fallback, so the code MUST handle it.
                self.fail(f"Training failed without fallback: {e}")

            # Verify that RandomForest was called multiple times (fallback occurred)
            # Expected: Called for depth=10 (failed), then depth=6 (success)
            self.assertGreaterEqual(
                mock_rf_class.call_count, 2,
                "Expected at least 2 training attempts (fallback triggered)"
            )

            # Verify the last call used a reduced max_depth
            last_call_kwargs = mock_rf_class.call_args_list[-1][1]
            self.assertLess(
                last_call_kwargs['max_depth'], 10,
                "Expected max_depth to be reduced from default 10 due to timeout"
            )

            # Verify the model file was created
            self.assertTrue(
                os.path.exists(self.output_model_path),
                "Model file should be saved after fallback"
            )

            # Verify metrics file was created
            self.assertTrue(
                os.path.exists(self.output_metrics_path),
                "Metrics file should be saved after fallback"
            )

    @patch('modeling.train_model.calculate_descriptors')
    @patch('modeling.train_model.RandomForestRegressor')
    def test_no_fallback_when_fast(self, mock_rf_class, mock_calc_desc):
        """
        Test that if training is fast, no fallback occurs.
        """
        # Setup mocks
        mock_df = pd.DataFrame({
            'vdw_volume': [10, 20],
            'h_bond_count': [1, 2],
            'molecular_weight': [46, 60]
        })
        mock_calc_desc.return_value = mock_df

        mock_instance = MagicMock()
        mock_instance.fit = MagicMock()
        mock_instance.score = MagicMock(return_value=0.8)
        mock_instance.feature_importances_ = np.array([0.5, 0.5])
        mock_rf_class.return_value = mock_instance

        # Mock time to simulate fast execution
        with patch('modeling.train_model.time.time') as mock_time:
            mock_time.side_effect = [0.0, 1.0] # 1 second elapsed

            result = train_model(
                data=self.dummy_data,
                target_col='permeability_barrer',
                output_model_path=self.output_model_path,
                output_metrics_path=self.output_metrics_path,
                budget_seconds=60
            )

            # Verify only one call
            self.assertEqual(
                mock_rf_class.call_count, 1,
                "Expected exactly 1 training attempt (no fallback)"
            )

            # Verify default max_depth (10) was used
            call_kwargs = mock_rf_class.call_args[1]
            self.assertEqual(
                call_kwargs['max_depth'], 10,
                "Expected default max_depth=10 when no timeout occurs"
            )


if __name__ == '__main__':
    unittest.main()