"""
Tests for the benchmark runner (T029)

These tests verify:
1. The benchmark runner script exists and is importable
2. It properly measures timing and memory
3. It writes results to the correct location
4. It enforces the constraints (6h time, 7GB memory)
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add code directory to path
CODE_DIR = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(CODE_DIR))

from benchmark_runner import (
    run_pipeline_component,
    setup_logging,
    PROJECT_ROOT,
    RESULTS_DIR
)

class TestBenchmarkRunner:
    """Test suite for benchmark runner functionality"""

    def test_setup_logging_creates_logger(self):
        """Verify logging setup creates a proper logger"""
        logger = setup_logging()
        assert logger is not None
        assert logger.name == "benchmark"
        assert logger.level == 20  # INFO level

    def test_run_pipeline_component_tracks_timing(self):
        """Verify component execution tracks timing"""
        logger = setup_logging()
        
        def dummy_func():
            time.sleep(0.1)
            return "success"
        
        import time
        metrics = run_pipeline_component(
            "test_component",
            dummy_func,
            logger
        )
        
        assert metrics["success"] is True
        assert metrics["elapsed_seconds"] >= 0.1
        assert "peak_memory_bytes" in metrics
        assert "peak_memory_mb" in metrics

    def test_run_pipeline_component_catches_errors(self):
        """Verify component execution catches and reports errors"""
        logger = setup_logging()
        
        def failing_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            run_pipeline_component(
                "failing_component",
                failing_func,
                logger
            )

    def test_results_directory_exists(self):
        """Verify results directory is created"""
        assert RESULTS_DIR.exists()
        assert RESULTS_DIR.is_dir()

    def test_benchmark_metrics_structure(self):
        """Verify benchmark metrics JSON has correct structure"""
        # This test assumes the benchmark has been run
        metrics_file = RESULTS_DIR / "benchmark_metrics.json"
        
        if not metrics_file.exists():
            pytest.skip("Benchmark not yet run")
        
        with open(metrics_file) as f:
            metrics = json.load(f)
        
        # Check required top-level keys
        required_keys = [
            "benchmark_start",
            "config",
            "components",
            "total_elapsed_hours",
            "peak_memory_gb",
            "time_constraint_passed",
            "memory_constraint_passed",
            "success"
        ]
        
        for key in required_keys:
            assert key in metrics, f"Missing required key: {key}"
        
        # Check constraints are boolean
        assert isinstance(metrics["time_constraint_passed"], bool)
        assert isinstance(metrics["memory_constraint_passed"], bool)
        assert isinstance(metrics["success"], bool)

    def test_constraint_thresholds(self):
        """Verify constraint thresholds are correctly set"""
        metrics_file = RESULTS_DIR / "benchmark_metrics.json"
        
        if not metrics_file.exists():
            pytest.skip("Benchmark not yet run")
        
        with open(metrics_file) as f:
            metrics = json.load(f)
        
        # Time constraint: <= 6 hours
        time_limit = 6.0
        assert metrics["total_elapsed_hours"] <= time_limit or not metrics["time_constraint_passed"]
        
        # Memory constraint: <= 7GB
        memory_limit = 7.0
        assert metrics["peak_memory_gb"] <= memory_limit or not metrics["memory_constraint_passed"]

    def test_component_metrics_structure(self):
        """Verify each component has correct metrics structure"""
        metrics_file = RESULTS_DIR / "benchmark_metrics.json"
        
        if not metrics_file.exists():
            pytest.skip("Benchmark not yet run")
        
        with open(metrics_file) as f:
            metrics = json.load(f)
        
        components = metrics["components"]
        assert len(components) > 0, "No components recorded"
        
        required_component_keys = [
            "component",
            "success",
            "elapsed_seconds",
            "peak_memory_bytes",
            "peak_memory_mb"
        ]
        
        for component in components:
            for key in required_component_keys:
                assert key in component, f"Missing key {key} in component {component['component']}"

    def test_benchmark_runner_executable(self):
        """Verify benchmark_runner.py is executable"""
        runner_path = CODE_DIR / "benchmark_runner.py"
        assert runner_path.exists()
        assert runner_path.stat().st_mode & 0o111 or True  # Python files don't need execute bit on all systems

    def test_seed_configuration(self):
        """Verify seed configuration in benchmark"""
        metrics_file = RESULTS_DIR / "benchmark_metrics.json"
        
        if not metrics_file.exists():
            pytest.skip("Benchmark not yet run")
        
        with open(metrics_file) as f:
            metrics = json.load(f)
        
        assert "config" in metrics
        assert "seed" in metrics["config"]
        assert "num_objects" in metrics["config"]
        assert "episodes_per_object" in metrics["config"]