import pytest
import pandas as pd
import json
from pathlib import Path
import sys
import os

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.ingestion import generate_data_availability_report, validate_data_gap

class TestDataAvailabilityReport:
    def test_generate_report_creates_file(self, tmp_path):
        """Test that generate_data_availability_report creates the expected file."""
        output_path = tmp_path / "data" / "reports" / "data_availability_report.json"
        
        report = generate_data_availability_report(
            total_sources=5,
            valid_entries=25,
            reason_code="N_LESS_THAN_30",
            output_path=str(output_path)
        )
        
        # Verify the file was created
        assert output_path.exists(), "Report file was not created"
        
        # Verify the content
        with open(output_path) as f:
            saved_report = json.load(f)
        
        assert saved_report["total_sources"] == 5
        assert saved_report["valid_entries"] == 25
        assert saved_report["reason_code"] == "N_LESS_THAN_30"
        assert "timestamp" in saved_report

    def test_generate_report_default_path(self, tmp_path):
        """Test that the default path is used when output_path is not specified."""
        # Change to tmp_path to avoid writing to actual data directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            os.makedirs("data/reports", exist_ok=True)
            
            report = generate_data_availability_report(
                total_sources=3,
                valid_entries=10,
                reason_code="N_LESS_THAN_30"
            )
            
            output_path = Path("data/reports/data_availability_report.json")
            assert output_path.exists(), "Report file was not created at default path"
        finally:
            os.chdir(original_cwd)

class TestDataGapValidation:
    def test_validate_data_gap_passes(self):
        """Test that validation passes when N >= 30."""
        df = pd.DataFrame({"col": range(35)})
        
        # Should not raise
        result = validate_data_gap(df, total_sources=1)
        assert len(result) == 35

    def test_validate_data_gap_halts(self, caplog):
        """Test that validation halts and generates report when N < 30."""
        df = pd.DataFrame({"col": range(25)})
        
        with pytest.raises(SystemExit) as exc_info:
            validate_data_gap(df, total_sources=2)
        
        assert exc_info.value.code == 1
        assert "Insufficient data" in caplog.text