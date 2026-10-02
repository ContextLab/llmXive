import pytest
import json
import os
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils import get_data_processed_path, get_data_qc_path
from code import gap_report

def test_generate_gap_report_creates_file():
    """Test that generate_gap_report creates the expected JSON file."""
    # Setup
    processed_dir = get_data_processed_path()
    processed_dir.mkdir(parents=True, exist_ok=True)
    report_file = processed_dir / "data_gap_report.json"
    
    # Remove file if it exists
    if report_file.exists():
        report_file.unlink()
    
    # Call function
    gap_report.generate_gap_report(reason="Test reason")
    
    # Assertions
    assert report_file.exists(), "Gap report file was not created."
    
    with open(report_file, 'r') as f:
        data = json.load(f)
    
    assert data['failure_reason'] == "Test reason"
    assert data['report_type'] == "Data Gap Report (FR-008)"
    assert 'associational' in data['framing'].lower()
    
    # Cleanup
    report_file.unlink()

def test_trigger_meta_analysis_logs():
    """Test that trigger_meta_analysis logs correctly."""
    # This is a simple check that the function runs without error
    try:
        gap_report.trigger_meta_analysis()
    except Exception as e:
        pytest.fail(f"trigger_meta_analysis raised an exception: {e}")