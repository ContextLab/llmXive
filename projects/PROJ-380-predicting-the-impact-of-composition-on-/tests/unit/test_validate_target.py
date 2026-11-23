import pytest
import os
import json
from pathlib import Path
import tempfile
import csv

from code.data.validate_target import (
    load_processed_data,
    validate_target_no_missing,
    save_validation_report
)

class TestValidateTarget:
    
    def setup_method(self):
        """Setup test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_path = Path(self.temp_dir) / "test_data.csv"
        self.test_report_path = Path(self.temp_dir) / "test_report.json"
        
        # Create a sample CSV with valid data
        self.valid_data = [
            {"composition": "Zr50Cu40", "shear_modulus_GPa": 30.5},
            {"composition": "Pd40Ni40", "shear_modulus_GPa": 28.2},
            {"composition": "La55Al25", "shear_modulus_GPa": 25.0}
        ]
        
        # Create a sample CSV with missing target values
        self.missing_data = [
            {"composition": "Zr50Cu40", "shear_modulus_GPa": 30.5},
            {"composition": "Pd40Ni40", "shear_modulus_GPa": ""},
            {"composition": "La55Al25", "shear_modulus_GPa": None}
        ]
        
        # Write valid data to file
        with open(self.test_data_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.valid_data[0].keys())
            writer.writeheader()
            writer.writerows(self.valid_data)
    
    def teardown_method(self):
        """Cleanup test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_processed_data_valid(self):
        """Test loading valid CSV data."""
        data = load_processed_data(str(self.test_data_path))
        assert len(data) == 3
        assert data[0]["composition"] == "Zr50Cu40"
        assert data[0]["shear_modulus_GPa"] == "30.5"

    def test_validate_target_no_missing_valid(self):
        """Test validation with no missing values."""
        result = validate_target_no_missing(self.valid_data)
        assert result["valid"] is True
        assert result["missing_count"] == 0
        assert result["missing_indices"] == []
        assert "passed" in result["message"].lower()

    def test_validate_target_no_missing_missing(self):
        """Test validation with missing values."""
        result = validate_target_no_missing(self.missing_data)
        assert result["valid"] is False
        assert result["missing_count"] == 2
        assert 1 in result["missing_indices"]
        assert 2 in result["missing_indices"]
        assert "failed" in result["message"].lower()

    def test_validate_target_empty_string(self):
        """Test validation with empty string as missing value."""
        data = [
            {"composition": "Zr50Cu40", "shear_modulus_GPa": "30.5"},
            {"composition": "Pd40Ni40", "shear_modulus_GPa": ""}
        ]
        result = validate_target_no_missing(data)
        assert result["valid"] is False
        assert result["missing_count"] == 1

    def test_validate_target_none_value(self):
        """Test validation with None as missing value."""
        data = [
            {"composition": "Zr50Cu40", "shear_modulus_GPa": "30.5"},
            {"composition": "Pd40Ni40", "shear_modulus_GPa": None}
        ]
        result = validate_target_no_missing(data)
        assert result["valid"] is False
        assert result["missing_count"] == 1

    def test_save_validation_report(self):
        """Test saving validation report to JSON."""
        result = {
            "valid": True,
            "missing_count": 0,
            "missing_indices": [],
            "message": "Validation passed"
        }
        save_validation_report(result, str(self.test_report_path))
        
        assert self.test_report_path.exists()
        with open(self.test_report_path, 'r') as f:
            saved_result = json.load(f)
        
        assert saved_result["valid"] is True
        assert saved_result["missing_count"] == 0
