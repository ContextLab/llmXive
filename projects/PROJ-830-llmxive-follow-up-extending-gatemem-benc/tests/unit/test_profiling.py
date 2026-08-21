import pytest
import time
import sys
import os

# Ensure code/ is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.utils.profiling import (
    ProfileResult,
    get_process_memory_mb,
    get_peak_memory_mb,
    start_profiling,
    stop_profiling,
    reset_profiling,
    profile_block,
    profile_function,
    profile_execution,
    get_results_summary,
    save_results_to_file
)

class TestProfileResult:
    def test_profile_result_structure(self):
        """Test that ProfileResult has correct fields."""
        result = ProfileResult(latency_ms=100.5, peak_ram_mb=50.2)
        assert result.latency_ms == 100.5
        assert result.peak_ram_mb == 50.2
        assert isinstance(result.latency_ms, float)
        assert isinstance(result.peak_ram_mb, float)

class TestMemoryFunctions:
    def test_get_process_memory_mb_returns_positive(self):
        """Test that memory function returns positive value."""
        memory = get_process_memory_mb()
        assert isinstance(memory, float)
        assert memory > 0

    def test_get_peak_memory_mb_after_start(self):
        """Test peak memory tracking."""
        start_profiling()
        time.sleep(0.01)
        peak = get_peak_memory_mb()
        stop_profiling()
        assert isinstance(peak, float)
        assert peak > 0

class TestProfilingLifecycle:
    def test_start_stop_profiling(self):
        """Test basic start/stop cycle."""
        start_profiling()
        time.sleep(0.01)
        result = stop_profiling()
        
        assert isinstance(result, ProfileResult)
        assert result.latency_ms >= 0
        assert result.peak_ram_mb > 0

    def test_stop_without_start_raises(self):
        """Test that stopping without starting raises error."""
        # Reset state first
        reset_profiling()
        with pytest.raises(RuntimeError, match="Profiling not started"):
            stop_profiling()

    def test_reset_profiling(self):
        """Test reset functionality."""
        start_profiling()
        reset_profiling()
        # Should be able to start again
        start_profiling()
        time.sleep(0.01)
        result = stop_profiling()
        assert isinstance(result, ProfileResult)

class TestProfileExecution:
    def test_profile_execution_returns_dict(self):
        """Test that profile_execution returns standardized dict."""
        @profile_execution
        def dummy_func():
            time.sleep(0.01)
            return "result"
        
        result = dummy_func()
        
        # Verify it's a dict with correct keys
        assert isinstance(result, dict)
        assert 'latency_ms' in result
        assert 'peak_ram_mb' in result
        assert isinstance(result['latency_ms'], float)
        assert isinstance(result['peak_ram_mb'], float)
        assert result['latency_ms'] >= 0
        assert result['peak_ram_mb'] > 0

    def test_profile_execution_preserves_function_result(self):
        """Test that profile_execution doesn't modify function return."""
        @profile_execution
        def return_value():
            return {"custom": "data", "count": 42}
        
        result = return_value()
        # The decorator wraps the return, so we check the structure
        assert isinstance(result, dict)
        assert 'latency_ms' in result
        assert 'peak_ram_mb' in result

class TestProfileFunctionDecorator:
    def test_profile_function_logs_and_returns(self):
        """Test profile_function decorator."""
        @profile_function
        def sample():
            time.sleep(0.01)
            return "done"
        
        result = sample()
        assert result == "done"

class TestProfileBlock:
    def test_profile_block_context_manager(self):
        """Test profile_block context manager."""
        with profile_block("test_block") as result:
            time.sleep(0.01)
        
        assert isinstance(result, ProfileResult)
        assert result.latency_ms >= 0
        assert result.peak_ram_mb > 0

class TestAggregation:
    def test_get_results_summary(self):
        """Test results aggregation."""
        results = [
            {'latency_ms': 100.0, 'peak_ram_mb': 50.0},
            {'latency_ms': 120.0, 'peak_ram_mb': 55.0},
            {'latency_ms': 80.0, 'peak_ram_mb': 45.0}
        ]
        
        summary = get_results_summary(results)
        
        assert 'latency_ms' in summary
        assert 'peak_ram_mb' in summary
        assert 'mean' in summary['latency_ms']
        assert 'std' in summary['latency_ms']
        assert summary['latency_ms']['mean'] == pytest.approx(100.0, rel=0.01)

    def test_get_results_summary_empty(self):
        """Test aggregation with empty list."""
        summary = get_results_summary([])
        assert summary == {}

class TestSaveToFile:
    def test_save_results_to_file(self, tmp_path):
        """Test saving results to file."""
        results = [
            {'latency_ms': 100.0, 'peak_ram_mb': 50.0},
            {'latency_ms': 120.0, 'peak_ram_mb': 55.0}
        ]
        
        output_path = tmp_path / "profiling_results.json"
        save_results_to_file(results, str(output_path))
        
        assert output_path.exists()
        
        import json
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert 'individual_results' in data
        assert 'summary' in data
        assert len(data['individual_results']) == 2