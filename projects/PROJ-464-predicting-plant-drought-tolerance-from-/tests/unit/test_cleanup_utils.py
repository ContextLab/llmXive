"""
Unit tests for cleanup and refactoring utilities.

Tests the validation functions in code/cleanup_utils.py to ensure
proper data integrity checking and reporting.
"""

import os
import tempfile
import pytest
from pathlib import Path
import pandas as pd
import yaml

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))
from cleanup_utils import (
    validate_csv_structure,
    validate_yaml_structure,
    check_data_integrity,
    generate_cleanup_report
)

class TestValidateCSVStructure:
    """Tests for validate_csv_structure function."""
    
    def test_valid_csv_with_all_columns(self, tmp_path):
        """Test validation passes when all required columns are present."""
        csv_file = tmp_path / "test.csv"
        df = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': ['a', 'b', 'c'],
            'col3': [1.1, 2.2, 3.3]
        })
        df.to_csv(csv_file, index=False)
        
        is_valid, missing = validate_csv_structure(csv_file, ['col1', 'col2', 'col3'])
        
        assert is_valid is True
        assert missing == []
    
    def test_csv_missing_columns(self, tmp_path):
        """Test validation fails when required columns are missing."""
        csv_file = tmp_path / "test.csv"
        df = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': ['a', 'b', 'c']
        })
        df.to_csv(csv_file, index=False)
        
        is_valid, missing = validate_csv_structure(csv_file, ['col1', 'col2', 'col3'])
        
        assert is_valid is False
        assert missing == ['col3']
    
    def test_nonexistent_file(self, tmp_path):
        """Test validation fails for non-existent file."""
        csv_file = tmp_path / "nonexistent.csv"
        
        is_valid, missing = validate_csv_structure(csv_file, ['col1'])
        
        assert is_valid is False
        assert len(missing) == 1
        assert "File does not exist" in missing
    
    def test_empty_csv_file(self, tmp_path):
        """Test validation fails for empty CSV file."""
        csv_file = tmp_path / "empty.csv"
        csv_file.touch()
        
        is_valid, missing = validate_csv_structure(csv_file, ['col1'])
        
        assert is_valid is False
        assert len(missing) == 1
        assert "File is empty" in missing

class TestValidateYAMLStructure:
    """Tests for validate_yaml_structure function."""
    
    def test_valid_yaml_with_all_keys(self, tmp_path):
        """Test validation passes when all required keys are present."""
        yaml_file = tmp_path / "test.yaml"
        data = {
            'key1': 'value1',
            'key2': 'value2',
            'key3': 'value3'
        }
        with open(yaml_file, 'w') as f:
            yaml.dump(data, f)
        
        is_valid, missing = validate_yaml_structure(yaml_file, ['key1', 'key2', 'key3'])
        
        assert is_valid is True
        assert missing == []
    
    def test_yaml_missing_keys(self, tmp_path):
        """Test validation fails when required keys are missing."""
        yaml_file = tmp_path / "test.yaml"
        data = {
            'key1': 'value1',
            'key2': 'value2'
        }
        with open(yaml_file, 'w') as f:
            yaml.dump(data, f)
        
        is_valid, missing = validate_yaml_structure(yaml_file, ['key1', 'key2', 'key3'])
        
        assert is_valid is False
        assert missing == ['key3']
    
    def test_nonexistent_yaml_file(self, tmp_path):
        """Test validation fails for non-existent YAML file."""
        yaml_file = tmp_path / "nonexistent.yaml"
        
        is_valid, missing = validate_yaml_structure(yaml_file, ['key1'])
        
        assert is_valid is False
        assert len(missing) == 1
        assert "File does not exist" in missing
    
    def test_invalid_yaml_content(self, tmp_path):
        """Test validation fails for invalid YAML content."""
        yaml_file = tmp_path / "invalid.yaml"
        yaml_file.write_text("invalid: yaml: content: [unclosed")
        
        is_valid, missing = validate_yaml_structure(yaml_file, ['key1'])
        
        assert is_valid is False
        assert len(missing) == 1
        assert "YAML error" in missing[0]

class TestGenerateCleanupReport:
    """Tests for generate_cleanup_report function."""
    
    def test_report_with_all_valid_artifacts(self):
        """Test report generation when all artifacts are valid."""
        results = {
            'artifact1.csv': {'exists': True, 'issues': [], 'path': '/path/to/artifact1.csv'},
            'artifact2.csv': {'exists': True, 'issues': [], 'path': '/path/to/artifact2.csv'}
        }
        
        report = generate_cleanup_report(results)
        
        assert "All artifacts are valid!" in report
        assert "Total artifacts checked: 2" in report
        assert "Valid artifacts: 2" in report
        assert "Invalid artifacts: 0" in report
    
    def test_report_with_invalid_artifacts(self):
        """Test report generation when some artifacts are invalid."""
        results = {
            'artifact1.csv': {'exists': True, 'issues': [], 'path': '/path/to/artifact1.csv'},
            'artifact2.csv': {'exists': False, 'issues': ['File does not exist'], 'path': '/path/to/artifact2.csv'}
        }
        
        report = generate_cleanup_report(results)
        
        assert "ISSUES FOUND:" in report
        assert "❌ artifact2.csv" in report
        assert "File does not exist" in report
        assert "Total artifacts checked: 2" in report
        assert "Valid artifacts: 1" in report
        assert "Invalid artifacts: 1" in report
    
    def test_report_format(self):
        """Test that the report has the expected format."""
        results = {
            'test.csv': {'exists': True, 'issues': [], 'path': '/path/test.csv'}
        }
        
        report = generate_cleanup_report(results)
        
        assert report.startswith("=" * 60)
        assert "CLEANUP AND VALIDATION REPORT" in report
        assert report.endswith("=" * 60)

class TestIntegration:
    """Integration tests for the cleanup utilities."""
    
    def test_full_validation_workflow(self, tmp_path):
        """Test the full validation workflow with mixed valid/invalid files."""
        # Create a mix of valid and invalid files
        data_dir = tmp_path / "data" / "derived"
        data_dir.mkdir(parents=True)
        
        # Create a valid CSV
        valid_csv = data_dir / "valid.csv"
        pd.DataFrame({'col1': [1, 2], 'col2': ['a', 'b']}).to_csv(valid_csv, index=False)
        
        # Create a CSV with missing columns
        invalid_csv = data_dir / "invalid.csv"
        pd.DataFrame({'col1': [1, 2]}).to_csv(invalid_csv, index=False)
        
        # Create a valid YAML
        valid_yaml = tmp_path / "state" / "valid.yaml"
        valid_yaml.parent.mkdir(parents=True)
        with open(valid_yaml, 'w') as f:
            yaml.dump({'key1': 'value1', 'key2': 'value2'}, f)
        
        # Test validation
        results = {
            'valid.csv': {'exists': True, 'issues': [], 'path': str(valid_csv)},
            'invalid.csv': {'exists': False, 'issues': ['Missing columns'], 'path': str(invalid_csv)},
            'valid.yaml': {'exists': True, 'issues': [], 'path': str(valid_yaml)}
        }
        
        report = generate_cleanup_report(results)
        
        assert "Valid artifacts: 2" in report
        assert "Invalid artifacts: 1" in report
        assert "ISSUES FOUND:" in report
