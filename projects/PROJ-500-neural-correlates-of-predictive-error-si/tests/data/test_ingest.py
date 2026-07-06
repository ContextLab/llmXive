"""
Tests for data ingestion variable validation (T002).
"""
import pytest
import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.data.ingest import validate_metadata_variables, check_and_report_variables, REQUIRED_METADATA_VARIABLES

class TestVariableValidation:
    """Tests for metadata variable validation logic."""

    def test_all_variables_present(self):
        """Test case where all required variables are present."""
        metadata = {
            "stimulus_type": ["standard", "deviant"],
            "response_correctness": ["correct", "incorrect"],
            "other_field": "value"
        }
        
        results = validate_metadata_variables(metadata)
        
        assert results["stimulus_type"] is True
        assert results["response_correctness"] is True
        assert all(results.values())

    def test_missing_variable(self):
        """Test case where one required variable is missing."""
        metadata = {
            "stimulus_type": ["standard", "deviant"],
            # response_correctness missing
            "other_field": "value"
        }
        
        results = validate_metadata_variables(metadata)
        
        assert results["stimulus_type"] is True
        assert results["response_correctness"] is False
        assert not all(results.values())

    def test_nested_variables_structure(self):
        """Test validation with nested variables structure."""
        metadata = {
            "variables": {
                "stimulus_type": {"type": "categorical"},
                "response_correctness": {"type": "boolean"}
            }
        }
        
        results = validate_metadata_variables(metadata)
        
        assert results["stimulus_type"] is True
        assert results["response_correctness"] is True

    def test_columns_list_structure(self):
        """Test validation with columns as list of dicts."""
        metadata = {
            "columns": [
                {"name": "stimulus_type", "dtype": "str"},
                {"name": "response_correctness", "dtype": "bool"}
            ]
        }
        
        results = validate_metadata_variables(metadata)
        
        assert results["stimulus_type"] is True
        assert results["response_correctness"] is True

    def test_check_and_report_generation(self, tmp_path):
        """Test that the report is generated correctly."""
        metadata = {
            "stimulus_type": ["standard"],
            "response_correctness": ["correct"]
        }
        
        output_file = tmp_path / "validation_report.json"
        report = check_and_report_variables(metadata, str(output_file))
        
        assert output_file.exists()
        assert report["all_required_present"] is True
        assert report["analysis_mode"] == "error_signal"
        
        with open(output_file, "r") as f:
            saved_report = json.load(f)
        
        assert saved_report == report

    def test_analysis_mode_switch_on_missing(self, tmp_path):
        """Test that analysis mode switches to stimulus_driven when variables are missing."""
        metadata = {
            "stimulus_type": ["standard"],
            # response_correctness missing
        }
        
        output_file = tmp_path / "validation_report_missing.json"
        report = check_and_report_variables(metadata, str(output_file))
        
        assert report["all_required_present"] is False
        assert report["analysis_mode"] == "stimulus_driven"
        assert "response_correctness" in report["missing_variables"]

    def test_invalid_metadata_type(self):
        """Test that invalid metadata type raises ValueError."""
        with pytest.raises(ValueError):
            validate_metadata_variables("not a dict")

        with pytest.raises(ValueError):
            validate_metadata_variables([1, 2, 3])