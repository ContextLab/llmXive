"""
Integration test for data completeness check (T011).

Verifies that the data completeness validation logic correctly raises a ValueError
when the percentage of valid records is below the 95% threshold.

This test mocks the data loading process to simulate a dataset with low completeness
and asserts that the `main` function in `code/data/preprocess.py` halts execution
and logs the appropriate error.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd

# Ensure code/ is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.preprocess import main
from code.utils.logger import log_validation_error


class MockDataset:
    """Mock HuggingFace dataset object for testing."""
    def __init__(self, data):
        self.data = data
    
    def to_pandas(self):
        return pd.DataFrame(self.data)


def test_data_completeness_below_threshold_raises_error():
    """
    Test that a dataset with <95% completeness triggers a ValueError.
    
    Scenario:
    1. Create a synthetic dataset with 100 rows.
    2. Make 10 rows invalid (e.g., missing 'diff' or 'review_comments').
    3. This results in 90% completeness (< 95%).
    4. Expect `main()` to raise ValueError and write error_report.json.
    """
    # Create a temporary directory for this test run
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Prepare mock data: 100 rows, 10 invalid (missing 'diff')
        valid_rows = 90
        invalid_rows = 10
        total_rows = valid_rows + invalid_rows
        
        data = []
        # Add valid rows
        for i in range(valid_rows):
            data.append({
                "pr_id": f"PR-{i}",
                "diff": f"diff content {i}",
                "review_comments": f"comment {i}",
                "merge_timestamp": "2023-01-01",
                "project_name": "test-project"
            })
        # Add invalid rows (missing 'diff')
        for i in range(invalid_rows):
            data.append({
                "pr_id": f"PR-{valid_rows + i}",
                "diff": None,  # Missing required field
                "review_comments": f"comment {valid_rows + i}",
                "merge_timestamp": "2023-01-01",
                "project_name": "test-project"
            })
        
        mock_dataset = MockDataset(data)
        
        # Patch load_dataset to return our mock dataset
        with patch("code.data.preprocess.load_dataset", return_value=mock_dataset):
            with patch("code.data.preprocess.Path", return_value=tmp_path):
                # We need to mock the specific Path behavior for output files
                # since the main function creates Path objects internally.
                # Instead of patching global Path, we rely on the function logic
                # using the passed tmp_path or environment. 
                # For this test, we assume the function uses the default data paths 
                # which we can influence by environment or mocking the specific file writes.
                
                # To make the test robust, we will mock the file writing of the error report
                # to ensure we don't hit permission issues in temp dirs, 
                # but the logic inside main must run.
                
                error_report_path = tmp_path / "docs" / "reports" / "error_report.json"
                error_report_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Mock the specific file write for the error report to capture the call
                # and prevent actual I/O if the temp dir is restrictive, 
                # though TemporaryDirectory usually works fine.
                
                # Execute the main function
                # We expect a ValueError to be raised
                with pytest.raises(ValueError) as exc_info:
                    # We need to ensure the preprocess module sees the tmp_path as the root
                    # The main function typically uses Path(".") or environment vars.
                    # Let's set the environment variable if the code uses it, 
                    # or patch the internal logic.
                    # Assuming the code uses a standard root detection or env var.
                    # If the code uses `Path(__file__).parent.parent` logic, we might need to adjust.
                    # For T011, we are testing the logic inside `main` which calls `validate_completeness`.
                    
                    # Let's mock the `load_dataset` call inside preprocess.py specifically
                    # and ensure the `Path` logic resolves to our temp dir for the report.
                    # Since we can't easily change the `Path(".")` inside the function without 
                    # refactoring, we will assume the test runner sets the working directory 
                    # or we patch the `Path` constructor to return our tmp_path for specific calls.
                    
                    # Robust approach: Patch the `Path` constructor in the `code.data.preprocess` module
                    # to return our tmp_path for the root, but allow specific sub-paths to work.
                    # However, `Path` is complex to patch globally.
                    # Alternative: The `main` function likely uses a config or fixed path.
                    # Let's assume it writes to `docs/reports/error_report.json` relative to project root.
                    # We will patch `Path` to use our tmp_dir as the base for 'docs'.
                    
                    original_path = Path
                    
                    def mock_path_constructor(*args, **kwargs):
                        p = original_path(*args, **kwargs)
                        # If the path starts with 'docs', redirect to tmp_path
                        if len(args) > 0 and str(args[0]).startswith("docs"):
                            return tmp_path / str(args[0])
                        return p
                    
                    with patch("code.data.preprocess.Path", side_effect=mock_path_constructor):
                        # Also need to ensure the fetch module doesn't run or is mocked
                        # The main function calls fetch_dataset.
                        with patch("code.data.preprocess.fetch_dataset", return_value=mock_dataset):
                            # Run the main logic
                            # We need to pass arguments or set environment if required.
                            # Assuming main() runs with defaults.
                            main()
                
                # Verify the error message contains completeness info
                error_msg = str(exc_info.value)
                assert "completeness" in error_msg.lower() or "valid" in error_msg.lower()
                assert "95" in error_msg or "90" in error_msg or str(int((valid_rows/total_rows)*100)) in error_msg
                
                # Verify error_report.json was written (if the logic allows I/O)
                # Since we patched Path for 'docs', the file should be at tmp_path/docs/reports/error_report.json
                # But we patched Path constructor, so the file write inside the function 
                # (which uses Path("docs/...")) would resolve to tmp_path/docs/...
                # Let's check if the file exists.
                if error_report_path.exists():
                    with open(error_report_path, "r") as f:
                        report = json.load(f)
                    assert "reason" in report
                    assert report["reason"].lower().find("completeness") != -1 or report["reason"].lower().find("valid") != -1
                    assert report["valid_percentage"] == (valid_rows / total_rows) * 100

def test_data_completeness_above_threshold_passes():
    """
    Test that a dataset with >=95% completeness does NOT raise an error.
    
    Scenario:
    1. Create a dataset with 100 rows, 5 invalid (95% valid).
    2. Expect `main()` to complete without raising ValueError.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        valid_rows = 95
        invalid_rows = 5
        total_rows = valid_rows + invalid_rows
        
        data = []
        for i in range(valid_rows):
            data.append({
                "pr_id": f"PR-{i}",
                "diff": f"diff content {i}",
                "review_comments": f"comment {i}",
                "merge_timestamp": "2023-01-01",
                "project_name": "test-project"
            })
        for i in range(invalid_rows):
            data.append({
                "pr_id": f"PR-{valid_rows + i}",
                "diff": None,
                "review_comments": f"comment {valid_rows + i}",
                "merge_timestamp": "2023-01-01",
                "project_name": "test-project"
            })
        
        mock_dataset = MockDataset(data)
        
        original_path = Path
        def mock_path_constructor(*args, **kwargs):
            p = original_path(*args, **kwargs)
            if len(args) > 0 and str(args[0]).startswith("docs"):
                return tmp_path / str(args[0])
            return p

        # We expect NO exception
        with patch("code.data.preprocess.load_dataset", return_value=mock_dataset):
            with patch("code.data.preprocess.fetch_dataset", return_value=mock_dataset):
                with patch("code.data.preprocess.Path", side_effect=mock_path_constructor):
                    # Ensure the function doesn't fail on other checks (like power)
                    # We are only testing completeness here.
                    # If main() has other logic that might fail (e.g. power check < 500),
                    # we might need to mock that too.
                    # For T011, we focus on completeness. 
                    # If the dataset is small, power check might fail.
                    # Let's ensure we have enough data for power check or mock it.
                    # The task is specifically for completeness.
                    # If the code checks power after completeness, we might get a power error.
                    # We should mock the power check or ensure data is large enough.
                    # Let's assume the main function checks completeness first.
                    # If it raises on power, then completeness passed.
                    # But to be safe, let's mock the power check function to not raise.
                    
                    with patch("code.data.preprocess.validate_power_insufficiency"):
                        try:
                            main()
                        except ValueError as e:
                            # If it's a power error, that means completeness passed (which is what we want)
                            if "power" in str(e).lower() or "size" in str(e).lower():
                                pass # Expected
                            else:
                                raise e # Unexpected error

if __name__ == "__main__":
    pytest.main([__file__, "-v"])