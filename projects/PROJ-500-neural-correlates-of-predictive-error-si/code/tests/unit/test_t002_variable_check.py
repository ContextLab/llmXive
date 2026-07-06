import pytest
import json
import os
import sys
from pathlib import Path
from src.data.ingest import validate_metadata_variables, check_and_report_variables

class TestT002VariableCheck:
    """Tests for T002: Variable check implementation in src/data/ingest.py"""

    def test_validate_metadata_variables_present(self):
        """Test that present variables are correctly identified."""
        metadata = {
            "features": {
                "stimulus_type": "string",
                "response_correctness": "bool",
                "reaction_time": "float"
            }
        }
        result = validate_metadata_variables(metadata)
        
        assert result["stimulus_type"] is True
        assert result["response_correctness"] is True

    def test_validate_metadata_variables_missing(self):
        """Test that missing variables are correctly identified."""
        metadata = {
            "features": {
                "reaction_time": "float",
                "subject_id": "int"
            }
        }
        result = validate_metadata_variables(metadata)
        
        assert result["stimulus_type"] is False
        assert result["response_correctness"] is False

    def test_validate_metadata_variables_empty(self):
        """Test handling of empty metadata."""
        metadata = {}
        result = validate_metadata_variables(metadata)
        
        assert result["stimulus_type"] is False
        assert result["response_correctness"] is False

    def test_check_and_report_variables_structure(self):
        """Test the structure of the report returned by check_and_report_variables."""
        metadata = {
            "features": {
                "stimulus_type": "string",
                "response_correctness": "bool"
            }
        }
        report = check_and_report_variables(metadata)
        
        assert "validation" in report
        assert "missing_variables" in report
        assert "is_valid" in report
        assert report["is_valid"] is True
        assert len(report["missing_variables"]) == 0

    def test_check_and_report_variables_missing_structure(self):
        """Test report structure when variables are missing."""
        metadata = {
            "features": {
                "reaction_time": "float"
            }
        }
        report = check_and_report_variables(metadata)
        
        assert report["is_valid"] is False
        assert "stimulus_type" in report["missing_variables"]
        assert "response_correctness" in report["missing_variables"]

    def test_list_features_parsing(self):
        """Test parsing when features is a list of dicts."""
        metadata = {
            "features": [
                {"name": "stimulus_type", "dtype": "string"},
                {"name": "response_correctness", "dtype": "bool"}
            ]
        }
        result = validate_metadata_variables(metadata)
        assert result["stimulus_type"] is True
        assert result["response_correctness"] is True
