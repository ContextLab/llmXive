import pytest
import pandas as pd
import json
import os
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from ingestion import validate_data_gap, generate_data_availability_report, ensure_directories, MIN_VALID_ENTRIES

class TestDataGapValidation:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        # Setup temporary directories for testing
        self.tmp_raw = tmp_path / "data" / "raw"
        self.tmp_reports = tmp_path / "data" / "reports"
        self.tmp_raw.mkdir(parents=True)
        self.tmp_reports.mkdir(parents=True)
        
        # Temporarily override the constants for testing
        import ingestion
        self.original_raw_dir = ingestion.DATA_RAW_DIR
        self.original_reports_dir = ingestion.DATA_REPORTS_DIR
        self.original_min = ingestion.MIN_VALID_ENTRIES
        
        ingestion.DATA_RAW_DIR = self.tmp_raw
        ingestion.DATA_REPORTS_DIR = self.tmp_reports
        ingestion.MIN_VALID_ENTRIES = 5  # Lower threshold for test
        
        yield
        
        # Restore
        ingestion.DATA_RAW_DIR = self.original_raw_dir
        ingestion.DATA_REPORTS_DIR = self.original_reports_dir
        ingestion.MIN_VALID_ENTRIES = self.original_min

    def test_validate_data_gap_pass(self, tmp_path):
        # Create a CSV with enough rows
        df = pd.DataFrame({
            'composition': ['Al2O3'] * 10,
            'weibull_modulus': [5.0] * 10,
            'primary_anion_cation_group': ['O-Al'] * 10
        })
        csv_path = self.tmp_raw / "combined_raw.csv"
        df.to_csv(csv_path, index=False)
        
        result = validate_data_gap()
        assert result is True

    def test_validate_data_gap_fail(self, tmp_path):
        # Create a CSV with too few rows
        df = pd.DataFrame({
            'composition': ['Al2O3'] * 3,
            'weibull_modulus': [5.0] * 3,
            'primary_anion_cation_group': ['O-Al'] * 3
        })
        csv_path = self.tmp_raw / "combined_raw.csv"
        df.to_csv(csv_path, index=False)
        
        result = validate_data_gap()
        assert result is False
        
        # Check that the report was generated
        report_path = self.tmp_reports / "data_availability_report.json"
        assert report_path.exists()
        
        with open(report_path) as f:
            report = json.load(f)
        
        assert report['status'] == 'HALTED'
        assert report['total_entries'] == 3
        assert report['minimum_required'] == 5

    def test_generate_data_availability_report(self, tmp_path):
        count = 2
        reason = "Test reason"
        report = generate_data_availability_report(count, reason)
        
        assert report['total_entries'] == count
        assert report['reason'] == reason
        assert report['status'] == 'HALTED'
        
        report_path = self.tmp_reports / "data_availability_report.json"
        assert report_path.exists()
