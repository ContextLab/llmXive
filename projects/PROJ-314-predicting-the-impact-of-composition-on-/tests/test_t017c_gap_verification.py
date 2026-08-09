"""
Unit test for T017c: Execute & Verify Data Gap Report.

This test ensures that:
1. A dataset with < 30 valid entries triggers the gap protocol.
2. The report is generated with correct structure.
3. The process halts correctly.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import pytest

# Add code to path
code_dir = Path(__file__).parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from ingestion import generate_data_availability_report, validate_data_gap

class TestDataGapProtocol:
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup test environment and cleanup after test."""
        # Ensure directories exist
        Path("data/reports").mkdir(parents=True, exist_ok=True)
        Path("data/raw").mkdir(parents=True, exist_ok=True)
        
        # Clean up any existing report
        report_path = Path("data/reports/data_availability_report.json")
        if report_path.exists():
            report_path.unlink()
            
        yield
        
        # Cleanup
        if report_path.exists():
            report_path.unlink()

    def test_generate_data_availability_report_creates_file(self):
        """Test that the report generation function creates the file with correct fields."""
        test_data = {
            'total_sources': 5,
            'valid_entries': 5,
            'reason_code': 'N_LESS_THAN_30',
            'timestamp': '2023-10-01T00:00:00'
        }
        
        # Call the function
        generate_data_availability_report(
            total_sources=test_data['total_sources'],
            valid_entries=test_data['valid_entries'],
            reason_code=test_data['reason_code']
        )
        
        # Verify file exists
        report_path = Path("data/reports/data_availability_report.json")
        assert report_path.exists(), "Report file was not created."
        
        # Verify content
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        assert report['total_sources'] == test_data['total_sources']
        assert report['valid_entries'] == test_data['valid_entries']
        assert report['reason_code'] == test_data['reason_code']
        assert 'timestamp' in report

    def test_validate_data_gap_halts_on_small_dataset(self):
        """Test that validate_data_gap halts with exit code 1 when N < 30."""
        # Create a small dataframe
        df_small = pd.DataFrame({
            'composition': ['Al2O3'] * 10,
            'weibull_modulus': [10.0] * 10,
            'sample_count': [30] * 10,
            'sintering_temp': [1500] * 10,
            'primary_anion_cation_group': ['O-Al'] * 10
        })
        
        # We expect a SystemExit with code 1
        with pytest.raises(SystemExit) as exc_info:
            validate_data_gap(df_small, source_id="test_unit")
        
        assert exc_info.value.code == 1, f"Expected exit code 1, got {exc_info.value.code}"
        
        # Verify the report was created during the halt
        report_path = Path("data/reports/data_availability_report.json")
        assert report_path.exists(), "Report file was not created during halt."
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        assert report['valid_entries'] == 10
        assert report['total_sources'] == 10