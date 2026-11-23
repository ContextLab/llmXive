"""
Unit tests for the performance harness.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code import code
from code import code

# We need to import the module we're testing
# Since it's in code/042_run_performance_harness.py, we need to handle the import carefully
import importlib.util
spec = importlib.util.spec_from_file_location(
    "performance_harness",
    Path(__file__).parent.parent / "code" / "042_run_performance_harness.py"
)
performance_harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(performance_harness)

class TestEnsureDirectories:
    def test_ensure_directories_creates_path(self, tmp_path):
        """Test that ensure_directories creates the required directory."""
        # Mock the Path to use our temp directory
        with patch('code.042_run_performance_harness.Path') as mock_path:
            mock_dir = MagicMock()
            mock_path.return_value = mock_dir
            
            performance_harness.ensure_directories()
            
            mock_path.assert_called_once_with("data/processed")
            mock_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)

class TestRunStepWithProfiling:
    def test_run_step_success(self, tmp_path):
        """Test successful execution of a step."""
        # Create a dummy script that exits successfully
        dummy_script = tmp_path / "dummy.py"
        dummy_script.write_text("import sys; sys.exit(0)")
        
        with patch('code.042_run_performance_harness.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            result = performance_harness.run_step_with_profiling(
                "Test Step",
                str(dummy_script)
            )
            
            assert result["status"] == "success"
            assert result["exit_code"] == 0
            assert "wall_clock_time_seconds" in result
            assert "peak_memory_mb" in result

    def test_run_step_timeout(self, tmp_path):
        """Test handling of timeout."""
        from subprocess import TimeoutExpired
        
        with patch('code.042_run_performance_harness.subprocess.run') as mock_run:
            mock_run.side_effect = TimeoutExpired(cmd="test", timeout=3600)
            
            result = performance_harness.run_step_with_profiling(
                "Test Step",
                str(tmp_path / "dummy.py")
            )
            
            assert result["status"] == "timeout"
            assert result["exit_code"] == -1
            assert result["error"] == "Timeout"

    def test_run_step_error(self, tmp_path):
        """Test handling of script error."""
        with patch('code.042_run_performance_harness.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Error occurred")
            
            result = performance_harness.run_step_with_profiling(
                "Test Step",
                str(tmp_path / "dummy.py")
            )
            
            assert result["status"] == "error"
            assert result["exit_code"] == -1
            assert "Error" in result["error"] or result["error"] == "Step Test Step failed"

class TestRunFullPipelineProfiling:
    def test_run_full_pipeline(self, tmp_path):
        """Test full pipeline profiling with mocked steps."""
        # Create dummy scripts for each step
        steps = [
            ("Ingest OpenML Data", tmp_path / "01_ingest_openml.py"),
            ("Parse Publications", tmp_path / "02_parse_publications.py"),
            ("Compute Sensitivity", tmp_path / "03_compute_sensitivity.py"),
            ("Generate Report", tmp_path / "04_generate_report.py")
        ]
        
        for step_name, script_path in steps:
            script_path.write_text("import sys; sys.exit(0)")
        
        with patch('code.042_run_performance_harness.run_step_with_profiling') as mock_run:
            mock_run.return_value = {
                "step_name": "Test",
                "script_path": "test.py",
                "status": "success",
                "wall_clock_time_seconds": 1.0,
                "peak_memory_mb": 100.0,
                "exit_code": 0
            }
            
            results = performance_harness.run_full_pipeline_profiling()
            
            assert "steps" in results
            assert "aggregate" in results
            assert results["aggregate"]["total_steps"] == 4
            assert results["aggregate"]["successful_steps"] == 4

class TestSaveResults:
    def test_save_results(self, tmp_path):
        """Test saving results to JSON."""
        output_path = tmp_path / "test_metrics.json"
        
        test_data = {
            "step": "test",
            "time": 1.0,
            "memory": 100.0
        }
        
        performance_harness.save_results(test_data, str(output_path))
        
        assert output_path.exists()
        
        with open(output_path) as f:
            saved_data = json.load(f)
        
        assert saved_data == test_data

class TestMain:
    def test_main_success(self, tmp_path):
        """Test main function with successful pipeline."""
        # Mock all the internal functions
        with patch('code.042_run_performance_harness.ensure_directories'), \
             patch('code.042_run_performance_harness.run_full_pipeline_profiling') as mock_run, \
             patch('code.042_run_performance_harness.save_results'), \
             patch('code.042_run_performance_harness.sys.exit') as mock_exit:
            
            mock_run.return_value = {
                "aggregate": {
                    "failed_steps": 0
                }
            }
            
            performance_harness.main()
            
            mock_exit.assert_called_once_with(0)

    def test_main_failure(self, tmp_path):
        """Test main function with failed steps."""
        with patch('code.042_run_performance_harness.ensure_directories'), \
             patch('code.042_run_performance_harness.run_full_pipeline_profiling') as mock_run, \
             patch('code.042_run_performance_harness.save_results'), \
             patch('code.042_run_performance_harness.sys.exit') as mock_exit:
            
            mock_run.return_value = {
                "aggregate": {
                    "failed_steps": 1
                }
            }
            
            performance_harness.main()
            
            mock_exit.assert_called_once_with(1)
