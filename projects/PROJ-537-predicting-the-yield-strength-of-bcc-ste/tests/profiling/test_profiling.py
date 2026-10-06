"""
Unit tests for profiling and optimization utilities.
"""

import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from profiling.optimization_utils import (
    set_thread_pool_size,
    optimize_dataframe_dtypes,
    chunked_dataframe,
    cache_result,
    profile_function
)
from profiling.profile_pipeline import PipelineProfiler

class TestOptimizationUtils:
    """Tests for optimization utilities."""
    
    def test_set_thread_pool_size(self):
        """Test that thread pool size is set correctly."""
        set_thread_pool_size(4)
        
        assert os.environ.get("OMP_NUM_THREADS") == "4"
        assert os.environ.get("OPENBLAS_NUM_THREADS") == "4"
        assert os.environ.get("MKL_NUM_THREADS") == "4"
    
    def test_optimize_dataframe_dtypes(self):
        """Test DataFrame dtype optimization."""
        # Create a test DataFrame
        df = pd.DataFrame({
            "int_col": [1, 2, 3, 4, 5],
            "float_col": [1.1, 2.2, 3.3, 4.4, 5.5],
            "category_col": ["a", "b", "a", "c", "b"]
        })
        
        # Optimize
        optimized = optimize_dataframe_dtypes(df.copy())
        
        # Check that optimization occurred
        assert optimized["int_col"].dtype != "int64"  # Should be downcasted
        assert optimized["float_col"].dtype != "float64"  # Should be downcasted
        assert optimized["category_col"].dtype == "category"
    
    def test_chunked_dataframe(self):
        """Test chunked DataFrame iteration."""
        df = pd.DataFrame({"x": range(100)})
        
        chunks = list(chunked_dataframe(df, chunk_size=10))
        
        assert len(chunks) == 10
        assert len(chunks[0]) == 10
        assert chunks[0]["x"].iloc[0] == 0
        assert chunks[9]["x"].iloc[-1] == 99
    
    def test_cache_result(self):
        """Test caching decorator."""
        call_count = 0
        
        @cache_result
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call
        result1 = expensive_function(5)
        assert call_count == 1
        assert result1 == 10
        
        # Second call with same args - should use cache
        result2 = expensive_function(5)
        assert call_count == 1  # Not incremented
        assert result2 == 10
        
        # Third call with different args - should compute
        result3 = expensive_function(6)
        assert call_count == 2
        assert result3 == 12
    
    def test_profile_function(self, caplog):
        """Test function profiling decorator."""
        @profile_function
        def test_function(x):
            time.sleep(0.01)
            return x * 2
        
        result = test_function(5)
        assert result == 10
        
        # Check that logging occurred
        assert any("test_function" in str(record.message) for record in caplog.records)

class TestPipelineProfiler:
    """Tests for PipelineProfiler class."""
    
    def test_profiler_initialization(self):
        """Test profiler initialization."""
        profiler = PipelineProfiler()
        
        assert profiler.start_time is None
        assert profiler.end_time is None
        assert len(profiler.memory_snapshots) == 0
        assert len(profiler.cpu_snapshots) == 0
        assert len(profiler.phase_timings) == 0
    
    def test_get_memory_info(self):
        """Test memory info retrieval."""
        profiler = PipelineProfiler()
        info = profiler._get_memory_info()
        
        assert "timestamp" in info
        assert "rss_mb" in info
        assert "vms_mb" in info
        assert "percent" in info
        assert info["rss_mb"] > 0
    
    def test_get_cpu_info(self):
        """Test CPU info retrieval."""
        profiler = PipelineProfiler()
        info = profiler._get_cpu_info()
        
        assert "timestamp" in info
        assert "percent" in info
        assert "num_threads" in info
        assert info["num_threads"] >= 1
    
    def test_save_results(self):
        """Test saving profiling results."""
        profiler = PipelineProfiler()
        
        # Create mock results
        results = {
            "total_time_seconds": 100,
            "total_time_hours": 100 / 3600,
            "max_memory_mb": 1000,
            "avg_cpu_percent": 50,
            "phase_timings": {"test": 10},
            "memory_snapshots": [],
            "cpu_snapshots": [],
            "status": "success"
        }
        
        # Create temporary directory for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            # Temporarily override CONFIG.PROVENANCE_DIR
            from config import CONFIG
            original_dir = CONFIG.PROVENANCE_DIR
            CONFIG.PROVENANCE_DIR = Path(tmpdir)
            
            try:
                output_files = profiler.save_results(results)
                
                # Check that files were created
                assert "profile_results" in output_files
                assert "memory_snapshot" in output_files
                assert "cpu_usage" in output_files
                assert "optimization_report" in output_files
                
                # Verify files exist
                for path_str in output_files.values():
                    assert Path(path_str).exists()
                
                # Verify profile_results.json content
                with open(output_files["profile_results"]) as f:
                    saved_results = json.load(f)
                    assert saved_results["total_time_seconds"] == 100
                    assert saved_results["status"] == "success"
                
            finally:
                # Restore original config
                CONFIG.PROVENANCE_DIR = original_dir

if __name__ == "__main__":
    pytest.main([__file__, "-v"])