import pytest
import os
import csv
import tempfile
from unittest.mock import patch, MagicMock
from io import StringIO

# Import the function under test
from sensitivity_analysis import (
    load_corrected_p_values,
    determine_significance,
    run_sensitivity_analysis
)

class TestDetermineSignificance:
    """Tests for the determine_significance function."""

    def test_significant_below_alpha(self):
        """Test that a p-value below alpha is significant."""
        assert determine_significance(0.005, 0.05) is True
        assert determine_significance(0.001, 0.01) is True

    def test_significant_at_alpha(self):
        """Test that a p-value exactly at alpha is significant."""
        assert determine_significance(0.05, 0.05) is True
        assert determine_significance(0.01, 0.01) is True

    def test_not_significant_above_alpha(self):
        """Test that a p-value above alpha is not significant."""
        assert determine_significance(0.06, 0.05) is False
        assert determine_significance(0.11, 0.10) is False

class TestLoadCorrectedPValues:
    """Tests for the load_corrected_p_values function."""

    def test_load_valid_csv(self, tmp_path):
        """Test loading a valid CSV file."""
        # Create a temporary CSV file
        csv_content = """query_id,metric,raw_p,corrected_p,is_significant
        1,NDCG@10,0.03,0.045,True
        2,NDCG@10,0.08,0.12,False
        3,MAP,0.02,0.035,True"""
        
        csv_file = tmp_path / "corrected_p_values.csv"
        csv_file.write_text(csv_content)
        
        # Load and verify
        data = load_corrected_p_values(str(csv_file))
        
        assert len(data) == 3
        assert data[0]['query_id'] == 1
        assert data[0]['metric'] == 'NDCG@10'
        assert data[0]['raw_p'] == 0.03
        assert data[0]['corrected_p'] == 0.045
        assert data[0]['is_significant'] is True
        
        assert data[1]['is_significant'] is False
        assert data[2]['metric'] == 'MAP'

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_corrected_p_values("non_existent_file.csv")

    def test_empty_csv(self, tmp_path):
        """Test loading an empty CSV (headers only)."""
        csv_content = "query_id,metric,raw_p,corrected_p,is_significant"
        
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text(csv_content)
        
        data = load_corrected_p_values(str(csv_file))
        assert len(data) == 0

class TestRunSensitivityAnalysis:
    """Tests for the run_sensitivity_analysis function."""

    def test_sensitivity_analysis_basic(self, tmp_path):
        """Test basic sensitivity analysis functionality."""
        # Create input data
        input_data = """query_id,metric,raw_p,corrected_p,is_significant
        1,NDCG@10,0.03,0.045,True
        2,NDCG@10,0.08,0.12,False
        3,MAP,0.02,0.035,True
        4,MAP,0.06,0.09,False"""
        
        input_file = tmp_path / "corrected_p_values.csv"
        input_file.write_text(input_data)
        
        output_file = tmp_path / "alpha_sweep.csv"
        
        # Run analysis
        alpha_values = [0.01, 0.05, 0.10]
        results = run_sensitivity_analysis(
            alpha_values=alpha_values,
            input_file=str(input_file),
            output_file=str(output_file)
        )
        
        # Verify results
        # At alpha=0.01: only query 3 (p=0.035) is significant? No, 0.035 > 0.01. None.
        # At alpha=0.05: query 1 (0.045) and query 3 (0.035) are significant. Count = 2.
        # At alpha=0.10: query 1, 3, and 4 (0.09) are significant. Count = 3.
        assert results[0.01] == 0
        assert results[0.05] == 2
        assert results[0.10] == 3

        # Verify output file
        assert output_file.exists()
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 3
        assert rows[0]['alpha'] == '0.01'
        assert rows[0]['significant_count'] == '0'
        assert rows[1]['alpha'] == '0.05'
        assert rows[1]['significant_count'] == '2'
        assert rows[2]['alpha'] == '0.10'
        assert rows[2]['significant_count'] == '3'

    def test_sensitivity_analysis_with_custom_alphas(self, tmp_path):
        """Test sensitivity analysis with custom alpha values."""
        input_data = """query_id,metric,raw_p,corrected_p,is_significant
        1,NDCG@10,0.03,0.045,True
        2,MAP,0.06,0.09,False"""
        
        input_file = tmp_path / "corrected_p_values.csv"
        input_file.write_text(input_data)
        
        output_file = tmp_path / "alpha_sweep.csv"
        
        alpha_values = [0.04, 0.05, 0.09, 0.10]
        results = run_sensitivity_analysis(
            alpha_values=alpha_values,
            input_file=str(input_file),
            output_file=str(output_file)
        )
        
        # At 0.04: none (0.045 > 0.04)
        # At 0.05: query 1 (0.045)
        # At 0.09: query 1 and 2 (0.09)
        # At 0.10: query 1 and 2
        assert results[0.04] == 0
        assert results[0.05] == 1
        assert results[0.09] == 2
        assert results[0.10] == 2

    def test_no_input_data(self, tmp_path):
        """Test handling of empty input data."""
        input_data = "query_id,metric,raw_p,corrected_p,is_significant"
        
        input_file = tmp_path / "corrected_p_values.csv"
        input_file.write_text(input_data)
        
        output_file = tmp_path / "alpha_sweep.csv"
        
        results = run_sensitivity_analysis(
            input_file=str(input_file),
            output_file=str(output_file)
        )
        
        # All counts should be 0
        for alpha, count in results.items():
            assert count == 0
        
        # Verify output file has headers
        assert output_file.exists()
        with open(output_file, 'r') as f:
            content = f.read()
            assert 'alpha,significant_count' in content
            # Should have 3 rows for default alphas
            lines = content.strip().split('\n')
            assert len(lines) == 4  # header + 3 data rows