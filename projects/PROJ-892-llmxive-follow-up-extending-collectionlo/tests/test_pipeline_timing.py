"""
Unit tests for the pipeline timing script (T031).
Tests the timing logic and report generation without running the full pipeline.
"""
import os
import sys
import json
import time
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from run_pipeline_timing import (
    ensure_dirs,
    generate_ci_report,
    MAX_DURATION_SECONDS
)

class TestEnsureDirs:
    def test_creates_data_directory(self, tmp_path):
        """Test that ensure_dirs creates the data directory if it doesn't exist."""
        data_dir = tmp_path / "data"
        with patch('run_pipeline_timing.PROJECT_ROOT', tmp_path):
            with patch('run_pipeline_timing.DATA_DIR', data_dir):
                ensure_dirs()
                assert data_dir.exists()
                assert data_dir.is_dir()

    def test_does_not_fail_if_directory_exists(self, tmp_path):
        """Test that ensure_dirs doesn't fail if directory already exists."""
        data_dir = tmp_path / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        with patch('run_pipeline_timing.PROJECT_ROOT', tmp_path):
            with patch('run_pipeline_timing.DATA_DIR', data_dir):
                ensure_dirs()
                assert data_dir.exists()

class TestGenerateCiReport:
    def test_creates_valid_json_report(self, tmp_path):
        """Test that generate_ci_report creates a valid JSON file."""
        report_path = tmp_path / "ci_report.json"
        
        with patch('run_pipeline_timing.DATA_DIR', tmp_path):
            with patch('run_pipeline_timing.CI_REPORT_PATH', report_path):
                report = generate_ci_report(True, 100.5, None)
                
                assert report_path.exists()
                assert report_path.is_file()
                
                with open(report_path, 'r') as f:
                    loaded_report = json.load(f)
                
                assert loaded_report['status'] == 'success'
                assert loaded_report['duration_seconds'] == 100.5
                assert loaded_report['within_time_limit'] is True
                assert loaded_report['task_id'] == 'T031'
                assert loaded_report['runner'] == 'ubuntu-latest'

    def test_reports_failure_correctly(self, tmp_path):
        """Test that failure status is correctly reported."""
        with patch('run_pipeline_timing.DATA_DIR', tmp_path):
            with patch('run_pipeline_timing.CI_REPORT_PATH', tmp_path / "ci_report.json"):
                report = generate_ci_report(False, 100.0, "Test error")
                
                assert report['status'] == 'failed'
                assert report['message'] == 'Test error'
                assert report['within_time_limit'] is True  # 100s < 6h

    def test_reports_timeout_correctly(self, tmp_path):
        """Test that timeout is correctly reported when duration exceeds limit."""
        with patch('run_pipeline_timing.DATA_DIR', tmp_path):
            with patch('run_pipeline_timing.CI_REPORT_PATH', tmp_path / "ci_report.json"):
                # 7 hours = 25200 seconds
                report = generate_ci_report(True, 25200.0, None)
                
                assert report['within_time_limit'] is False
                assert report['message'] == 'Pipeline completed within time limit'

    def test_contains_required_fields(self, tmp_path):
        """Test that the report contains all required fields."""
        with patch('run_pipeline_timing.DATA_DIR', tmp_path):
            with patch('run_pipeline_timing.CI_REPORT_PATH', tmp_path / "ci_report.json"):
                report = generate_ci_report(True, 100.0, None)
                
                required_fields = [
                    'timestamp', 'task_id', 'status', 'duration_seconds',
                    'max_allowed_seconds', 'within_time_limit', 'runner', 'message'
                ]
                
                for field in required_fields:
                    assert field in report, f"Missing required field: {field}"

class TestConstants:
    def test_max_duration_is_six_hours(self):
        """Test that MAX_DURATION_SECONDS is exactly 6 hours."""
        assert MAX_DURATION_SECONDS == 6 * 3600
        assert MAX_DURATION_SECONDS == 21600

class TestIntegration:
    def test_full_workflow(self, tmp_path):
        """Test the complete workflow of generating a CI report."""
        # Setup
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        report_path = data_dir / "ci_report.json"
        
        with patch('run_pipeline_timing.PROJECT_ROOT', tmp_path):
            with patch('run_pipeline_timing.DATA_DIR', data_dir):
                with patch('run_pipeline_timing.CI_REPORT_PATH', report_path):
                    # Generate report
                    generate_ci_report(True, 300.0, None)
                    
                    # Verify file exists and is valid JSON
                    assert report_path.exists()
                    with open(report_path, 'r') as f:
                        content = json.load(f)
                    
                    # Verify content
                    assert content['status'] == 'success'
                    assert content['duration_seconds'] == 300.0
                    assert content['within_time_limit'] is True
                    assert content['task_id'] == 'T031'

if __name__ == '__main__':
    pytest.main([__file__, '-v'])