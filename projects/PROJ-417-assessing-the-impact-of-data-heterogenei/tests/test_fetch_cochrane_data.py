"""
Tests for the Cochrane data fetch script.

These tests verify that:
1. The data is loaded correctly
2. The data structure is valid
3. The CSV is saved correctly
"""
import os
import sys
import csv
import tempfile
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.fetch_cochrane_data import load_jackson_2010_base_data, validate_data_structure, save_to_csv


class TestJackson2010BaseData:
    """Tests for the Jackson et al. (2010) base data loader."""
    
    def test_load_data_returns_list(self):
        """Test that load_jackson_2010_base_data returns a list."""
        data = load_jackson_2010_base_data()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_load_data_has_required_fields(self):
        """Test that all records have required fields."""
        data = load_jackson_2010_base_data()
        required_fields = ["study_id", "effect_size", "std_error", "n_studies", "n_events"]
        
        for record in data:
            for field in required_fields:
                assert field in record, f"Missing field: {field}"
    
    def test_load_data_has_correct_types(self):
        """Test that data types are correct."""
        data = load_jackson_2010_base_data()
        
        for record in data:
            assert isinstance(record["study_id"], str)
            assert isinstance(record["effect_size"], (int, float))
            assert isinstance(record["std_error"], (int, float))
            assert isinstance(record["n_studies"], int)
            assert isinstance(record["n_events"], int)
    
    def test_load_data_has_valid_ranges(self):
        """Test that data values are in valid ranges."""
        data = load_jackson_2010_base_data()
        
        for record in data:
            assert record["std_error"] > 0, "std_error must be positive"
            assert record["n_studies"] > 0, "n_studies must be positive"
            assert 0 <= record["n_events"] <= record["n_studies"], "n_events must be valid"
    
    def test_load_data_has_expected_size(self):
        """Test that we have the expected number of studies."""
        data = load_jackson_2010_base_data()
        # Jackson et al. (2010) typically uses around 20 studies
        assert len(data) == 20, f"Expected 20 studies, got {len(data)}"


class TestDataValidation:
    """Tests for data validation function."""
    
    def test_validate_empty_data(self):
        """Test validation of empty data."""
        assert not validate_data_structure([])
    
    def test_validate_missing_fields(self):
        """Test validation with missing fields."""
        data = [{"study_id": "S001", "effect_size": 0.1}]
        assert not validate_data_structure(data)
    
    def test_validate_invalid_types(self):
        """Test validation with invalid types."""
        data = [{"study_id": 123, "effect_size": 0.1, "std_error": 0.1, "n_studies": 100, "n_events": 50}]
        assert not validate_data_structure(data)
    
    def test_validate_invalid_ranges(self):
        """Test validation with invalid ranges."""
        data = [
            {"study_id": "S001", "effect_size": 0.1, "std_error": -0.1, "n_studies": 100, "n_events": 50},
        ]
        assert not validate_data_structure(data)
    
    def test_validate_valid_data(self):
        """Test validation of valid data."""
        data = [
            {"study_id": "S001", "effect_size": 0.1, "std_error": 0.1, "n_studies": 100, "n_events": 50},
            {"study_id": "S002", "effect_size": 0.2, "std_error": 0.15, "n_studies": 80, "n_events": 30},
        ]
        assert validate_data_structure(data)


class TestSaveToCsv:
    """Tests for CSV saving function."""
    
    def test_save_and_load_csv(self):
        """Test that data can be saved and loaded from CSV."""
        data = [
            {"study_id": "S001", "effect_size": 0.1, "std_error": 0.1, "n_studies": 100, "n_events": 50},
            {"study_id": "S002", "effect_size": 0.2, "std_error": 0.15, "n_studies": 80, "n_events": 30},
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.csv"
            save_to_csv(data, output_path)
            
            # Verify file exists
            assert output_path.exists()
            
            # Load and verify content
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                assert len(rows) == 2
                assert rows[0]["study_id"] == "S001"
                assert float(rows[0]["effect_size"]) == 0.1
                assert rows[1]["study_id"] == "S002"
    
    def test_save_creates_directory(self):
        """Test that save_to_csv creates the output directory if needed."""
        data = [
            {"study_id": "S001", "effect_size": 0.1, "std_error": 0.1, "n_studies": 100, "n_events": 50},
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "test.csv"
            save_to_csv(data, output_path)
            
            assert output_path.exists()
    
    def test_save_empty_data_raises_error(self):
        """Test that saving empty data raises an error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.csv"
            with pytest.raises(ValueError, match="Cannot save empty data"):
                save_to_csv([], output_path)