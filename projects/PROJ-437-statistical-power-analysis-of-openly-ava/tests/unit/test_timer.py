"""
Unit tests for the timer module.
"""
import os
import time
import pytest
from pathlib import Path
from datetime import datetime

# Import the module under test
from utils.timer import (
    start_run,
    end_run,
    log_split,
    save_timing_report,
    save_timing_breakdown,
    _run_start_time,
    _split_times
)

@pytest.fixture(autouse=True)
def reset_timer_state():
    """Reset global timer state before each test."""
    global _run_start_time, _split_times
    _run_start_time = None
    _split_times = []
    yield
    # Reset after test
    _run_start_time = None
    _split_times = []

class TestStartRun:
    def test_start_run_initializes_time(self):
        start_run()
        assert _run_start_time is not None
        assert _run_start_time > 0

    def test_start_run_resets_splits(self):
        global _split_times
        _split_times = [{"dummy": "data"}]  # Pre-populate
        start_run()
        assert _split_times == []

class TestLogSplit:
    def test_log_split_requires_start_run(self):
        with pytest.raises(RuntimeError, match="start_run"):
            log_split("test_split")

    def test_log_split_records_data(self):
        start_run()
        log_split("preprocessing", {"kernel": "4mm"})
        
        assert len(_split_times) == 1
        assert _split_times[0]["split_name"] == "preprocessing"
        assert _split_times[0]["metadata"]["kernel"] == "4mm"
        assert "elapsed_seconds" in _split_times[0]
        assert "timestamp" in _split_times[0]

    def test_log_split_handles_missing_metadata(self):
        start_run()
        log_split("download")
        
        assert _split_times[0]["metadata"] == {}

class TestEndRun:
    def test_end_run_requires_start_run(self):
        with pytest.raises(RuntimeError, match="start_run"):
            end_run()

    def test_end_run_clears_start_time(self):
        global _run_start_time
        start_run()
        initial_time = _run_start_time
        end_run()
        assert _run_start_time is None

class TestSaveTimingReport:
    def test_save_report_requires_end_run(self):
        start_run()
        log_split("test")
        with pytest.raises(RuntimeError, match="end_run"):
            save_timing_report()

    def test_save_report_creates_file(self, tmp_path):
        start_run()
        log_split("stage1")
        end_run()
        
        output_path = str(tmp_path / "timing_report.md")
        save_timing_report(output_path)
        
        assert Path(output_path).exists()
        
        with open(output_path, 'r') as f:
            content = f.read()
            assert "# Pipeline Timing Report" in content
            assert "Total Duration" in content
            assert "Execution Budget" in content

    def test_save_report_fails_if_no_splits(self):
        start_run()
        end_run()
        
        with pytest.raises(RuntimeError, match="No timing splits"):
            save_timing_report()

class TestSaveTimingBreakdown:
    def test_save_csv_requires_end_run(self):
        start_run()
        log_split("test")
        with pytest.raises(RuntimeError, match="end_run"):
            save_timing_breakdown()

    def test_save_csv_creates_file(self, tmp_path):
        start_run()
        log_split("stage1", {"param": "value"})
        end_run()
        
        output_path = str(tmp_path / "timing_breakdown.csv")
        save_timing_breakdown(output_path)
        
        assert Path(output_path).exists()
        
        with open(output_path, 'r') as f:
            content = f.read()
            assert "split_name" in content
            assert "elapsed_seconds" in content
            assert "stage1" in content

class TestIntegration:
    def test_full_workflow(self, tmp_path):
        # Start
        start_run()
        
        # Log splits
        log_split("download", {"dataset": "ds000030"})
        time.sleep(0.05)
        log_split("preprocess", {"kernel": "4mm"})
        time.sleep(0.05)
        log_split("analysis")
        
        # End
        end_run()
        
        # Save
        report_path = str(tmp_path / "report.md")
        csv_path = str(tmp_path / "breakdown.csv")
        
        save_timing_report(report_path)
        save_timing_breakdown(csv_path)
        
        # Verify
        assert Path(report_path).exists()
        assert Path(csv_path).exists()
        
        # Check content
        with open(report_path) as f:
            report = f.read()
            assert "ds000030" in report
            assert "4mm" in report
        
        with open(csv_path) as f:
            csv_content = f.read()
            assert "download" in csv_content
            assert "preprocess" in csv_content
            assert "analysis" in csv_content
