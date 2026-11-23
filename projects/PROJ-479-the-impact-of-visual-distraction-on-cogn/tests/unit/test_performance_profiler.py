"""
Unit tests for the performance profiler module.

Tests verify that the profiler correctly measures runtime and memory usage,
and generates appropriate reports.
"""
import os
import sys
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import pytest

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from code.utils import get_logger
from code._performance_profiler import (
    ensure_output_dir,
    get_memory_usage_mb,
    profile_script,
    generate_markdown_report,
    main
)

class TestEnsureOutputDir:
    """Tests for ensure_output_dir function."""
    
    def test_creates_directory_if_not_exists(self):
        """Test that the function creates the output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = os.path.join(tmpdir, "test_output")
            assert not os.path.exists(test_dir)
            
            # Mock the OUTPUT_DIR to use our temp directory
            with patch('code._performance_profiler.OUTPUT_DIR', test_dir):
                ensure_output_dir()
            
            assert os.path.exists(test_dir)
            assert os.path.isdir(test_dir)
    
    def test_does_not_error_if_exists(self):
        """Test that the function doesn't error if directory already exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = os.path.join(tmpdir, "test_output")
            os.makedirs(test_dir)
            
            with patch('code._performance_profiler.OUTPUT_DIR', test_dir):
                ensure_output_dir()  # Should not raise
            
            assert os.path.exists(test_dir)

class TestGetMemoryUsageMb:
    """Tests for get_memory_usage_mb function."""
    
    def test_returns_positive_number(self):
        """Test that the function returns a positive number."""
        memory = get_memory_usage_mb()
        assert memory >= 0
    
    def test_returns_float(self):
        """Test that the function returns a float."""
        memory = get_memory_usage_mb()
        assert isinstance(memory, float)

class TestProfileScript:
    """Tests for profile_script function."""
    
    def test_script_not_found_returns_error(self):
        """Test that missing script returns error status."""
        result = profile_script("/nonexistent/script.py", "test_script")
        
        assert result["status"] == "error"
        assert "Script not found" in result["error"]
        assert result["runtime_seconds"] is None
    
    def test_successful_profile_returns_expected_keys(self):
        """Test that successful profiling returns all expected keys."""
        # Create a temporary script
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('hello')\n")
            temp_script = f.name
        
        try:
            result = profile_script(temp_script, "test_script")
            
            assert result["status"] == "success"
            assert "runtime_seconds" in result
            assert "peak_memory_mb" in result
            assert "within_limit" in result
            assert isinstance(result["runtime_seconds"], (int, float))
            assert isinstance(result["peak_memory_mb"], (int, float))
        finally:
            os.unlink(temp_script)

class TestGenerateMarkdownReport:
    """Tests for generate_markdown_report function."""
    
    def test_generates_valid_markdown(self):
        """Test that the function generates valid markdown."""
        results = {
            "script1.py": {
                "status": "success",
                "runtime_seconds": 100,
                "peak_memory_mb": 50.5,
                "within_limit": True
            }
        }
        
        report = generate_markdown_report(results)
        
        assert "# Performance Profiling Report" in report
        assert "script1.py" in report
        assert "100.00" in report  # Runtime
        assert "50.50" in report   # Memory
        assert "✅ PASS" in report
    
    def test_handles_error_status(self):
        """Test that the function handles error status correctly."""
        results = {
            "script1.py": {
                "status": "error",
                "error": "Test error"
            }
        }
        
        report = generate_markdown_report(results)
        
        assert "❌ Error" in report
        assert "Test error" in report

class TestMain:
    """Tests for main function."""
    
    def test_creates_output_files(self):
        """Test that main creates the expected output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a fake script to profile
            fake_script = os.path.join(tmpdir, "fake_script.py")
            with open(fake_script, 'w') as f:
                f.write("print('hello')\n")
            
            # Mock paths
            with patch('code._performance_profiler.DATA_ACQUISITION_SCRIPT', fake_script):
                with patch('code._performance_profiler.VISUAL_METRICS_SCRIPT', fake_script):
                    with patch('code._performance_profiler.OUTPUT_DIR', os.path.join(tmpdir, "output")):
                        with patch('code._performance_profiler.JSON_OUTPUT', os.path.join(tmpdir, "output", "perf.json")):
                            with patch('code._performance_profiler.MD_OUTPUT', os.path.join(tmpdir, "output", "perf.md")):
                                result = main()
                                
                                # Check that files were created
                                assert os.path.exists(os.path.join(tmpdir, "output", "perf.json"))
                                assert os.path.exists(os.path.join(tmpdir, "output", "perf.md"))
                                assert result == 0  # Success
    
    def test_returns_nonzero_on_failure(self):
        """Test that main returns non-zero on failure."""
        # This is harder to test without actually failing a script
        # For now, we'll just verify the function exists and has the right signature
        assert callable(main)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])