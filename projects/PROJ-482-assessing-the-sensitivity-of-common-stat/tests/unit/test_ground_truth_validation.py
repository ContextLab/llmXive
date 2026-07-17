import pytest
import numpy as np
import logging
from unittest.mock import patch, MagicMock

from config import SimulationConfig
from run_ground_truth_validation import run_validation_batch
from data_generator import generate_data, validate_sample_statistics

# Suppress logging during tests
logging.disable(logging.CRITICAL)

class TestGroundTruthValidationGate:
    """
    Unit tests for the Ground-Truth Validation Gate (T017b).
    These tests verify that the validation routine correctly identifies
    passing and failing scenarios.
    """

    def test_validation_batch_all_pass(self):
        """Test that a batch of valid scenarios returns True."""
        config = SimulationConfig()
        
        # Mock generate_data to return deterministic data that will pass validation
        with patch('run_ground_truth_validation.generate_data') as mock_gen, \
             patch('run_ground_truth_validation.validate_sample_statistics') as mock_val:
            
            # Setup mocks to simulate successful generation and validation
            mock_gen.return_value = (np.random.normal(0, 1, 20), np.random.normal(0, 1, 20))
            mock_val.return_value = {
                "passed": True,
                "details": {"mean_diff": 0.0, "variance": 1.0},
                "reason": None
            }
            
            result = run_validation_batch(config)
            assert result is True

    def test_validation_batch_with_failure(self):
        """Test that a batch with a failing scenario returns False."""
        config = SimulationConfig()
        
        with patch('run_ground_truth_validation.generate_data') as mock_gen, \
             patch('run_ground_truth_validation.validate_sample_statistics') as mock_val:
            
            # First call passes, second fails
            mock_gen.return_value = (np.random.normal(0, 1, 20), np.random.normal(0, 1, 20))
            
            # Simulate a failure on the second scenario
            call_count = [0]
            def mock_val_side_effect(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 2:
                    return {
                        "passed": False,
                        "details": {},
                        "reason": "Mean difference exceeds tolerance"
                    }
                return {
                    "passed": True,
                    "details": {"mean_diff": 0.0, "variance": 1.0},
                    "reason": None
                }
            
            mock_val.side_effect = mock_val_side_effect
            
            result = run_validation_batch(config)
            assert result is False

    def test_validation_batch_exception_handling(self):
        """Test that exceptions during validation are caught and result in failure."""
        config = SimulationConfig()
        
        with patch('run_ground_truth_validation.generate_data') as mock_gen, \
             patch('run_ground_truth_validation.validate_sample_statistics') as mock_val:
            
            mock_gen.return_value = (np.random.normal(0, 1, 20), np.random.normal(0, 1, 20))
            mock_val.side_effect = RuntimeError("Numerical overflow in validation")
            
            result = run_validation_batch(config)
            assert result is False

    def test_logging_confirmation(self):
        """Test that a log entry confirming verification is produced."""
        config = SimulationConfig()
        
        with patch('run_ground_truth_validation.generate_data') as mock_gen, \
             patch('run_ground_truth_validation.validate_sample_statistics') as mock_val, \
             patch('run_ground_truth_validation.logger') as mock_logger:
            
            mock_gen.return_value = (np.random.normal(0, 1, 20), np.random.normal(0, 1, 20))
            mock_val.return_value = {
                "passed": True,
                "details": {"mean_diff": 0.0, "variance": 1.0},
                "reason": None
            }
            
            run_validation_batch(config)
            
            # Verify that the success message was logged
            success_logs = [
                call for call in mock_logger.info.call_args_list 
                if "PASSED" in str(call)
            ]
            assert len(success_logs) > 0, "Expected a log entry confirming validation passed"

    def test_config_parameters_used(self):
        """Test that the validation uses the correct configuration parameters."""
        config = SimulationConfig(alpha=0.01, max_replicates=5000)
        
        with patch('run_ground_truth_validation.generate_data') as mock_gen, \
             patch('run_ground_truth_validation.validate_sample_statistics') as mock_val:
            
            mock_gen.return_value = (np.random.normal(0, 1, 20), np.random.normal(0, 1, 20))
            mock_val.return_value = {
                "passed": True,
                "details": {},
                "reason": None
            }
            
            run_validation_batch(config)
            
            # Verify validate_sample_statistics was called with the correct alpha
            # We check the last call arguments
            last_call = mock_val.call_args_list[-1]
            # The alpha parameter should be passed as the last argument
            assert last_call[0][4] == 0.01, "Validation should use config.alpha"