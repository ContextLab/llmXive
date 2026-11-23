import pytest
import json
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the functions to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from task_t015b_stimulus_validation import load_metadata, validate_stimulus_doi

class TestLoadMetadata:
    def test_load_metadata_success(self, tmp_path):
        """Test successful loading of a valid metadata file."""
        metadata_path = tmp_path / "metadata.json"
        test_data = {"key": "value", "validation_study_doi": "10.1234/test"}
        metadata_path.write_text(json.dumps(test_data))
        
        result = load_metadata(metadata_path)
        assert result == test_data
        assert result["validation_study_doi"] == "10.1234/test"

    def test_load_metadata_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised when file is missing."""
        metadata_path = tmp_path / "nonexistent.json"
        with pytest.raises(FileNotFoundError):
            load_metadata(metadata_path)

    def test_load_metadata_invalid_json(self, tmp_path):
        """Test that JSONDecodeError is raised for invalid JSON."""
        metadata_path = tmp_path / "invalid.json"
        metadata_path.write_text("not valid json")
        
        with pytest.raises(json.JSONDecodeError):
            load_metadata(metadata_path)

class TestValidateStimulusDoi:
    def test_doi_present(self):
        """Test validation when DOI is present."""
        metadata = {"validation_study_doi": "10.1234/example_doi"}
        result = validate_stimulus_doi(metadata)
        assert result == "INFO_STIMULUS_VALIDATED"

    def test_doi_null(self):
        """Test validation when DOI is null."""
        metadata = {"validation_study_doi": None}
        result = validate_stimulus_doi(metadata)
        assert result == "WARN_STIMULUS_NO_VALIDATION"

    def test_doi_missing(self):
        """Test validation when DOI key is missing."""
        metadata = {"other_key": "value"}
        result = validate_stimulus_doi(metadata)
        assert result == "WARN_STIMULUS_NO_VALIDATION"

    def test_doi_empty_string(self):
        """Test validation when DOI is an empty string."""
        metadata = {"validation_study_doi": ""}
        result = validate_stimulus_doi(metadata)
        assert result == "WARN_STIMULUS_NO_VALIDATION"