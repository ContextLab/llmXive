"""
Integration test for Task T036: Sweep timing verification.

Verifies that the timing script runs and produces the expected log file.
Note: This test does NOT run the full 6-hour sweep (too slow for CI).
Instead, it verifies the script structure and that it can be invoked.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import time

import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from analysis.sweep_timing import main as timing_main, TIME_BUDGET_SECONDS


class TestSweepTiming:
    """Tests for the sweep timing verification script."""

    def test_timing_script_executes(self, tmp_path):
        """Test that the timing script can be executed without import errors."""
        # Mock the threshold_sweep.main to return immediately
        with patch('analysis.sweep_timing.run_threshold_sweep') as mock_sweep:
            mock_sweep.return_value = None
            
            # Change to temp directory to avoid polluting project state
            original_cwd = os.getcwd()
            os.chdir(tmp_path)
            
            try:
                # Mock get_project_paths to use temp directory
                with patch('analysis.sweep_timing.get_project_paths') as mock_paths:
                    mock_state_dir = tmp_path / "state"
                    mock_state_dir.mkdir(parents=True, exist_ok=True)
                    
                    mock_paths.return_value = {
                        "root": tmp_path,
                        "state": mock_state_dir,
                        "data": tmp_path / "data",
                        "code": tmp_path / "code",
                        "tests": tmp_path / "tests",
                        "figures": tmp_path / "figures"
                    }
                    
                    # Ensure directories exist
                    (tmp_path / "state").mkdir(exist_ok=True)
                    (tmp_path / "data").mkdir(exist_ok=True)
                    (tmp_path / "data" / "raw").mkdir(exist_ok=True)
                    (tmp_path / "data" / "processed").mkdir(exist_ok=True)
                    
                    # Run the timing main
                    timing_main()
                    
                    # Verify log file was created
                    log_file = tmp_path / "state" / "sweep_timing.log"
                    assert log_file.exists(), "sweep_timing.log should be created"
                    
                    # Verify summary JSON was created
                    summary_file = tmp_path / "state" / "sweep_timing_summary.json"
                    assert summary_file.exists(), "sweep_timing_summary.json should be created"
                    
                    # Verify summary content
                    with open(summary_file) as f:
                        summary = json.load(f)
                    
                    assert summary["task_id"] == "T036"
                    assert "duration_seconds" in summary
                    assert "within_budget" in summary
                    assert summary["status"] == "passed"
                    
            finally:
                os.chdir(original_cwd)

    def test_time_budget_constant(self):
        """Test that the time budget is set to 6 hours."""
        assert TIME_BUDGET_SECONDS == 6 * 60 * 60, "Time budget should be 6 hours in seconds"

    def test_timeout_scenario(self, tmp_path):
        """Test that the script correctly reports failure if sweep exceeds budget."""
        # Mock the threshold_sweep to simulate a long-running process
        def slow_sweep():
            time.sleep(0.1)  # Simulate some work
            # We won't actually wait 6 hours, but we can mock the duration check
            pass

        with patch('analysis.sweep_timing.run_threshold_sweep', side_effect=slow_sweep):
            with patch('analysis.sweep_timing.get_project_paths') as mock_paths:
                mock_state_dir = tmp_path / "state"
                mock_state_dir.mkdir(parents=True, exist_ok=True)
                
                mock_paths.return_value = {
                    "root": tmp_path,
                    "state": mock_state_dir,
                    "data": tmp_path / "data",
                    "code": tmp_path / "code",
                    "tests": tmp_path / "tests",
                    "figures": tmp_path / "figures"
                }
                
                # Temporarily reduce budget for testing
                with patch('analysis.sweep_timing.TIME_BUDGET_SECONDS', 0.05):
                    # This should raise SystemExit with code 1
                    with pytest.raises(SystemExit) as exc_info:
                        timing_main()
                    
                    assert exc_info.value.code == 1
                    
                    # Verify log shows failure
                    log_file = tmp_path / "state" / "sweep_timing.log"
                    assert log_file.exists()
                    
                    with open(log_file) as f:
                        log_content = f.read()
                    
                    assert "FAILED" in log_content
                    assert "Exceeded 6-hour budget" in log_content