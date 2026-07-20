"""
Integration tests for T048b: Real Data Validation Script.
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Adjust import path for testing
import sys
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "code"))

from validate_real_data import run_validation_pipeline, save_json_file, REPORT_PATH


class TestValidateRealData:
    
    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary data directory structure."""
        temp_dir = tempfile.mkdtemp()
        raw_dir = Path(temp_dir) / "data" / "raw"
        results_dir = Path(temp_dir) / "data" / "results"
        raw_dir.mkdir(parents=True)
        results_dir.mkdir(parents=True)
        
        # Mock the global paths in the module
        # We need to patch the module-level constants or pass paths explicitly
        # Since the script uses global constants, we will test the logic directly
        # and verify the report structure.
        
        yield {
            "temp_dir": temp_dir,
            "raw_dir": raw_dir,
            "results_dir": results_dir
        }
        
        shutil.rmtree(temp_dir)

    def test_simulated_failure_mode(self):
        """Test that simulated_failure mode produces the expected error report."""
        report = run_validation_pipeline(mode="simulated_failure")
        
        assert report["status"] == "failed_no_real_data"
        assert report["attempting_real_data"] is True
        assert len(report["errors"]) > 0
        
        error = report["errors"][0]
        assert error["type"] == "MissingDataError"
        assert "prevent fabrication" in error["message"]

    def test_real_data_mode_no_files(self, temp_data_dir):
        """Test real_data mode when no files exist in data/raw."""
        # We need to simulate the environment where data/raw is empty
        # Since run_validation_pipeline uses global constants, we test the logic
        # by ensuring the function handles the empty directory case correctly.
        # In a real integration test, we would mock the file system or the path.
        
        # For this test, we assume the function logic is correct based on the code review
        # and verify the structure of a hypothetical empty state.
        # The actual check for files happens inside the function.
        
        # We can't easily change the global PROJECT_ROOT in the module without monkeypatching
        # So we verify the logic by checking the code structure or mocking.
        # Let's verify the error handling path directly.
        
        # Mocking the file check
        import validate_real_data as vrd
        original_glob = vrd.Path.glob
        
        def mock_glob(self, pattern):
            return [] # Simulate no files found
        
        vrd.Path.glob = mock_glob
        
        try:
            report = run_validation_pipeline(mode="real_data")
            assert report["status"] == "failed_no_real_data"
            assert any("No real data files found" in e["message"] for e in report["errors"])
        finally:
            vrd.Path.glob = original_glob

    def test_report_structure(self):
        """Verify the report contains all required keys."""
        report = run_validation_pipeline(mode="simulated_failure")
        
        required_keys = [
            "timestamp", "mode", "status", "errors", "warnings",
            "metrics", "execution_time_seconds", "attempting_real_data",
            "data_source", "data_path", "sample_size", 
            "variables_loaded", "missing_variables"
        ]
        
        for key in required_keys:
            assert key in report, f"Missing required key: {key}"

    def test_output_file_creation(self, temp_data_dir):
        """Test that the report is saved to the correct location."""
        # Temporarily override REPORT_PATH for this test
        import validate_real_data as vrd
        original_path = vrd.REPORT_PATH
        test_path = Path(temp_data_dir["results_dir"]) / "test_report.json"
        vrd.REPORT_PATH = test_path
        
        try:
            run_validation_pipeline(mode="simulated_failure")
            
            assert test_path.exists(), "Report file was not created"
            
            with open(test_path, 'r') as f:
                saved_report = json.load(f)
            
            assert saved_report["status"] == "failed_no_real_data"
        finally:
            vrd.REPORT_PATH = original_path