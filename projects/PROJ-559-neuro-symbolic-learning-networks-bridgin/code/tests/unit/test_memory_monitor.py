"""
Unit tests for the Memory Monitor and Batch Processor.

These tests verify that the memory monitoring logic works correctly
and that the batch processing strategies are implemented without
loading the entire dataset into memory at once.
"""
import pytest
import os
import sys
import tempfile
import json
import pandas as pd
import gc
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.performance.memory_monitor import (
    MemoryMonitor, 
    stream_csv_batch, 
    check_memory_limit, 
    force_gc, 
    MemoryExceededError,
    get_current_memory_mb
)
from code.performance.batch_processor import (
    merge_datasets_streaming,
    process_simulation_logs_batch
)

class TestMemoryMonitor:
    """Tests for the MemoryMonitor context manager and utilities."""

    def test_memory_check_passes_under_limit(self):
        """Test that check_memory_limit passes when under the limit."""
        # Limit is set to a very high number for this test
        try:
            check_memory_limit(threshold_mb=100000)
            assert True
        except MemoryExceededError:
            pytest.fail("check_memory_limit raised unexpectedly under high limit")

    def test_memory_monitor_context_manager(self):
        """Test that MemoryMonitor tracks peak memory correctly."""
        with MemoryMonitor(limit_mb=10000) as monitor:
            initial = get_current_memory_mb()
            # Simulate some work
            data = [i for i in range(10000)]
            current = get_current_memory_mb()
            assert current >= initial
            assert monitor.peak_memory >= current
            assert monitor.peak_memory <= 10000 # Should not exceed limit

    def test_memory_monitor_raises_on_exceed(self):
        """Test that MemoryMonitor raises exception if limit is exceeded."""
        # Set a very low limit to force failure
        with pytest.raises(MemoryExceededError):
            with MemoryMonitor(limit_mb=0.001) as monitor:
                # Force a check immediately
                monitor.check()

    def test_stream_csv_batch_generator(self):
        """Test that stream_csv_batch yields batches correctly."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            # Create a small CSV
            f.write("id,value\n")
            for i in range(100):
                f.write(f"{i},{i*2}\n")
            temp_path = f.name

        try:
            batches = list(stream_csv_batch(temp_path, batch_size=10))
            assert len(batches) == 10
            assert len(batches[0]) == 10
            # Verify data integrity
            assert batches[0]['id'].iloc[0] == 0
            assert batches[0]['value'].iloc[9] == 18
        finally:
            os.unlink(temp_path)

class TestBatchProcessor:
    """Tests for the batch processing logic."""

    def test_process_simulation_logs_batch(self):
        """Test processing a small simulation log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "sim_logs.csv")
            output_path = os.path.join(tmpdir, "processed_logs.csv")
            
            # Create input
            df = pd.DataFrame({
                "student_id": range(100),
                "problem_id": [1]*100,
                "correct": [1]*50 + [0]*50,
                "rt_seconds": [1.5]*100,
                "data_source": ["sim"]*100
            })
            df.to_csv(input_path, index=False)
            
            # Run processor
            process_simulation_logs_batch(input_path, output_path, batch_size=20)
            
            # Verify output
            assert os.path.exists(output_path)
            result = pd.read_csv(output_path)
            assert len(result) == 100
            assert "correct" in result.columns
            assert result['correct'].dtype in [int, float]

    def test_merge_datasets_streaming(self):
        """Test merging two small datasets."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sim_path = os.path.join(tmpdir, "sim.csv")
            real_path = os.path.join(tmpdir, "real.csv")
            output_path = os.path.join(tmpdir, "merged.csv")
            
            # Create inputs
            pd.DataFrame({"id": [1, 2], "val": [10, 20]}).to_csv(sim_path, index=False)
            pd.DataFrame({"id": [3, 4], "val": [30, 40]}).to_csv(real_path, index=False)
            
            # Run merge
            merge_datasets_streaming(sim_path, real_path, output_path, batch_size=10)
            
            # Verify output
            assert os.path.exists(output_path)
            result = pd.read_csv(output_path)
            assert len(result) == 4
            assert "data_source" in result.columns
            assert result['data_source'].unique().tolist() == ["simulated", "real"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
