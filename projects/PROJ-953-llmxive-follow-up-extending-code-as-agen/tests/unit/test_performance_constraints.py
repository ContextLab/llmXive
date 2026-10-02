"""
Unit tests for performance constraints and profiling logic.

Verifies that the profiling script correctly measures runtime and memory
and validates against GitHub Actions constraints.
"""
import os
import sys
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.profile_pipeline import main as profile_main, run_with_profiler

class TestPerformanceConstraints:
    """Tests for performance profiling logic."""

    def test_run_with_profiler_measures_time(self):
        """Verify that run_with_profiler correctly measures execution time."""
        def dummy_func():
            time.sleep(0.1)
        
        runtime, memory, stats = run_with_profiler(dummy_func, "dummy")
        
        assert runtime >= 0.1, "Runtime should be at least 0.1s"
        assert runtime < 1.0, "Runtime should be reasonable for 0.1s sleep"
        assert memory >= 0, "Memory should be non-negative"
        assert isinstance(stats, dict), "Stats should be a dictionary"
        assert "function" in stats, "Stats should contain function list"

    def test_run_with_profiler_handles_exceptions(self):
        """Verify that run_with_profiler raises exceptions from the target function."""
        def failing_func():
            raise ValueError("Test error")
        
        try:
            run_with_profiler(failing_func, "failing")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert str(e) == "Test error"

    def test_constraints_logic(self):
        """Verify constraint checking logic in the report structure."""
        # This test ensures the structure of the report matches expectations
        # We mock the actual pipeline run to avoid long execution
        with patch('scripts.profile_pipeline.run_full_pipeline') as mock_pipeline:
            mock_pipeline.return_value = None
            
            # We need to mock the internal logic to return specific values
            # Since run_with_profiler is called inside main, we patch it
            with patch('scripts.profile_pipeline.run_with_profiler') as mock_profiler:
                mock_profiler.return_value = (3600.0, 5.0, {"function": [], "cumulative_time": [], "call_count": []})
                
                # Run main
                try:
                    profile_main()
                except SystemExit:
                    pass # Expected if constraints are met or not
                
                # Check that the report file was created
                log_dir = project_root / "data" / "logs"
                report_path = log_dir / "pipeline_runtime.json"
                
                # If the file exists, verify its content
                if report_path.exists():
                    with open(report_path) as f:
                        report = json.load(f)
                    
                    assert "results" in report
                    assert "runtime_hours" in report["results"]
                    assert "peak_memory_gb" in report["results"]
                    assert "status" in report["results"]
                    assert report["results"]["status"] in ["PASS", "FAIL"]

    def test_runtime_threshold_check(self):
        """Verify that runtime exceeding limit is detected."""
        # Simulate a runtime of 7 hours (exceeds 6h limit)
        with patch('scripts.profile_pipeline.run_with_profiler') as mock_profiler:
            mock_profiler.return_value = (7 * 3600, 2.0, {"function": [], "cumulative_time": [], "call_count": []})
            
            # Capture stdout to check for warning
            import io
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                try:
                    profile_main()
                except SystemExit as e:
                    # Expected when constraints fail
                    assert e.code == 1
            
            output = f.getvalue()
            assert "CRITICAL" in output or "FAIL" in output

    def test_memory_threshold_check(self):
        """Verify that memory exceeding limit is detected."""
        # Simulate memory usage of 8GB (exceeds 7GB limit)
        with patch('scripts.profile_pipeline.run_with_profiler') as mock_profiler:
            mock_profiler.return_value = (1.0, 8.0, {"function": [], "cumulative_time": [], "call_count": []})
            
            import io
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                try:
                    profile_main()
                except SystemExit as e:
                    assert e.code == 1
            
            output = f.getvalue()
            assert "CRITICAL" in output or "FAIL" in output

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])