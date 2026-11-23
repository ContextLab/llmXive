import pytest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

# Import the functions to test
from code.validate_metadata import (
    load_aggregated_subjects,
    validate_age_gender_metadata,
    write_validation_log,
    main
)

class TestLoadAggregatedSubjects:
    def test_load_valid_json(self, tmp_path):
        """Test loading a valid JSON file."""
        test_data = {
            "subjects": [
                {"subject_id": "sub-01", "age": 25, "gender": "M", "has_fluid_intelligence": True},
                {"subject_id": "sub-02", "age": 30, "gender": "F", "has_fluid_intelligence": True}
            ]
        }
        file_path = tmp_path / "aggregated_subjects.json"
        with open(file_path, 'w') as f:
            json.dump(test_data, f)
        
        result = load_aggregated_subjects(str(file_path))
        assert len(result) == 2
        assert result[0]['subject_id'] == 'sub-01'
    
    def test_load_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_aggregated_subjects(str(tmp_path / "nonexistent.json"))
    
    def test_load_invalid_json(self, tmp_path):
        """Test that JSONDecodeError is raised for invalid JSON."""
        file_path = tmp_path / "invalid.json"
        file_path.write_text("not valid json")
        
        with pytest.raises(json.JSONDecodeError):
            load_aggregated_subjects(str(file_path))

class TestValidateAgeGenderMetadata:
    def test_all_valid(self):
        """Test validation when all subjects have valid metadata."""
        subjects = [
            {"subject_id": "sub-01", "age": 25, "gender": "M", "has_fluid_intelligence": True},
            {"subject_id": "sub-02", "age": 30, "gender": "F", "has_fluid_intelligence": True}
        ]
        result = validate_age_gender_metadata(subjects)
        
        assert result['valid_count'] == 2
        assert result['invalid_count'] == 0
        assert len(result['missing_age']) == 0
        assert len(result['missing_gender']) == 0
    
    def test_missing_age(self):
        """Test validation when some subjects are missing age."""
        subjects = [
            {"subject_id": "sub-01", "age": 25, "gender": "M", "has_fluid_intelligence": True},
            {"subject_id": "sub-02", "age": None, "gender": "F", "has_fluid_intelligence": True},
            {"subject_id": "sub-03", "age": 35, "gender": "M", "has_fluid_intelligence": True}
        ]
        result = validate_age_gender_metadata(subjects)
        
        assert result['valid_count'] == 2
        assert result['invalid_count'] == 1
        assert 'sub-02' in result['missing_age']
    
    def test_missing_gender(self):
        """Test validation when some subjects are missing gender."""
        subjects = [
            {"subject_id": "sub-01", "age": 25, "gender": "M", "has_fluid_intelligence": True},
            {"subject_id": "sub-02", "age": 30, "gender": None, "has_fluid_intelligence": True},
            {"subject_id": "sub-03", "age": 35, "gender": "M", "has_fluid_intelligence": True}
        ]
        result = validate_age_gender_metadata(subjects)
        
        assert result['valid_count'] == 2
        assert result['invalid_count'] == 1
        assert 'sub-02' in result['missing_gender']
    
    def test_missing_fluid_intelligence(self):
        """Test that subjects without Fluid Intelligence scores are tracked but not counted as invalid."""
        subjects = [
            {"subject_id": "sub-01", "age": 25, "gender": "M", "has_fluid_intelligence": True},
            {"subject_id": "sub-02", "age": 30, "gender": "F", "has_fluid_intelligence": False}
        ]
        result = validate_age_gender_metadata(subjects)
        
        assert result['valid_count'] == 1
        assert result['invalid_count'] == 0
        assert 'sub-02' in result['missing_fluid_intelligence']
    
    def test_empty_list(self):
        """Test validation with empty subject list."""
        result = validate_age_gender_metadata([])
        
        assert result['valid_count'] == 0
        assert result['invalid_count'] == 0
        assert len(result['missing_age']) == 0
        assert len(result['missing_gender']) == 0
        assert len(result['missing_fluid_intelligence']) == 0
    
    def test_empty_string_age(self):
        """Test that empty string age is treated as missing."""
        subjects = [
            {"subject_id": "sub-01", "age": "", "gender": "M", "has_fluid_intelligence": True}
        ]
        result = validate_age_gender_metadata(subjects)
        
        assert result['invalid_count'] == 1
        assert 'sub-01' in result['missing_age']
    
    def test_empty_string_gender(self):
        """Test that empty string gender is treated as missing."""
        subjects = [
            {"subject_id": "sub-01", "age": 25, "gender": "", "has_fluid_intelligence": True}
        ]
        result = validate_age_gender_metadata(subjects)
        
        assert result['invalid_count'] == 1
        assert 'sub-01' in result['missing_gender']

class TestWriteValidationLog:
    def test_write_log_creates_file(self, tmp_path):
        """Test that write_validation_log creates the log file."""
        result = {
            'valid_count': 2,
            'invalid_count': 0,
            'missing_age': [],
            'missing_gender': [],
            'missing_fluid_intelligence': []
        }
        log_path = tmp_path / "validation.log"
        
        write_validation_log(result, str(log_path))
        
        assert log_path.exists()
        content = log_path.read_text()
        assert "Valid metadata" in content
        assert "2" in content
        
        # Check that summary JSON was also created
        summary_path = tmp_path / "metadata_validation_summary.json"
        assert summary_path.exists()

class TestMain:
    def test_main_success(self, tmp_path, capsys):
        """Test main function with valid data."""
        # Create test data
        test_data = {
            "subjects": [
                {"subject_id": "sub-01", "age": 25, "gender": "M", "has_fluid_intelligence": True}
            ]
        }
        data_dir = tmp_path / "data" / "processed"
        data_dir.mkdir(parents=True)
        aggregated_path = data_dir / "aggregated_subjects.json"
        with open(aggregated_path, 'w') as f:
            json.dump(test_data, f)
        
        # Mock the base_dir to use tmp_path
        with patch('code.validate_metadata.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            with patch('code.validate_metadata.sys.exit') as mock_exit:
                main()
                mock_exit.assert_called_with(0)
    
    def test_main_failure_missing_metadata(self, tmp_path):
        """Test main function fails when metadata is missing."""
        # Create test data with missing metadata
        test_data = {
            "subjects": [
                {"subject_id": "sub-01", "age": None, "gender": "M", "has_fluid_intelligence": True}
            ]
        }
        data_dir = tmp_path / "data" / "processed"
        data_dir.mkdir(parents=True)
        aggregated_path = data_dir / "aggregated_subjects.json"
        with open(aggregated_path, 'w') as f:
            json.dump(test_data, f)
        
        # Mock the base_dir to use tmp_path
        with patch('code.validate_metadata.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            with patch('code.validate_metadata.sys.exit') as mock_exit:
                main()
                mock_exit.assert_called_with(1)
    
    def test_main_file_not_found(self, tmp_path):
        """Test main function fails when aggregated file is missing."""
        data_dir = tmp_path / "data" / "processed"
        data_dir.mkdir(parents=True)
        
        # Mock the base_dir to use tmp_path
        with patch('code.validate_metadata.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            with patch('code.validate_metadata.sys.exit') as mock_exit:
                main()
                mock_exit.assert_called_with(1)