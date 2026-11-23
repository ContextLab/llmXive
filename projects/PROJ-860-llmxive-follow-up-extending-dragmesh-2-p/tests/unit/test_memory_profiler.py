"""
Unit tests for memory_profiler.py to verify peak memory capture.

These tests validate that the memory profiling utilities correctly:
1. Initialize and reset tracemalloc
2. Capture peak memory usage
3. Handle function profiling with mock workloads
4. Integrate with the pipeline component profiling
"""

import pytest
import sys
import os
import time
import tracemalloc
import tempfile
import json

# Add parent directory to path to import code modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from memory_profiler import (
    setup_profiling_logger,
    profile_function,
    profile_pipeline_component,
    write_profile_results,
    run_memory_profile_pipeline
)

class TestMemoryProfilerSetup:
    """Tests for memory profiler initialization and logging setup."""
    
    def test_setup_profiling_logger_creates_file(self, tmp_path):
        """Verify that setup_profiling_logger creates a valid log file."""
        log_file = tmp_path / "test_memory.log"
        logger = setup_profiling_logger(str(log_file))
        
        assert logger is not None
        assert log_file.exists()
        
        # Test that the logger actually writes
        logger.info("Test log entry")
        with open(log_file, 'r') as f:
            content = f.read()
            assert "Test log entry" in content
    
    def test_setup_profiling_logger_default_path(self):
        """Verify default log file path is used when none provided."""
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            # Temporarily override the default path
            import memory_profiler as mp
            original_default = mp.DEFAULT_LOG_PATH
            mp.DEFAULT_LOG_PATH = os.path.join(tmpdir, "default_test.log")
            
            try:
                logger = setup_profiling_logger()
                assert logger is not None
                log_file = os.path.join(tmpdir, "default_test.log")
                assert os.path.exists(log_file)
            finally:
                mp.DEFAULT_LOG_PATH = original_default

class TestProfileFunction:
    """Tests for the profile_function decorator and functionality."""
    
    def test_profile_function_captures_memory(self):
        """Verify that profile_function correctly measures memory usage."""
        tracemalloc.start()
        
        try:
            # Create a simple function that allocates memory
            @profile_function
            def memory_intensive_function():
                # Allocate a significant amount of memory
                data = [i for i in range(100000)]
                time.sleep(0.01)  # Small delay to allow measurement
                return data
            
            result = memory_intensive_function()
            assert len(result) == 100000
            
            # Verify that memory was actually tracked
            current, peak = tracemalloc.get_traced_memory()
            assert peak > 0
            
        finally:
            tracemalloc.stop()
    
    def test_profile_function_returns_profile_data(self):
        """Verify that profile_function returns correct profile data structure."""
        tracemalloc.start()
        
        try:
            @profile_function
            def simple_function():
                data = [i for i in range(1000)]
                return data
            
            result = simple_function()
            
            # The decorator should return the original result
            assert result is not None
            assert len(result) == 1000
            
        finally:
            tracemalloc.stop()
    
    def test_profile_function_handles_exceptions(self):
        """Verify that profile_function handles exceptions gracefully."""
        tracemalloc.start()
        
        try:
            @profile_function
            def failing_function():
                raise ValueError("Intentional error")
            
            with pytest.raises(ValueError):
                failing_function()
            
        finally:
            tracemalloc.stop()

class TestProfilePipelineComponent:
    """Tests for pipeline component profiling."""
    
    def test_profile_pipeline_component_basic(self):
        """Verify basic pipeline component profiling."""
        tracemalloc.start()
        
        try:
            def mock_component():
                data = [i for i in range(50000)]
                time.sleep(0.01)
                return len(data)
            
            component_name = "test_component"
            result = profile_pipeline_component(component_name, mock_component)
            
            assert result is not None
            assert "component_name" in result
            assert result["component_name"] == component_name
            assert "peak_memory_mb" in result
            assert result["peak_memory_mb"] > 0
            assert "duration_seconds" in result
            assert result["duration_seconds"] >= 0
            
        finally:
            tracemalloc.stop()
    
    def test_profile_pipeline_component_with_args(self):
        """Verify pipeline component profiling with arguments."""
        tracemalloc.start()
        
        try:
            def component_with_args(factor):
                data = [i * factor for i in range(20000)]
                return sum(data)
            
            result = profile_pipeline_component(
                "arg_test_component", 
                component_with_args, 
                args=(2,),
                kwargs={}
            )
            
            assert result is not None
            assert result["peak_memory_mb"] > 0
            
        finally:
            tracemalloc.stop()

class TestWriteProfileResults:
    """Tests for writing profile results to file."""
    
    def test_write_profile_results_creates_file(self, tmp_path):
        """Verify that write_profile_results creates a valid JSON file."""
        output_file = tmp_path / "profile_results.json"
        
        profile_data = {
            "component_name": "test_component",
            "peak_memory_mb": 10.5,
            "duration_seconds": 0.1,
            "timestamp": "2024-01-01T00:00:00"
        }
        
        write_profile_results(output_file, profile_data)
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            loaded_data = json.load(f)
            assert loaded_data == profile_data
    
    def test_write_profile_results_multiple_entries(self, tmp_path):
        """Verify writing multiple profile entries."""
        output_file = tmp_path / "multiple_profiles.json"
        
        profiles = [
            {
                "component_name": "component_1",
                "peak_memory_mb": 5.2,
                "duration_seconds": 0.05,
                "timestamp": "2024-01-01T00:00:00"
            },
            {
                "component_name": "component_2",
                "peak_memory_mb": 8.7,
                "duration_seconds": 0.08,
                "timestamp": "2024-01-01T00:00:01"
            }
        ]
        
        # Write first profile
        write_profile_results(output_file, profiles[0])
        
        # Append second profile (simulate multiple runs)
        write_profile_results(output_file, profiles[1], append=True)
        
        # Verify both entries exist
        with open(output_file, 'r') as f:
            content = f.read()
            assert "component_1" in content
            assert "component_2" in content

class TestRunMemoryProfilePipeline:
    """Tests for the main pipeline profiling function."""
    
    def test_run_memory_profile_pipeline_basic(self, tmp_path):
        """Verify basic pipeline profiling execution."""
        tracemalloc.start()
        
        try:
            def mock_pipeline_step():
                data = [i for i in range(30000)]
                time.sleep(0.01)
                return len(data)
            
            output_file = tmp_path / "pipeline_profile.json"
            
            result = run_memory_profile_pipeline(
                pipeline_name="test_pipeline",
                steps=[("step1", mock_pipeline_step)],
                output_file=str(output_file)
            )
            
            assert result is not None
            assert result["pipeline_name"] == "test_pipeline"
            assert "total_peak_memory_mb" in result
            assert "steps" in result
            assert len(result["steps"]) == 1
            assert result["steps"][0]["component_name"] == "step1"
            
            # Verify output file was created
            assert output_file.exists()
            
        finally:
            tracemalloc.stop()
    
    def test_run_memory_profile_pipeline_multiple_steps(self, tmp_path):
        """Verify pipeline profiling with multiple steps."""
        tracemalloc.start()
        
        try:
            def step1():
                data = [i for i in range(20000)]
                return len(data)
            
            def step2():
                data = [i * 2 for i in range(20000)]
                return len(data)
            
            output_file = tmp_path / "multi_step_profile.json"
            
            result = run_memory_profile_pipeline(
                pipeline_name="multi_step_pipeline",
                steps=[
                    ("data_loading", step1),
                    ("processing", step2)
                ],
                output_file=str(output_file)
            )
            
            assert result is not None
            assert len(result["steps"]) == 2
            assert any(s["component_name"] == "data_loading" for s in result["steps"])
            assert any(s["component_name"] == "processing" for s in result["steps"])
            
        finally:
            tracemalloc.stop()

class TestPeakMemoryCapture:
    """Specific tests for peak memory capture accuracy."""
    
    def test_peak_memory_exceeds_current(self):
        """Verify that peak memory is always >= current memory."""
        tracemalloc.start()
        
        try:
            # Initial state
            current, peak = tracemalloc.get_traced_memory()
            
            # Allocate more memory
            large_data = [i for i in range(200000)]
            
            # Check again
            current_after, peak_after = tracemalloc.get_traced_memory()
            
            # Peak should be at least as high as current
            assert peak_after >= current_after
            assert peak_after > 0
            
        finally:
            tracemalloc.stop()
    
    def test_memory_profiler_detects_allocation(self):
        """Verify that memory profiler detects memory allocation changes."""
        tracemalloc.start()
        
        try:
            initial_current, initial_peak = tracemalloc.get_traced_memory()
            
            # Allocate memory
            data = [i for i in range(100000)]
            
            final_current, final_peak = tracemalloc.get_traced_memory()
            
            # Both current and peak should have increased
            assert final_current >= initial_current
            assert final_peak >= initial_peak
            
        finally:
            tracemalloc.stop()

class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_profile_function_with_none_return(self):
        """Verify profiling works with functions that return None."""
        tracemalloc.start()
        
        try:
            @profile_function
            def returns_none():
                data = [i for i in range(1000)]
                time.sleep(0.01)
                return None
            
            result = returns_none()
            assert result is None
            
        finally:
            tracemalloc.stop()
    
    def test_profile_function_empty_function(self):
        """Verify profiling works with minimal functions."""
        tracemalloc.start()
        
        try:
            @profile_function
            def minimal_function():
                pass
            
            result = minimal_function()
            assert result is None
            
        finally:
            tracemalloc.stop()
    
    def test_write_profile_results_invalid_path(self):
        """Verify graceful handling of invalid output paths."""
        profile_data = {
            "component_name": "test",
            "peak_memory_mb": 1.0,
            "duration_seconds": 0.1,
            "timestamp": "2024-01-01T00:00:00"
        }
        
        # Try to write to a non-existent directory
        with pytest.raises((OSError, IOError)):
            write_profile_results("/nonexistent/path/file.json", profile_data)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])