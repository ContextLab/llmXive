import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.data.profiles import (
    get_memory_usage_mb,
    get_cpu_time_seconds,
    profile_clip_execution,
    save_profiling_results,
    load_profiling_results,
    run_feasibility_gate
)


class TestMemoryProfiling:
    """Unit tests for memory profiling functions."""

    def test_get_memory_usage_mb_returns_positive_value(self):
        """Test that memory usage is a positive number."""
        mem = get_memory_usage_mb()
        assert isinstance(mem, float)
        assert mem >= 0

    def test_get_cpu_time_seconds_returns_positive_value(self):
        """Test that CPU time is a non-negative number."""
        cpu_time = get_cpu_time_seconds()
        assert isinstance(cpu_time, float)
        assert cpu_time >= 0

    def test_profile_clip_execution_success(self):
        """Test profiling a successful execution."""
        def dummy_func():
            pass

        result = profile_clip_execution("test_clip", dummy_func)

        assert result["clip_id"] == "test_clip"
        assert result["status"] == "success"
        assert result["cpu_time_seconds"] >= 0
        assert result["memory_peak_mb"] >= 0

    def test_profile_clip_execution_failure(self):
        """Test profiling a failing execution."""
        def failing_func():
            raise ValueError("Test error")

        result = profile_clip_execution("test_clip", failing_func)

        assert result["clip_id"] == "test_clip"
        assert result["status"] == "failed"
        assert result["error"] is not None

    def test_save_and_load_profiling_results(self, tmp_path):
        """Test saving and loading profiling results."""
        profiling_results = [
            {
                "clip_id": "clip1",
                "status": "success",
                "cpu_time_seconds": 1.0,
                "memory_peak_mb": 100.0
            },
            {
                "clip_id": "clip2",
                "status": "success",
                "cpu_time_seconds": 2.0,
                "memory_peak_mb": 200.0
            }
        ]

        output_path = tmp_path / "test_profiling.json"

        # Save results
        saved_path = save_profiling_results(profiling_results, str(output_path))
        assert os.path.exists(saved_path)

        # Load results
        loaded_results = load_profiling_results(str(output_path))
        assert len(loaded_results) == 2
        assert loaded_results[0]["clip_id"] == "clip1"
        assert loaded_results[1]["clip_id"] == "clip2"

    def test_run_feasibility_gate_pass(self):
        """Test feasibility gate when thresholds are met."""
        profiling_results = [
            {
                "clip_id": "clip1",
                "status": "success",
                "cpu_time_seconds": 1.0,
                "memory_peak_mb": 1000.0  # ~1GB
            }
        ]

        gate_result = run_feasibility_gate(
            profiling_results,
            memory_threshold_gb=7.0,
            projected_hours_threshold=6.0
        )

        assert gate_result["gate_passed"] is True
        assert gate_result["max_memory_gb"] < 7.0

    def test_run_feasibility_gate_fail_memory(self):
        """Test feasibility gate when memory threshold is exceeded."""
        profiling_results = [
            {
                "clip_id": "clip1",
                "status": "success",
                "cpu_time_seconds": 1.0,
                "memory_peak_mb": 8000.0  # ~8GB
            }
        ]

        gate_result = run_feasibility_gate(
            profiling_results,
            memory_threshold_gb=7.0,
            projected_hours_threshold=6.0
        )

        assert gate_result["gate_passed"] is False
        assert gate_result["details"]["memory_ok"] is False

    def test_run_feasibility_gate_fail_time(self):
        """Test feasibility gate when time threshold is exceeded."""
        # Simulate a very slow clip (1 hour per clip)
        profiling_results = [
            {
                "clip_id": "clip1",
                "status": "success",
                "cpu_time_seconds": 3600.0,  # 1 hour
                "memory_peak_mb": 1000.0
            }
        ]

        gate_result = run_feasibility_gate(
            profiling_results,
            memory_threshold_gb=7.0,
            projected_hours_threshold=6.0
        )

        assert gate_result["gate_passed"] is False
        assert gate_result["details"]["time_ok"] is False

    def test_run_feasibility_gate_no_success(self):
        """Test feasibility gate when no successful profiles exist."""
        profiling_results = [
            {
                "clip_id": "clip1",
                "status": "failed",
                "error": "Some error"
            }
        ]

        gate_result = run_feasibility_gate(profiling_results)

        assert gate_result["gate_passed"] is False
        assert "No successful profiling results" in gate_result["reason"]