"""
Integration tests for sensitivity analysis (T024).

Verifies that the sensitivity analysis correctly:
1. Loads corrected p-values from the expected file
2. Calculates significance counts for each alpha value
3. Generates the output CSV with correct format and content
"""
import os
import csv
import tempfile
import pytest
from unittest.mock import patch, MagicMock
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.sensitivity_analysis import (
    load_corrected_p_values,
    determine_significance,
    run_sensitivity_analysis,
    ALPHA_VALUES
)


class TestDetermineSignificance:
    """Tests for the determine_significance helper function."""
    
    def test_significant_at_higher_alpha(self):
        """A p-value of 0.03 should be significant at alpha=0.05 and 0.10."""
        assert determine_significance(0.03, 0.05) is True
        assert determine_significance(0.03, 0.10) is True
    
    def test_not_significant_at_lower_alpha(self):
        """A p-value of 0.03 should not be significant at alpha=0.01."""
        assert determine_significance(0.03, 0.01) is False
    
    def test_exact_boundary(self):
        """A p-value equal to alpha should be significant."""
        assert determine_significance(0.05, 0.05) is True
        assert determine_significance(0.01, 0.01) is True
    
    def test_just_above_boundary(self):
        """A p-value just above alpha should not be significant."""
        assert determine_significance(0.051, 0.05) is False
        assert determine_significance(0.011, 0.01) is False


class TestLoadCorrectedPValues:
    """Tests for loading corrected p-values."""
    
    def test_load_valid_file(self):
        """Test loading a valid corrected p-values file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            writer = csv.writer(f)
            writer.writerow(['query_id', 'metric', 'raw_p', 'corrected_p', 'is_significant'])
            writer.writerow([1, 'NDCG@10', 0.005, 0.04, 'True'])
            writer.writerow([2, 'MAP', 0.06, 0.12, 'False'])
            temp_path = f.name
        
        try:
            data = load_corrected_p_values(temp_path)
            assert len(data) == 2
            assert data[0]['query_id'] == 1
            assert data[0]['metric'] == 'NDCG@10'
            assert data[0]['corrected_p'] == 0.04
            assert data[0]['is_significant'] is True
            assert data[1]['is_significant'] is False
        finally:
            os.unlink(temp_path)
    
    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_corrected_p_values('/nonexistent/path/file.csv')


class TestSensitivityAnalysis:
    """Integration tests for the full sensitivity analysis pipeline."""
    
    def test_full_pipeline_with_mock_data(self, tmp_path):
        """Test the full sensitivity analysis pipeline with mock data."""
        # Create mock corrected p-values file
        mock_data_path = tmp_path / "p_values" / "corrected_p_values.csv"
        mock_data_path.parent.mkdir(parents=True)
        
        with open(mock_data_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['query_id', 'metric', 'raw_p', 'corrected_p', 'is_significant'])
            # Create data that will change significance across alpha values
            writer.writerow([1, 'NDCG@10', 0.005, 0.04, 'True'])   # Sig at 0.05, 0.10
            writer.writerow([2, 'MAP', 0.06, 0.12, 'False'])      # Not sig at any
            writer.writerow([3, 'NDCG@10', 0.02, 0.025, 'True'])  # Sig at 0.05, 0.10
            writer.writerow([4, 'MAP', 0.008, 0.009, 'True'])     # Sig at all
            writer.writerow([5, 'NDCG@10', 0.003, 0.003, 'True']) # Sig at all
        
        output_path = tmp_path / "sensitivity" / "alpha_sweep.csv"
        
        # Run analysis
        run_sensitivity_analysis(
            input_path=str(mock_data_path),
            output_path=str(output_path)
        )
        
        # Verify output file exists
        assert output_path.exists()
        
        # Verify output content
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 3  # 3 alpha values
        
        # Check alpha values and counts
        # At 0.01: 2 significant (rows 4, 5)
        # At 0.05: 4 significant (rows 1, 3, 4, 5)
        # At 0.10: 4 significant (rows 1, 3, 4, 5)
        assert float(rows[0]['alpha']) == 0.01
        assert int(rows[0]['significant_count']) == 2
        
        assert float(rows[1]['alpha']) == 0.05
        assert int(rows[1]['significant_count']) == 4
        
        assert float(rows[2]['alpha']) == 0.10
        assert int(rows[2]['significant_count']) == 4
    
    def test_empty_input_file(self, tmp_path):
        """Test handling of an empty input file (header only)."""
        mock_data_path = tmp_path / "p_values" / "corrected_p_values.csv"
        mock_data_path.parent.mkdir(parents=True)
        
        with open(mock_data_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['query_id', 'metric', 'raw_p', 'corrected_p', 'is_significant'])
        
        output_path = tmp_path / "sensitivity" / "alpha_sweep.csv"
        
        # Should not raise, but produce empty results
        run_sensitivity_analysis(
            input_path=str(mock_data_path),
            output_path=str(output_path)
        )
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 3  # Still 3 alpha values, but with 0 counts
        
        for row in rows:
            assert int(row['significant_count']) == 0
    
    def test_output_format(self, tmp_path):
        """Verify the output CSV has the correct format."""
        mock_data_path = tmp_path / "p_values" / "corrected_p_values.csv"
        mock_data_path.parent.mkdir(parents=True)
        
        with open(mock_data_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['query_id', 'metric', 'raw_p', 'corrected_p', 'is_significant'])
            writer.writerow([1, 'NDCG@10', 0.005, 0.001, 'True'])
        
        output_path = tmp_path / "sensitivity" / "alpha_sweep.csv"
        
        run_sensitivity_analysis(
            input_path=str(mock_data_path),
            output_path=str(output_path)
        )
        
        with open(output_path, 'r') as f:
            header = f.readline().strip()
            assert header == 'alpha,significant_count'
        
        # Verify columns in data rows
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                assert 'alpha' in row
                assert 'significant_count' in row
                assert float(row['alpha']) in ALPHA_VALUES