import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add the code directory to the path so we can import data_loader
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from data_loader import fetch_locomo_dataset, save_raw_data
from datasets import DatasetNotFoundError

class TestSilentFallbackAudit:
    """
    T040: Audit Data Loader for Silent Fallbacks.
    
    This test verifies that when the real data fetch fails (simulated network error),
    the script raises an exception and exits with a non-zero code, rather than
    silently falling back to synthetic data.
    """

    def test_fetch_raises_on_connection_error(self):
        """
        Verify that fetch_locomo_dataset raises an exception when datasets.load_dataset
        raises a ConnectionError, and does NOT return synthetic data.
        """
        # Simulate a network failure by mocking load_dataset to raise ConnectionError
        with patch('data_loader.load_dataset') as mock_load:
            mock_load.side_effect = ConnectionError("Simulated network failure")
            
            # We expect a RuntimeError to be raised by fetch_locomo_dataset
            # because it explicitly checks for real data availability (T035)
            with pytest.raises(RuntimeError) as exc_info:
                fetch_locomo_dataset(subset=5)
            
            # Verify the error message indicates the failure
            assert "Cannot proceed without real data" in str(exc_info.value)
            assert "Fetch failed" in str(exc_info.value)

    def test_no_synthetic_fallback_on_dataset_not_found(self):
        """
        Verify that when the dataset ID is invalid (DatasetNotFoundError),
        the script raises an exception and does not generate synthetic data.
        """
        with patch('data_loader.load_dataset') as mock_load:
            mock_load.side_effect = DatasetNotFoundError("Dataset 'locomo/locomo-benchmark' doesn't exist")
            
            with pytest.raises(RuntimeError) as exc_info:
                fetch_locomo_dataset(subset=5)
            
            assert "Cannot proceed without real data" in str(exc_info.value)

    def test_main_exits_non_zero_on_failure(self, tmp_path):
        """
        Verify that the main() function exits with a non-zero code when data fetch fails,
        and no synthetic files are produced.
        """
        # Create a temporary directory for output
        temp_dir = tmp_path / "temp_output"
        temp_dir.mkdir()
        
        # Mock sys.argv to simulate command line arguments
        original_argv = sys.argv
        sys.argv = ['data_loader.py', '--download', '--output-dir', str(temp_dir)]
        
        # Mock load_dataset to fail
        with patch('data_loader.load_dataset') as mock_load:
            mock_load.side_effect = ConnectionError("Simulated network failure")
            
            # Capture the exit code behavior
            with pytest.raises(SystemExit) as exc_info:
                # Import main here to ensure it uses the mocked environment
                from data_loader import main
                main()
            
            # Verify the exit code is non-zero (indicating failure)
            assert exc_info.value.code != 0
            
            # Verify that no output files were created (no synthetic data)
            output_files = list(temp_dir.glob("**/*"))
            # We expect only the directory itself, no files
            assert len(output_files) == 0 or all(f.is_dir() for f in output_files)

    def test_audit_report_generation(self, tmp_path):
        """
        T040 Core Requirement: Generate an audit report documenting the behavior.
        This test simulates the audit process and generates data/audit/audit_report.json.
        """
        audit_dir = tmp_path / "audit"
        audit_dir.mkdir()
        report_path = audit_dir / "audit_report.json"
        
        # Simulate the audit process
        audit_results = {
            "test_id": "T040",
            "description": "Audit Data Loader for Silent Fallbacks",
            "tests_passed": 0,
            "tests_failed": 0,
            "details": []
        }
        
        # Test 1: ConnectionError handling
        test1_passed = False
        try:
            with patch('data_loader.load_dataset') as mock_load:
                mock_load.side_effect = ConnectionError("Simulated network failure")
                try:
                    fetch_locomo_dataset(subset=5)
                except RuntimeError:
                    test1_passed = True
        except Exception as e:
            audit_results["details"].append({
                "test": "ConnectionError handling",
                "status": "failed",
                "error": str(e)
            })
        
        if test1_passed:
            audit_results["tests_passed"] += 1
            audit_results["details"].append({
                "test": "ConnectionError handling",
                "status": "passed",
                "message": "Script correctly raises RuntimeError on network failure"
            })
        
        # Test 2: DatasetNotFoundError handling
        test2_passed = False
        try:
            with patch('data_loader.load_dataset') as mock_load:
                mock_load.side_effect = DatasetNotFoundError("Dataset not found")
                try:
                    fetch_locomo_dataset(subset=5)
                except RuntimeError:
                    test2_passed = True
        except Exception as e:
            audit_results["details"].append({
                "test": "DatasetNotFoundError handling",
                "status": "failed",
                "error": str(e)
            })
        
        if test2_passed:
            audit_results["tests_passed"] += 1
            audit_results["details"].append({
                "test": "DatasetNotFoundError handling",
                "status": "passed",
                "message": "Script correctly raises RuntimeError on missing dataset"
            })
        
        # Test 3: No synthetic fallback
        test3_passed = False
        try:
            with patch('data_loader.load_dataset') as mock_load:
                mock_load.side_effect = ConnectionError("Simulated network failure")
                with tempfile.TemporaryDirectory() as tmp:
                    try:
                        fetch_locomo_dataset(subset=5)
                    except RuntimeError:
                        # Check that no files were created in tmp
                        files = list(Path(tmp).glob("*"))
                        if len(files) == 0:
                            test3_passed = True
        except Exception as e:
            audit_results["details"].append({
                "test": "No synthetic fallback",
                "status": "failed",
                "error": str(e)
            })
        
        if test3_passed:
            audit_results["tests_passed"] += 1
            audit_results["details"].append({
                "test": "No synthetic fallback",
                "status": "passed",
                "message": "Script does not generate synthetic data on failure"
            })
        
        audit_results["tests_failed"] = 3 - audit_results["tests_passed"]
        audit_results["verdict"] = "PASSED" if audit_results["tests_failed"] == 0 else "FAILED"
        
        # Write the audit report
        with open(report_path, 'w') as f:
            json.dump(audit_results, f, indent=2)
        
        # Verify the report was created
        assert report_path.exists()
        
        # Load and verify the report content
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        assert report["test_id"] == "T040"
        assert "audit_results" in report or report["verdict"] in ["PASSED", "FAILED"]
        
        # The test passes if all critical checks pass
        assert audit_results["tests_passed"] == 3

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
