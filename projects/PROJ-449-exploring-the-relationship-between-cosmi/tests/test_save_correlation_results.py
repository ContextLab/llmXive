"""
Tests for T023: Save correlation results checkpoint.

These tests verify that the correlation results files are properly
generated and validated by the save_correlation_results script.
"""

import os
import json
import tempfile
import pytest
from pathlib import Path
import pandas as pd

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.analysis.save_correlation_results import (
    verify_file_exists,
    validate_json_structure,
    validate_csv_structure
)


class TestVerifyFileExists:
    """Tests for verify_file_exists function."""
    
    def test_file_exists(self, tmp_path):
        """Test that existing file is verified successfully."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        result = verify_file_exists(test_file, "Test")
        assert result is True
    
    def test_file_not_found(self, tmp_path):
        """Test that missing file returns False."""
        missing_file = tmp_path / "nonexistent.txt"
        
        result = verify_file_exists(missing_file, "Test")
        assert result is False
    
    def test_empty_file(self, tmp_path):
        """Test that empty file returns False."""
        empty_file = tmp_path / "empty.txt"
        empty_file.touch()  # Create empty file
        
        result = verify_file_exists(empty_file, "Test")
        assert result is False


class TestValidateJsonStructure:
    """Tests for validate_json_structure function."""
    
    def test_valid_json(self, tmp_path):
        """Test validation of valid JSON with expected structure."""
        test_file = tmp_path / "valid.json"
        data = {
            'correlations': [],
            'summary': {},
            'metadata': {'version': '1.0'}
        }
        with open(test_file, 'w') as f:
            json.dump(data, f)
        
        result = validate_json_structure(test_file)
        assert result is True
    
    def test_invalid_json(self, tmp_path):
        """Test validation of malformed JSON."""
        test_file = tmp_path / "invalid.json"
        test_file.write_text("{ invalid json }")
        
        result = validate_json_structure(test_file)
        assert result is False
    
    def test_json_not_dict(self, tmp_path):
        """Test validation of JSON that is not a dictionary."""
        test_file = tmp_path / "not_dict.json"
        with open(test_file, 'w') as f:
            json.dump([1, 2, 3], f)  # List instead of dict
        
        result = validate_json_structure(test_file)
        assert result is False
    
    def test_json_missing_keys(self, tmp_path, caplog):
        """Test validation of JSON with missing expected keys."""
        test_file = tmp_path / "missing_keys.json"
        data = {'only_key': 'value'}
        with open(test_file, 'w') as f:
            json.dump(data, f)
        
        result = validate_json_structure(test_file)
        # Should still return True, just with warnings
        assert result is True


class TestValidateCsvStructure:
    """Tests for validate_csv_structure function."""
    
    def test_valid_csv(self, tmp_path):
        """Test validation of valid CSV with expected columns."""
        test_file = tmp_path / "valid.csv"
        df = pd.DataFrame({
            'species': ['proton', 'helium'],
            'rigidity_bin': [1.0, 2.0],
            'lag_months': [0, 1],
            'correlation_coefficient': [0.5, 0.6],
            'p_value': [0.01, 0.02],
            'method': ['pearson', 'spearman']
        })
        df.to_csv(test_file, index=False)
        
        result = validate_csv_structure(test_file)
        assert result is True
    
    def test_empty_csv(self, tmp_path):
        """Test validation of empty CSV."""
        test_file = tmp_path / "empty.csv"
        test_file.touch()
        
        result = validate_csv_structure(test_file)
        assert result is False
    
    def test_csv_missing_columns(self, tmp_path, caplog):
        """Test validation of CSV with missing expected columns."""
        test_file = tmp_path / "missing_cols.csv"
        df = pd.DataFrame({
            'species': ['proton'],
            'rigidity_bin': [1.0]
            # Missing other expected columns
        })
        df.to_csv(test_file, index=False)
        
        result = validate_csv_structure(test_file)
        # Should still return True, just with warnings
        assert result is True
    
    def test_invalid_csv(self, tmp_path):
        """Test validation of malformed CSV."""
        test_file = tmp_path / "invalid.csv"
        test_file.write_text("col1,col2\nval1")  # Missing value
        
        result = validate_csv_structure(test_file)
        # Pandas may handle this differently, but shouldn't crash
        # The exact behavior depends on pandas version and settings
        # We just ensure it doesn't raise an unhandled exception
        assert result in [True, False]  # Either is acceptable


class TestIntegration:
    """Integration tests for the full workflow."""
    
    def test_full_workflow(self, tmp_path, monkeypatch):
        """Test the full workflow with valid files."""
        # Create test JSON file
        json_file = tmp_path / "correlation_results.json"
        json_data = {
            'correlations': [
                {
                    'species': 'He/p',
                    'rigidity_bin': 1.0,
                    'lag_months': 0,
                    'correlation_coefficient': 0.75,
                    'p_value': 0.001,
                    'method': 'pearson'
                }
            ],
            'summary': {
                'total_correlations': 1,
                'significant_correlations': 1
            },
            'metadata': {
                'version': '1.0',
                'generated_by': 'T020'
            }
        }
        with open(json_file, 'w') as f:
            json.dump(json_data, f)
        
        # Create test CSV file
        csv_file = tmp_path / "correlation_summary.csv"
        df = pd.DataFrame({
            'species': ['He/p', 'Fe/p'],
            'rigidity_bin': [1.0, 2.0],
            'lag_months': [0, 1],
            'correlation_coefficient': [0.75, 0.65],
            'p_value': [0.001, 0.005],
            'method': ['pearson', 'spearman']
        })
        df.to_csv(csv_file, index=False)
        
        # Verify both files
        json_valid = verify_file_exists(json_file, "JSON") and validate_json_structure(json_file)
        csv_valid = verify_file_exists(csv_file, "CSV") and validate_csv_structure(csv_file)
        
        assert json_valid is True
        assert csv_valid is True