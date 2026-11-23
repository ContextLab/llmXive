"""
Test for T032: Configuration parameter n_max in generate_partitions.py and asymptotic_baseline.py.

Verifies that:
1. n_max parameter is configurable via command line
2. n_max is explicitly logged at runtime
3. The asymptotic regime is defined by n_max
"""

import os
import sys
import tempfile
import subprocess
import logging
from io import StringIO

import pytest
import numpy as np

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from utils.asymptotic_baseline import compute_asymptotic_baseline

class TestT032Configuration:
    """Tests for n_max configuration parameter."""
    
    def test_asymptotic_baseline_handles_small_n(self):
        """Test that asymptotic baseline handles small n values correctly."""
        # For n=1, should return 0.0
        assert compute_asymptotic_baseline(1) == 0.0
        
        # For n=2, should return a positive value
        val = compute_asymptotic_baseline(2)
        assert val > 0
        
        # For larger n, the value should increase
        val_100 = compute_asymptotic_baseline(100)
        val_10 = compute_asymptotic_baseline(10)
        assert val_100 > val_10
    
    def test_generate_partitions_logs_n_max(self):
        """Test that generate_partitions.py logs the chosen n_max at runtime."""
        # Create a temporary directory for test outputs
        with tempfile.TemporaryDirectory() as tmpdir:
            # Prepare test arguments
            output_csv = os.path.join(tmpdir, "test_output.csv")
            state_file = os.path.join(tmpdir, "test_state.json")
            reference_file = os.path.join(tmpdir, "reference.csv")
            primes_file = os.path.join(tmpdir, "primes.npy")
            
            # Create a minimal reference file
            with open(reference_file, 'w') as f:
                f.write("n,p_P(n)\n1,0\n2,0\n3,0\n4,0\n5,1\n")
            
            # Create a minimal primes file (primes up to 10)
            primes = np.array([2, 3, 5, 7], dtype=np.int64)
            np.save(primes_file, primes)
            
            # Run generate_partitions.py with a specific n_max
            script_path = os.path.join(os.path.dirname(__file__), '..', 'code', 'generate_partitions.py')
            cmd = [
                sys.executable, script_path,
                '--n_max', '10',
                '--reference', reference_file,
                '--output', output_csv,
                '--state', state_file
            ]
            
            # Capture stdout/stderr to check logging
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            )
            
            # Check that the output contains the n_max log message
            combined_output = result.stdout + result.stderr
            assert "n_max = 10" in combined_output, f"Expected 'n_max = 10' in output, got: {combined_output}"
            assert "transition region" in combined_output.lower(), f"Expected mention of asymptotic regime, got: {combined_output}"
            
            # Check that the command succeeded
            assert result.returncode == 0, f"Command failed with: {result.stderr}"
            
            # Verify output file was created
            assert os.path.exists(output_csv), f"Output file not created: {output_csv}"
            
            # Verify output contains expected data
            with open(output_csv, 'r') as f:
                content = f.read()
                assert "n,p_P(n),Q_as(n)" in content
                assert "5,1," in content  # p_P(5) = 1 (5 itself)
    
    def test_default_n_max_value(self):
        """Test that the default n_max value is sufficiently large."""
        # Import the default value from the module
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "generate_partitions",
            os.path.join(os.path.dirname(__file__), '..', 'code', 'generate_partitions.py')
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Check the default value
        default_n_max = getattr(module, 'DEFAULT_N_MAX', None)
        assert default_n_max is not None, "DEFAULT_N_MAX not found in module"
        assert default_n_max >= 10000, f"Default n_max ({default_n_max}) should be sufficiently large for robust coverage"
    
    def test_n_max_affects_output_size(self):
        """Test that different n_max values produce different output sizes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            reference_file = os.path.join(tmpdir, "ref.csv")
            primes_file = os.path.join(tmpdir, "primes.npy")
            output_small = os.path.join(tmpdir, "out_small.csv")
            output_large = os.path.join(tmpdir, "out_large.csv")
            state_small = os.path.join(tmpdir, "state_small.json")
            state_large = os.path.join(tmpdir, "state_large.json")
            
            # Create reference
            with open(reference_file, 'w') as f:
                f.write("n,p_P(n)\n1,0\n2,0\n3,0\n4,0\n5,1\n")
            
            # Create primes
            primes = np.array([2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47], dtype=np.int64)
            np.save(primes_file, primes)
            
            script_path = os.path.join(os.path.dirname(__file__), '..', 'code', 'generate_partitions.py')
            
            # Run with n_max=10
            cmd_small = [
                sys.executable, script_path,
                '--n_max', '10',
                '--reference', reference_file,
                '--output', output_small,
                '--state', state_small
            ]
            result_small = subprocess.run(cmd_small, capture_output=True, text=True)
            assert result_small.returncode == 0
            
            # Run with n_max=20
            cmd_large = [
                sys.executable, script_path,
                '--n_max', '20',
                '--reference', reference_file,
                '--output', output_large,
                '--state', state_large
            ]
            result_large = subprocess.run(cmd_large, capture_output=True, text=True)
            assert result_large.returncode == 0
            
            # Compare output sizes
            with open(output_small, 'r') as f:
                lines_small = len(f.readlines())
            with open(output_large, 'r') as f:
                lines_large = len(f.readlines())
            
            # Output with n_max=20 should have more lines than n_max=10
            assert lines_large > lines_small, f"Expected more lines for n_max=20 ({lines_large}) than n_max=10 ({lines_small})"