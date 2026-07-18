import pytest
import pandas as pd
from pathlib import Path
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingest import generate_insufficiency_report, run_data_availability_gate

class TestDataAvailabilityGate:
    def test_insufficient_data_small_n(self, tmp_path):
        """
        Test that the Data Availability Gate fails when N < 30.
        """
        # Create a small dataset
        data = {
            'smiles': ['CCO', 'CCO', 'CCO'],
            'half_life': [10.0, 20.0, 30.0]
        }
        df = pd.DataFrame(data)
        
        # Temporarily override the output path for the report
        report_path = str(tmp_path / "data_insufficiency_report.md")
        
        # Mock the function to use our temp path
        # We need to patch the function or the internal call
        # Since run_data_availability_gate calls generate_insufficiency_report with a hardcoded path in the original,
        # we will test the logic by checking the report generation directly or by patching.
        
        # Let's test the logic directly by calling the helper
        from ingest import check_degradation_columns
        
        # Mock the check to return True so we test the N < 30 logic
        # But run_data_availability_gate is the main function.
        # We will patch the generate_insufficiency_report to capture the call.
        
        import ingest
        original_report_func = ingest.generate_insufficiency_report
        
        captured_reason = None
        captured_count = None
        
        def mock_report(reason, count, path):
            nonlocal captured_reason, captured_count
            captured_reason = reason
            captured_count = count
            Path(path).write_text(f"Report: {reason} - {count}")
        
        ingest.generate_insufficiency_report = mock_report
        
        try:
            result = run_data_availability_gate(df)
            assert result is False, "Gate should return False for N < 30"
            assert captured_count == 3, f"Expected count 3, got {captured_count}"
            assert "Insufficient" in captured_reason or "30" in captured_reason, f"Reason should mention insufficiency: {captured_reason}"
            
            # Verify report file exists
            assert Path("data/data_insufficiency_report.md").exists() or \
                   Path(tmp_path / "data_insufficiency_report.md").exists(), "Report file should be created"
        finally:
            ingest.generate_insufficiency_report = original_report_func

    def test_sufficient_data(self):
        """
        Test that the Data Availability Gate passes when N >= 30.
        """
        # Create a dataset with 35 rows
        data = {
            'smiles': ['CCO'] * 35,
            'half_life': [float(i) for i in range(35)]
        }
        df = pd.DataFrame(data)
        
        result = run_data_availability_gate(df)
        assert result is True, "Gate should return True for N >= 30"

    def test_missing_degradation_columns(self):
        """
        Test that the Data Availability Gate fails when degradation columns are missing.
        """
        data = {
            'smiles': ['CCO', 'CCO'],
            'other_col': [1, 2]
        }
        df = pd.DataFrame(data)
        
        import ingest
        original_report_func = ingest.generate_insufficiency_report
        
        captured_reason = None
        
        def mock_report(reason, count, path):
            nonlocal captured_reason
            captured_reason = reason
        
        ingest.generate_insufficiency_report = mock_report
        
        try:
            result = run_data_availability_gate(df)
            assert result is False, "Gate should return False when columns missing"
            assert "Missing degradation" in captured_reason or "degradation" in captured_reason.lower()
        finally:
            ingest.generate_insufficiency_report = original_report_func