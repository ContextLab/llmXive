import pytest
import os
import json
import time
from pathlib import Path
from unittest.mock import patch

# Import the module under test
from metrics.cost_profiler import CostProfiler, CostMetrics

class TestCostProfiler:
    """Tests for the CostProfiler utility."""

    @pytest.fixture
    def temp_output_path(self, tmp_path):
        """Provide a temporary file path for output."""
        return tmp_path / "cost_test.jsonl"

    def test_initialization(self, temp_output_path):
        """Test that the profiler initializes correctly."""
        profiler = CostProfiler(str(temp_output_path))
        assert profiler.step_count == 0
        assert profiler.start_time is None
        assert profiler.output_path == temp_output_path
        assert len(profiler.metrics_log) == 0

    def test_start_end_step(self, temp_output_path):
        """Test that a step can be started and ended, returning metrics."""
        profiler = CostProfiler(str(temp_output_path))
        
        profiler.start_step()
        time.sleep(0.01) # Sleep to ensure non-zero CPU time
        metrics = profiler.end_step({"test_key": "test_val"})

        assert isinstance(metrics, CostMetrics)
        assert metrics.step == 0
        assert metrics.cpu_time >= 0.01
        assert metrics.rss_memory_mb >= 0.0
        assert metrics.extra_data == {"test_key": "test_val"}
        assert profiler.step_count == 1

    def test_multiple_steps(self, temp_output_path):
        """Test that multiple steps increment the counter correctly."""
        profiler = CostProfiler(str(temp_output_path))
        
        for i in range(3):
            profiler.start_step()
            time.sleep(0.01)
            profiler.end_step({"step": i})

        assert profiler.step_count == 3
        assert len(profiler.metrics_log) == 3
        assert profiler.metrics_log[0].step == 0
        assert profiler.metrics_log[2].step == 2

    def test_save_log(self, temp_output_path):
        """Test that metrics are saved correctly to JSONL."""
        profiler = CostProfiler(str(temp_output_path))
        
        profiler.start_step()
        time.sleep(0.01)
        profiler.end_step({"data": 123})
        
        profiler.save_log()

        assert temp_output_path.exists()
        with open(temp_output_path, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["step"] == 0
        assert record["cpu_time"] >= 0.01
        assert record["extra_data"]["data"] == 123

    def test_end_step_without_start(self, temp_output_path):
        """Test that calling end_step without start_step raises an error."""
        profiler = CostProfiler(str(temp_output_path))
        with pytest.raises(RuntimeError, match="start_step"):
            profiler.end_step()

    def test_get_summary(self, temp_output_path):
        """Test summary calculation."""
        profiler = CostProfiler(str(temp_output_path))
        
        # Step 1
        profiler.start_step()
        time.sleep(0.02)
        m1 = profiler.end_step()
        
        # Step 2
        profiler.start_step()
        time.sleep(0.01)
        m2 = profiler.end_step()

        summary = profiler.get_summary()
        
        assert summary["steps"] == 2
        assert summary["total_cpu_time"] >= 0.03
        assert summary["avg_rss_mb"] > 0.0
        assert summary["peak_rss_mb"] > 0.0
        assert summary["peak_rss_mb"] >= summary["avg_rss_mb"]

    def test_empty_summary(self, temp_output_path):
        """Test summary when no steps have been run."""
        profiler = CostProfiler(str(temp_output_path))
        summary = profiler.get_summary()
        
        assert summary["total_cpu_time"] == 0.0
        assert summary["avg_rss_mb"] == 0.0
        assert summary["peak_rss_mb"] == 0.0
        assert summary["steps"] == 0
