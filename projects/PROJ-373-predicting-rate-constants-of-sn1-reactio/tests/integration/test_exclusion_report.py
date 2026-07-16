import os
import tempfile
import pandas as pd
import pytest

from data.exclusion_report import generate_exclusion_report, main
from config import ensure_dirs

class TestExclusionReport:
    def test_generate_empty_report(self, tmp_path):
        """Test generating an empty exclusion report."""
        output_path = str(tmp_path / "exclusion_report.csv")
        df = generate_exclusion_report(input_path=None, output_path=output_path)
        
        assert os.path.exists(output_path)
        assert df.empty
        assert list(df.columns) == ['row_index', 'reason', 'original_smiles']

    def test_generate_report_with_records(self, tmp_path):
        """Test generating a report with provided exclusion records."""
        output_path = str(tmp_path / "exclusion_report.csv")
        records = [
            {'row_index': 0, 'reason': 'parsing_error', 'original_smiles': 'invalid_smiles'},
            {'row_index': 5, 'reason': 'missing_rate', 'original_smiles': 'CCO'},
            {'row_index': 10, 'reason': 'invalid_substrate', 'original_smiles': 'CC(C)Cl'}
        ]
        
        df = generate_exclusion_report(
            input_path=None,
            output_path=output_path,
            exclusion_reasons=records
        )
        
        assert os.path.exists(output_path)
        assert len(df) == 3
        assert list(df.columns) == ['row_index', 'reason', 'original_smiles']
        assert df.iloc[0]['row_index'] == 0
        assert df.iloc[0]['reason'] == 'parsing_error'

    def test_generate_report_from_input_file(self, tmp_path):
        """Test generating a report from an input CSV file."""
        input_path = str(tmp_path / "input_exclusions.csv")
        output_path = str(tmp_path / "exclusion_report.csv")
        
        # Create input file
        input_df = pd.DataFrame([
            {'row_index': 1, 'reason': 'parsing_error', 'original_smiles': 'bad'},
            {'row_index': 2, 'reason': 'missing_rate', 'original_smiles': 'good'}
        ])
        input_df.to_csv(input_path, index=False)
        
        df = generate_exclusion_report(input_path=input_path, output_path=output_path)
        
        assert os.path.exists(output_path)
        assert len(df) == 2
        assert df.iloc[0]['row_index'] == 1

    def test_invalid_reason_ignored(self, tmp_path):
        """Test that invalid exclusion reasons are ignored."""
        output_path = str(tmp_path / "exclusion_report.csv")
        records = [
            {'row_index': 0, 'reason': 'invalid_reason', 'original_smiles': 'CCO'},
            {'row_index': 1, 'reason': 'parsing_error', 'original_smiles': 'CC(C)Cl'}
        ]
        
        df = generate_exclusion_report(
            input_path=None,
            output_path=output_path,
            exclusion_reasons=records
        )
        
        assert len(df) == 1
        assert df.iloc[0]['reason'] == 'parsing_error'

    def test_main_function(self, tmp_path):
        """Test the main function with arguments."""
        output_path = str(tmp_path / "exclusion_report.csv")
        
        # Mock sys.argv
        import sys
        original_argv = sys.argv
        sys.argv = ['test', '--output', output_path, '--log-level', 'WARNING']
        
        try:
            result = main()
            assert result == 0
            assert os.path.exists(output_path)
        finally:
            sys.argv = original_argv
