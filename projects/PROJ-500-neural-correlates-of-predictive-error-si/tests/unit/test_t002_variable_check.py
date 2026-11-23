import pytest
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile

from src.data.ingest import validate_metadata_variables, check_and_report_variables, generate_validation_report

class TestT002VariableCheck:
    """
    Tests for T002: Implement variable check in src/data/ingest.py
    """

    def test_validate_metadata_variables_all_present(self):
        """Test that validate_metadata_variables returns True when all required vars are present."""
        metadata = {
            'stimulus_type': ['standard', 'deviant'],
            'response_correctness': [True, False]
        }
        required = ['stimulus_type', 'response_correctness']
        assert validate_metadata_variables(metadata, required) is True

    def test_validate_metadata_variables_missing_one(self):
        """Test that validate_metadata_variables returns False when one required var is missing."""
        metadata = {
            'stimulus_type': ['standard', 'deviant']
            # response_correctness missing
        }
        required = ['stimulus_type', 'response_correctness']
        assert validate_metadata_variables(metadata, required) is False

    def test_validate_metadata_variables_missing_all(self):
        """Test that validate_metadata_variables returns False when all required vars are missing."""
        metadata = {
            'other_var': 'value'
        }
        required = ['stimulus_type', 'response_correctness']
        assert validate_metadata_variables(metadata, required) is False

    def test_validate_metadata_variables_empty_metadata(self):
        """Test that validate_metadata_variables returns False for empty metadata."""
        assert validate_metadata_variables({}, ['stimulus_type']) is False
        assert validate_metadata_variables(None, ['stimulus_type']) is False

    def test_check_and_report_variables_error_signal_mode(self):
        """
        Test check_and_report_variables determines 'error_signal' mode
        when both stimulus_type and response_correctness are present.
        """
        metadata = {
            'stimulus_type': ['standard', 'deviant'],
            'response_correctness': [True, False]
        }
        result = check_and_report_variables(metadata)
        
        assert result['stimulus_type_present'] is True
        assert result['response_correctness_present'] is True
        assert result['analysis_mode'] == 'error_signal'

    def test_check_and_report_variables_stimulus_driven_mode(self):
        """
        Test check_and_report_variables determines 'stimulus_driven' mode
        when only stimulus_type is present.
        """
        metadata = {
            'stimulus_type': ['standard', 'deviant'],
            'other_field': 'value'
        }
        result = check_and_report_variables(metadata)
        
        assert result['stimulus_type_present'] is True
        assert result['response_correctness_present'] is False
        assert result['analysis_mode'] == 'stimulus_driven'

    def test_check_and_report_variables_invalid_mode(self):
        """
        Test check_and_report_variables returns None for analysis_mode
        when neither required variable is present.
        """
        metadata = {
            'other_field': 'value'
        }
        result = check_and_report_variables(metadata)
        
        assert result['stimulus_type_present'] is False
        assert result['response_correctness_present'] is False
        assert result['analysis_mode'] is None

    def test_generate_validation_report_creates_file(self):
        """Test that generate_validation_report creates the JSON file with correct content."""
        metadata = {
            'stimulus_type': ['standard', 'deviant'],
            'response_correctness': [True, False]
        }
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "validation_report.json"
            report = generate_validation_report(metadata, output_path)
            
            assert output_path.exists()
            assert report['analysis_mode'] == 'error_signal'
            assert report['status'] == 'valid'
            
            # Verify file content
            with open(output_path, 'r') as f:
                loaded = json.load(f)
                assert loaded == report

    def test_generate_validation_report_stimulus_driven(self):
        """Test report generation for stimulus_driven mode."""
        metadata = {
            'stimulus_type': ['standard', 'deviant']
        }
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "validation_report.json"
            report = generate_validation_report(metadata, output_path)
            
            assert report['analysis_mode'] == 'stimulus_driven'
            assert report['status'] == 'valid' # Valid because stimulus_type exists

    def test_generate_validation_report_invalid(self):
        """Test report generation when no required variables exist."""
        metadata = {
            'random_field': 'value'
        }
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "validation_report.json"
            report = generate_validation_report(metadata, output_path)
            
            assert report['analysis_mode'] is None
            assert report['status'] == 'invalid'