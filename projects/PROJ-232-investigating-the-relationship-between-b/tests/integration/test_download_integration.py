"""
Integration test for T011b: Simulating a scenario where BMRQ is missing.
This test verifies that the pipeline exits with code 1 and generates the report.
"""
import pytest
import pandas as pd
from pathlib import Path
import sys
import os
import tempfile
import shutil

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from code.src.data.download import download_behavioral_data, REPORTS_DIR, GAP_REPORT_FILENAME

@pytest.fixture
def mock_data_dir():
    """Create a temporary directory with a mock behavioral CSV missing BMRQ."""
    temp_dir = tempfile.mkdtemp()
    data_dir = Path(temp_dir)
    
    # Create a CSV without BMRQ
    df = pd.DataFrame({
        "subject_id": [1, 2, 3],
        "age": [20, 21, 22],
        "sex": ["M", "F", "M"]
    })
    csv_path = data_dir / "behav.csv"
    df.to_csv(csv_path, index=False)
    
    return data_dir

@pytest.fixture
def mock_reports_dir():
    """Create a temporary directory for reports."""
    temp_dir = tempfile.mkdtemp()
    reports_dir = Path(temp_dir)
    return reports_dir

def test_missing_bmrq_triggers_exit_and_report(mock_data_dir, mock_reports_dir, monkeypatch):
    """
    Test that if BMRQ is missing, the function generates a report and exits with code 1.
    """
    # Temporarily override the REPORTS_DIR constant in the download module
    import code.src.data.download as download_module
    original_reports_dir = download_module.REPORTS_DIR
    download_module.REPORTS_DIR = mock_reports_dir
    
    # We need to patch the function to use our mock data dir
    # Since download_behavioral_data expects a dataset_id and output_dir,
    # and it tries to read from output_dir / "behav.csv", we can pass our mock dir.
    
    # However, the function also tries to download if the file doesn't exist.
    # We created the file, so it should read it.
    
    # We need to catch the SystemExit
    with pytest.raises(SystemExit) as exc_info:
        # We pass the mock data dir as output_dir
        # The function will look for "behav.csv" in that dir
        download_behavioral_data("ds000233", mock_data_dir)
    
    assert exc_info.value.code == 1
    
    # Check that the report was generated
    report_path = mock_reports_dir / GAP_REPORT_FILENAME
    assert report_path.exists()
    
    content = report_path.read_text()
    assert "BMRQ_Total" in content
    assert "CRITICAL" in content
    
    # Restore original
    download_module.REPORTS_DIR = original_reports_dir

def test_present_bmrq_does_not_exit(mock_data_dir, monkeypatch):
    """
    Test that if BMRQ is present, the function does not exit and returns the DataFrame.
    """
    # Add BMRQ column to the mock data
    df = pd.read_csv(mock_data_dir / "behav.csv")
    df["BMRQ_Total"] = [10, 20, 30]
    df.to_csv(mock_data_dir / "behav.csv", index=False)
    
    # We need to patch the function to use our mock data dir
    # Since download_behavioral_data expects a dataset_id and output_dir,
    # and it tries to read from output_dir / "behav.csv", we can pass our mock dir.
    
    # We need to catch the SystemExit if it happens (it shouldn't)
    # But since we are not mocking the download part, it might fail if the file is not found.
    # But we created the file, so it should be fine.
    
    # We need to mock the download logic to avoid network calls
    # For this test, we assume the file exists and is read correctly.
    
    # Since we cannot easily mock the download part without changing the code,
    # we will assume the function works as expected if the file exists.
    
    # We will just check that it doesn't raise SystemExit
    try:
        result = download_behavioral_data("ds000233", mock_data_dir)
        assert result is not None
        assert "BMRQ_Total" in result.columns
    except SystemExit:
        pytest.fail("Function exited unexpectedly when BMRQ was present.")