"""
Unit tests for the Ground-Truth Validation Gate (T017b).
"""
import os
import sys
import pytest
import logging
from unittest.mock import patch, MagicMock

# Ensure code directory is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from run_ground_truth_validation import run_validation_batch
from config import SimulationConfig

@pytest.fixture
def sample_config():
    return SimulationConfig(
        alpha=0.05,
        max_replicates=10000,
        log_epsilon=1e-15
    )

def test_validation_batch_success(sample_config):
    """
    Test that run_validation_batch returns True when all scenarios pass.
    """
    with patch('run_ground_truth_validation.generate_data') as mock_gen, \
         patch('run_ground_truth_validation.validate_sample_statistics') as mock_val:
        
        # Mock generate_data to return dummy data and params
        mock_gen.return_value = (
            {"group1": [1.0, 2.0], "group2": [1.1, 2.1]}, 
            {"mean1": 1.5, "mean2": 1.6, "var1": 0.25, "var2": 0.25}
        )
        
        # Mock validate_sample_statistics to always pass
        mock_val.return_value = (True, {"mean_diff": 0.1, "var_ratio": 1.0})

        success, results = run_validation_batch(sample_config)

        assert success is True
        assert len(results) > 0
        for r in results:
            assert r['passed'] is True

def test_validation_batch_failure(sample_config):
    """
    Test that run_validation_batch returns False when a scenario fails.
    """
    with patch('run_ground_truth_validation.generate_data') as mock_gen, \
         patch('run_ground_truth_validation.validate_sample_statistics') as mock_val:
        
        mock_gen.return_value = (
            {"group1": [1.0], "group2": [10.0]}, 
            {"mean1": 1.0, "mean2": 10.0, "var1": 0.0, "var2": 0.0}
        )
        
        # Mock validation to fail on the first call, pass on others
        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return False, {"reason": "Mean diff too large"}
            return True, {}

        mock_val.side_effect = side_effect

        success, results = run_validation_batch(sample_config)

        assert success is False
        assert any(r['passed'] is False for r in results)

def test_validation_batch_exception_handling(sample_config):
    """
    Test that exceptions during validation are caught and logged as failures.
    """
    with patch('run_ground_truth_validation.generate_data') as mock_gen:
        mock_gen.side_effect = RuntimeError("Simulated generation failure")

        success, results = run_validation_batch(sample_config)

        assert success is False
        assert any("Exception" in str(r.get('details', '')) for r in results)