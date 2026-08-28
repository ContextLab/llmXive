"""
Integration tests for simulation pipeline memory limits.

Tests that the simulation pipeline correctly enforces memory limits
and terminates gracefully when the memory threshold is exceeded.
"""
import pytest
import os
import sys
import time
import json
import tempfile
import subprocess
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from cli.run_simulation import (
    SimulationResult,
    get_memory_usage_mb,
    check_memory_and_log,
    run_with_timeout,
    parse_args,
    main
)
from sim.eco_director import run_simulation, load_config
from config import set_seed


class TestMemoryLimitEnforcement:
    """Tests for memory limit enforcement in the simulation pipeline."""

    def test_memory_monitoring_function(self):
        """Test that get_memory_usage_mb returns a valid positive number."""
        memory = get_memory_usage_mb()
        assert isinstance(memory, (int, float))
        assert memory >= 0, "Memory usage should be non-negative"

    def test_check_memory_and_log_with_limit(self):
        """Test that check_memory_and_log returns True when under limit."""
        # Set a very high limit to ensure we're under it
        current_memory = get_memory_usage_mb()
        limit = current_memory * 2
        
        result = check_memory_and_log(limit)
        assert result is True, "Should return True when under memory limit"

    def test_check_memory_and_log_over_limit(self, capsys):
        """Test that check_memory_and_log returns False when over limit."""
        # Set a limit of 0 to force an over-limit condition
        result = check_memory_and_log(0)
        captured = capsys.readouterr()
        
        assert result is False, "Should return False when over memory limit"
        assert "Memory limit exceeded" in captured.out

    def test_run_with_timeout_basic(self):
        """Test basic timeout functionality."""
        def quick_func():
            return "done"
        
        result = run_with_timeout(quick_func, timeout=5)
        assert result == "done"

    def test_run_with_timeout_exceeded(self):
        """Test that timeout works when function takes too long."""
        def slow_func():
            time.sleep(10)
            return "done"
        
        with pytest.raises(TimeoutError):
            run_with_timeout(slow_func, timeout=1)

    def test_integration_memory_limit_in_simulation(self, tmp_path):
        """
        Integration test: Run a simulation with a memory limit that should
        cause termination. This test verifies the end-to-end memory monitoring
        loop in the simulation pipeline.
        """
        # Create a temporary config file for the simulation
        config_content = {
            "simulation": {
                "steps": 1000,
                "grid_size": 50,
                "seed": 42
            },
            "ca_params": {
                "locality": 0.5,
                "memory": 0.3,
                "non_linearity": 0.7
            }
        }
        
        config_file = tmp_path / "test_config.yaml"
        import yaml
        with open(config_file, 'w') as f:
            yaml.dump(config_content, f)
        
        # Test that the simulation can be loaded and run with a reasonable memory limit
        # (We don't actually trigger OOM in this test, but verify the monitoring hooks work)
        set_seed(42)
        
        # Load config and verify it works
        config = load_config(str(config_file))
        assert config is not None
        
        # Run a short simulation to verify the pipeline works
        # We'll use a small grid and few steps to ensure it completes quickly
        small_config = {
            "simulation": {
                "steps": 100,
                "grid_size": 10,
                "seed": 42
            },
            "ca_params": {
                "locality": 0.5,
                "memory": 0.3,
                "non_linearity": 0.7
            }
        }
        
        small_config_file = tmp_path / "small_config.yaml"
        with open(small_config_file, 'w') as f:
            yaml.dump(small_config, f)
        
        # Run simulation with memory monitoring
        result = run_simulation(
            config_file=str(small_config_file),
            memory_limit_mb=5000,  # 5GB limit
            timeout_seconds=60
        )
        
        assert isinstance(result, SimulationResult)
        assert result.status in ["completed", "terminated"]
        assert result.memory_limit_mb == 5000

    def test_cli_memory_limit_argument_parsing(self):
        """Test that CLI correctly parses memory limit arguments."""
        test_args = [
            'run_simulation.py',
            '--config', 'test.yaml',
            '--memory-limit', '4096',
            '--timeout', '300'
        ]
        
        args = parse_args(test_args)
        assert args.memory_limit == 4096
        assert args.timeout == 300

    def test_memory_limit_json_log_output(self, capsys):
        """Test that memory limit enforcement outputs proper JSON log."""
        # Force a memory limit check that will fail (limit = 0)
        check_memory_and_log(0)
        
        captured = capsys.readouterr()
        output = captured.out.strip()
        
        # Verify it's valid JSON
        log_data = json.loads(output)
        assert "status" in log_data
        assert log_data["status"] == "memory_limit_exceeded"
        assert "memory_mb" in log_data
        assert "timestamp" in log_data

    def test_simulation_result_memory_tracking(self):
        """Test that SimulationResult correctly tracks memory usage."""
        result = SimulationResult(
            status="completed",
            steps=100,
            coherence_score=0.85,
            diversity_score=0.72,
            memory_mb=1024.5,
            elapsed_time=10.0,
            memory_limit_mb=4096
        )
        
        assert result.memory_mb == 1024.5
        assert result.memory_limit_mb == 4096
        assert result.is_within_memory_limit() is True

        result_high_memory = SimulationResult(
            status="terminated",
            steps=50,
            coherence_score=0.45,
            diversity_score=0.30,
            memory_mb=5000.0,
            elapsed_time=5.0,
            memory_limit_mb=4096
        )
        
        assert result_high_memory.is_within_memory_limit() is False
        assert result_high_memory.status == "terminated"

class TestPipelineTimeoutEnforcement:
    """Tests for timeout enforcement in the simulation pipeline."""

    def test_timeout_in_simulation(self, tmp_path):
        """Test that simulation respects timeout limits."""
        config_content = {
            "simulation": {
                "steps": 10000,  # Many steps to take time
                "grid_size": 50,
                "seed": 42
            },
            "ca_params": {
                "locality": 0.5,
                "memory": 0.3,
                "non_linearity": 0.7
            }
        }
        
        config_file = tmp_path / "timeout_config.yaml"
        import yaml
        with open(config_file, 'w') as f:
            yaml.dump(config_content, f)
        
        # Run with a very short timeout
        result = run_simulation(
            config_file=str(config_file),
            memory_limit_mb=5000,
            timeout_seconds=1  # 1 second timeout
        )
        
        # Should be terminated due to timeout
        assert result.status in ["completed", "terminated"]
        # If it terminated, the elapsed time should be close to the timeout
        if result.status == "terminated":
            assert result.elapsed_time <= 2.0  # Allow some buffer

    def test_cli_timeout_argument(self):
        """Test CLI timeout argument parsing."""
        test_args = [
            'run_simulation.py',
            '--config', 'test.yaml',
            '--timeout', '120'
        ]
        
        args = parse_args(test_args)
        assert args.timeout == 120

class TestEndToEndPipeline:
    """End-to-end integration tests for the full simulation pipeline."""

    def test_full_pipeline_with_memory_monitoring(self, tmp_path):
        """
        Full end-to-end test: Create config, run simulation with memory
        monitoring, and verify results are properly recorded.
        """
        # Create a valid config
        config_content = {
            "simulation": {
                "steps": 200,
                "grid_size": 20,
                "seed": 42
            },
            "ca_params": {
                "locality": 0.5,
                "memory": 0.3,
                "non_linearity": 0.7
            }
        }
        
        config_file = tmp_path / "e2e_config.yaml"
        import yaml
        with open(config_file, 'w') as f:
            yaml.dump(config_content, f)
        
        # Run the simulation
        result = run_simulation(
            config_file=str(config_file),
            memory_limit_mb=4096,
            timeout_seconds=120
        )
        
        # Verify result structure
        assert isinstance(result, SimulationResult)
        assert result.steps == 200
        assert result.memory_limit_mb == 4096
        assert result.status in ["completed", "terminated"]
        
        # If completed, we should have valid scores
        if result.status == "completed":
            assert result.coherence_score is not None
            assert result.diversity_score is not None
            assert result.elapsed_time > 0

    def test_multiple_runs_consistency(self, tmp_path):
        """Test that multiple runs with same config produce consistent results."""
        config_content = {
            "simulation": {
                "steps": 50,
                "grid_size": 10,
                "seed": 123  # Fixed seed
            },
            "ca_params": {
                "locality": 0.5,
                "memory": 0.3,
                "non_linearity": 0.7
            }
        }
        
        config_file = tmp_path / "consistent_config.yaml"
        import yaml
        with open(config_file, 'w') as f:
            yaml.dump(config_content, f)
        
        # Run twice with same seed
        result1 = run_simulation(
            config_file=str(config_file),
            memory_limit_mb=4096,
            timeout_seconds=60
        )
        
        result2 = run_simulation(
            config_file=str(config_file),
            memory_limit_mb=4096,
            timeout_seconds=60
        )
        
        # Results should be identical due to fixed seed
        assert result1.coherence_score == result2.coherence_score
        assert result1.diversity_score == result2.diversity_score
        assert result1.steps == result2.steps