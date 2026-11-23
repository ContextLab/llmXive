import pytest
import os
import sys
import subprocess
from unittest.mock import patch, MagicMock
import numpy as np

# Import the function to test
from src.environment.runner import enforce_cpu_cores

class TestCPUEnforcement:
    """Tests for the enforce_cpu_cores function in runner.py"""

    def test_enforce_cpu_cores_valid_count(self):
        """Test that enforce_cpu_cores successfully pins to valid core count"""
        # Mock os.sched_setaffinity and os.sched_getaffinity to avoid actual system calls
        # in environments where they might fail or be restricted
        with patch('os.sched_setaffinity') as mock_set, \
             patch('os.sched_getaffinity', return_value={0, 1}), \
             patch('os.cpu_count', return_value=4), \
             patch.dict(os.environ, {}, clear=False):
            
            # This should not raise
            enforce_cpu_cores(cores=2)
            
            # Verify setaffinity was called with correct args
            mock_set.assert_called_once_with(0, [0, 1])
            assert os.environ['OMP_NUM_THREADS'] == '2'

    def test_enforce_cpu_cores_invalid_count_too_high(self):
        """Test that enforce_cpu_cores raises error if requested cores > available"""
        with patch('os.cpu_count', return_value=2):
            with pytest.raises(RuntimeError, match="Requested 4 cores but system only has 2"):
                enforce_cpu_cores(cores=4)

    def test_enforce_cpu_cores_invalid_count_zero(self):
        """Test that enforce_cpu_cores raises error if cores < 1"""
        with pytest.raises(RuntimeError, match="Requested cores .* must be >= 1"):
            enforce_cpu_cores(cores=0)

    def test_enforce_cpu_cores_sets_omp_env(self):
        """Test that OMP_NUM_THREADS is set correctly"""
        with patch('os.sched_setaffinity'), \
             patch('os.sched_getaffinity', return_value={0, 1}), \
             patch('os.cpu_count', return_value=4):
            
            enforce_cpu_cores(cores=2)
            
            assert os.environ.get('OMP_NUM_THREADS') == '2'

    def test_enforce_cpu_cores_unavailable_platform(self):
        """Test behavior when sched_setaffinity is not available (e.g. Windows)"""
        with patch('os.cpu_count', return_value=4), \
             patch('os.sched_setaffinity', side_effect=AttributeError("No setaffinity")):
            
            with pytest.raises(RuntimeError, match="os.sched_setaffinity is not available"):
                enforce_cpu_cores(cores=2)

    def test_verify_nproc_simulation(self):
        """
        Simulate the verification step: run a subprocess to check effective concurrency.
        Note: This test verifies the logic of the verification, not the actual system state.
        """
        # We cannot easily test `nproc` output in a mock environment,
        # so we verify that the function sets the environment variable
        # which is the primary mechanism for controlling thread count in the runner.
        with patch('os.sched_setaffinity'), \
             patch('os.sched_getaffinity', return_value={0, 1}), \
             patch('os.cpu_count', return_value=4):
            
            enforce_cpu_cores(cores=2)
            
            # The verification in the runner script relies on OMP_NUM_THREADS
            # and the affinity set. We confirm these are set.
            assert os.environ['OMP_NUM_THREADS'] == '2'