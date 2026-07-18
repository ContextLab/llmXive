"""
Unit tests for the Ground-Truth Validation Gate (Task T017b).
"""
import pytest
import sys
import os
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SimulationConfig
from data_generator import generate_data, validate_sample_statistics
from run_ground_truth_validation import run_validation_batch

class TestGroundTruthValidationGate:
    """Tests for the validation gate logic."""

    def test_validate_normal_data_passes(self):
        """Test that normal data with correct parameters passes validation."""
        n = 100
        effect = 0.5
        seed = 42
        
        data = generate_data(n=n, distribution='normal', effect_size=effect, seed=seed)
        
        result = validate_sample_statistics(
            group1=data['group1'],
            group2=data['group2'],
            expected_effect=effect,
            distribution='normal'
        )
        
        assert result['passed'], f"Validation failed: {result['reason']}"

    def test_validate_log_normal_data_passes(self):
        """Test that log-normal data passes validation (skewness check)."""
        n = 200
        effect = 0.0
        seed = 123
        
        data = generate_data(n=n, distribution='log-normal', effect_size=effect, seed=seed)
        
        result = validate_sample_statistics(
            group1=data['group1'],
            group2=data['group2'],
            expected_effect=effect,
            distribution='log-normal'
        )
        
        assert result['passed'], f"Validation failed: {result['reason']}"

    def test_validate_batch_success(self):
        """Test that a valid batch of configurations passes."""
        config = SimulationConfig()
        sample_sizes = [10, 50]
        distributions = ['normal']
        
        success = run_validation_batch(config, sample_sizes, distributions)
        assert success is True

    def test_validate_batch_failure_on_mismatch(self):
        """
        Test that the validation logic correctly identifies a mismatch if we 
        force a theoretical expectation that doesn't match the generated data.
        (Note: This tests the validator logic itself, not the generator).
        """
        n = 100
        effect = 0.5
        seed = 99
        
        data = generate_data(n=n, distribution='normal', effect_size=effect, seed=seed)
        
        # Intentionally pass a wrong expected effect size to force failure
        result = validate_sample_statistics(
            group1=data['group1'],
            group2=data['group2'],
            expected_effect=0.0, # Wrong expectation
            distribution='normal'
        )
        
        assert result['passed'] is False
        assert 'effect size' in result['reason'].lower() or 'difference' in result['reason'].lower()

    def test_logging_file_created(self):
        """Verify that the validation script creates the log file."""
        # This is a bit of an integration test, but checks the artifact requirement
        log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs', 'ground_truth_validation.log')
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        # Run a tiny batch
        config = SimulationConfig()
        run_validation_batch(config, [10], ['normal'])
        
        assert os.path.exists(log_path), "Log file was not created"
        assert os.path.getsize(log_path) > 0, "Log file is empty"