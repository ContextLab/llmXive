"""
Unit tests for the Monte Carlo Integration Benchmark Worker.

These tests verify the correctness of the Pi estimation logic,
parameter handling, and output generation without requiring network access.
"""
import json
import math
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module to test
# We need to ensure the path is set up correctly
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from orchestrator.workers.monte_carlo import estimate_pi, run_benchmark, main
from orchestrator.models import TaskStatus

class TestEstimatePi:
    def test_estimation_accuracy_large_samples(self):
        """Test that with a large number of samples, the estimate is close to pi."""
        num_samples = 1000000
        seed = 42
        
        result = estimate_pi(num_samples, seed=seed)
        
        assert result["num_samples"] == num_samples
        assert result["status"] == "success"
        
        # With 1M samples, we expect reasonable accuracy (within 0.1%)
        # This is a statistical test, so we allow some margin
        actual_pi = math.pi
        error = result["absolute_error"]
        relative_error = result["relative_error"]
        
        assert error < 0.01  # Within 0.01 of actual pi
        assert relative_error < 0.001  # Within 0.1%
        
        # Verify the estimate is reasonable
        assert 3.13 < result["pi_estimate"] < 3.15

    def test_estimation_deterministic_with_seed(self):
        """Test that the same seed produces the same result."""
        num_samples = 100000
        seed = 12345
        
        result1 = estimate_pi(num_samples, seed=seed)
        result2 = estimate_pi(num_samples, seed=seed)
        
        assert result1["pi_estimate"] == result2["pi_estimate"]
        assert result1["inside_circle"] == result2["inside_circle"]

    def test_small_sample_variance(self):
        """Test that small sample sizes have higher variance (statistical check)."""
        num_samples = 100
        
        # Run multiple times to check variance
        estimates = []
        for i in range(10):
            result = estimate_pi(num_samples, seed=i)
            estimates.append(result["pi_estimate"])
        
        # With small samples, variance should be non-zero
        variance = sum((x - sum(estimates)/len(estimates))**2 for x in estimates) / len(estimates)
        assert variance > 0.001  # Should have some variance

    def test_elapsed_time_positive(self):
        """Test that elapsed time is positive."""
        result = estimate_pi(10000, seed=42)
        assert result["elapsed_seconds"] > 0

    def test_inside_circle_count_valid(self):
        """Test that inside_circle count is valid."""
        num_samples = 1000
        result = estimate_pi(num_samples, seed=42)
        
        assert result["inside_circle"] >= 0
        assert result["inside_circle"] <= num_samples

class TestRunBenchmark:
    def test_run_benchmark_writes_file(self):
        """Test that run_benchmark writes a valid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_output.json")
            run_id = "test_run_001"
            node_id = "test_node"
            
            success = run_benchmark(
                num_samples=10000,
                output_path=output_path,
                run_id=run_id,
                node_id=node_id,
                seed=42
            )
            
            assert success is True
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert data["run_id"] == run_id
            assert data["node_id"] == node_id
            assert data["task_type"] == "monte_carlo_pi"
            assert data["status"] == TaskStatus.COMPLETED.value
            assert "metrics" in data
            assert "pi_estimate" in data["metrics"]

    def test_run_benchmark_creates_directories(self):
        """Test that run_benchmark creates parent directories if they don't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a nested path that doesn't exist yet
            output_path = os.path.join(tmpdir, "nested", "deep", "output.json")
            
            success = run_benchmark(
                num_samples=1000,
                output_path=output_path,
                run_id="test_run",
                node_id="test"
            )
            
            assert success is True
            assert os.path.exists(output_path)

    def test_run_benchmark_handles_failure(self):
        """Test that run_benchmark writes failure record on exception."""
        # This is hard to trigger without mocking, but we can test the structure
        # by mocking the estimate_pi function to raise an exception
        with patch('orchestrator.workers.monte_carlo.estimate_pi', side_effect=Exception("Test error")):
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = os.path.join(tmpdir, "failure_output.json")
                
                success = run_benchmark(
                    num_samples=1000,
                    output_path=output_path,
                    run_id="fail_run",
                    node_id="test"
                )
                
                assert success is False
                assert os.path.exists(output_path)
                
                with open(output_path, 'r') as f:
                    data = json.load(f)
                
                assert data["status"] == TaskStatus.FAILED.value
                assert "error" in data

class TestMain:
    def test_main_parsing(self, capsys):
        """Test that main() parses arguments correctly."""
        # Mock sys.argv
        test_args = [
            'monte_carlo.py',
            '--samples', '1000',
            '--output', '/tmp/test_main.json',
            '--run-id', 'main_test_001',
            '--node-id', 'cli_node',
            '--seed', '99'
        ]
        
        with patch('sys.argv', test_args):
            # We can't easily test the full run without file I/O issues in tests,
            # but we can verify the argument parsing logic by checking if it runs
            # without argument errors
            try:
                # Temporarily redirect stdout/stderr to avoid clutter
                import io
                from contextlib import redirect_stdout, redirect_stderr
                
                # This will actually run the benchmark, which is fine for a unit test
                # as long as it completes quickly
                main()
                
                # Check if output file was created
                assert os.path.exists('/tmp/test_main.json')
                
                with open('/tmp/test_main.json', 'r') as f:
                    data = json.load(f)
                
                assert data["metrics"]["num_samples"] == 1000
                assert data["run_id"] == "main_test_001"
                assert data["node_id"] == "cli_node"
                
            finally:
                # Cleanup
                if os.path.exists('/tmp/test_main.json'):
                    os.remove('/tmp/test_main.json')

    def test_main_default_values(self):
        """Test that main() uses default values when no args provided."""
        test_args = ['monte_carlo.py']
        
        with patch('sys.argv', test_args):
            # Use a temporary file for output
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = os.path.join(tmpdir, "default_output.json")
                test_args_with_output = ['monte_carlo.py', '--output', output_path]
                
                with patch('sys.argv', test_args_with_output):
                    main()
                    
                    assert os.path.exists(output_path)
                    
                    with open(output_path, 'r') as f:
                        data = json.load(f)
                    
                    # Check defaults
                    assert data["metrics"]["num_samples"] == 1000000
                    assert data["node_id"] == "local_worker"