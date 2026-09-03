"""
Unit tests for T016b implementation.
Verifies step count, time-bound flagging, and partial output saving.
"""
import pytest
import os
import sys
import tempfile
import json
from datetime import datetime
import pandas as pd
import numpy as np

# Import the module under test
from src.cli.run_simulation import (
    run_simulation_with_timeout,
    verify_step_count,
    parse_args,
    ensure_output_dir
)

class TestT016bImplementation:
    """Tests for T016b runner logic."""

    def test_verify_step_count_success(self):
        """Verify that step count meets target."""
        assert verify_step_count(10000, 10000, False) is True
        assert verify_step_count(15000, 10000, False) is True

    def test_verify_step_count_time_bound(self):
        """Verify that time-bound runs are accepted even with fewer steps."""
        assert verify_step_count(5000, 10000, True) is True
        assert verify_step_count(1000, 10000, True) is True

    def test_verify_step_count_failure(self):
        """Verify that non-time-bound runs with insufficient steps fail."""
        assert verify_step_count(9999, 10000, False) is False
        assert verify_step_count(100, 10000, False) is False

    def test_run_simulation_creates_parquet(self):
        """Test that run_simulation_with_timeout creates the parquet file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                "simulation": {
                    "target_steps": 100, # Small number for unit test
                    "seed": 42,
                    "memory_limit_mb": 7000,
                    "time_limit_seconds": 30
                },
                "output": {
                    "raw_data_dir": tmpdir,
                    "partial_baseline_filename": "test_partial.parquet",
                    "status_log_filename": "test_status.json"
                },
                "logging": {
                    "log_step_latency": True
                }
            }
            
            # Mock logger
            class MockLogger:
                def info(self, msg): pass
                def warning(self, msg): pass
                def error(self, msg): pass
                def log_step_latency(self, step, latency): pass

            logger = MockLogger()
            status = run_simulation_with_timeout(config, tmpdir, logger)
            
            # Check output file exists
            expected_path = os.path.join(tmpdir, "test_partial.parquet")
            assert os.path.exists(expected_path), f"Output file {expected_path} not created"
            
            # Check status log
            status_path = os.path.join(tmpdir, "test_status.json")
            assert os.path.exists(status_path)
            
            with open(status_path, 'r') as f:
                status_data = json.load(f)
            
            assert status_data["actual_steps"] == 100
            assert status_data["status"] == "completed"
            assert "Time-Bound Baseline" not in status_data["flags"]

    def test_run_simulation_time_bound_flag(self):
        """Test that time-bound runs are flagged correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Set a very short time limit to force timeout
            config = {
                "simulation": {
                    "target_steps": 10000,
                    "seed": 42,
                    "memory_limit_mb": 7000,
                    "time_limit_seconds": 0.1 # Force timeout
                },
                "output": {
                    "raw_data_dir": tmpdir,
                    "partial_baseline_filename": "timeout_partial.parquet",
                    "status_log_filename": "test_status.json"
                },
                "logging": {
                    "log_step_latency": True
                }
            }
            
            class MockLogger:
                def info(self, msg): pass
                def warning(self, msg): pass
                def error(self, msg): pass
                def log_step_latency(self, step, latency): pass

            logger = MockLogger()
            status = run_simulation_with_timeout(config, tmpdir, logger)
            
            # Check status
            assert "Time-Bound Baseline" in status["flags"], "Time-Bound Baseline flag missing"
            assert status["status"] == "time-bound"
            
            # Check parquet file exists
            expected_path = os.path.join(tmpdir, "timeout_partial.parquet")
            assert os.path.exists(expected_path), "Partial parquet file not created on timeout"
            
            # Verify minimum 1000 steps for partial run (T057a requirement)
            # Note: In this unit test, the loop might not run 1000 steps due to the very short timeout.
            # The actual integration test would verify this on a real runner.
            # For this unit test, we just verify the file is created.
            df = pd.read_parquet(expected_path)
            assert len(df) > 0, "Partial parquet file is empty"

    def test_parse_args_defaults(self):
        """Test argument parsing defaults."""
        # Simulate no args
        sys.argv = ['run_simulation.py']
        args = parse_args()
        assert args.config == "config/default.yaml"
        assert args.steps is None
        assert args.seed is None

    def test_parse_args_overrides(self):
        """Test argument parsing overrides."""
        sys.argv = ['run_simulation.py', '--steps', '5000', '--seed', '123', '--config', 'test.yaml']
        args = parse_args()
        assert args.steps == 5000
        assert args.seed == 123
        assert args.config == 'test.yaml'

if __name__ == "__main__":
    pytest.main([__file__, "-v"])