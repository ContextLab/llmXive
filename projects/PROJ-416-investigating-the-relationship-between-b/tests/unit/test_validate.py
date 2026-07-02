"""
Unit tests for code/data/validate.py

Tests the validation logic for metadata presence and type checking.
"""
import pytest
import logging
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path
import json
import tempfile

# Add project root to path for imports if running standalone
# In the actual project structure, this is handled by pytest.ini or conftest
try:
    from code.data.validate import validate_metadata, validate_subject_metadata_path
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from code.data.validate import validate_metadata, validate_subject_metadata_path


@pytest.fixture
def valid_metadata():
    return {
        'pre_treatment_score': 15.0,
        'post_treatment_score': 10.0,
        'subject_id': 'sub-01',
        'session': 'baseline'
    }


@pytest.fixture
def missing_pre_metadata():
    return {
        'post_treatment_score': 10.0,
        'subject_id': 'sub-01'
    }


@pytest.fixture
def missing_post_metadata():
    return {
        'pre_treatment_score': 15.0,
        'subject_id': 'sub-01'
    }


@pytest.fixture
def none_score_metadata():
    return {
        'pre_treatment_score': None,
        'post_treatment_score': 10.0
    }


@pytest.fixture
def non_numeric_metadata():
    return {
        'pre_treatment_score': "not_a_number",
        'post_treatment_score': 10.0
    }


class TestValidateMetadata:
    def test_valid_metadata_passes(self, valid_metadata):
        """Test that valid metadata returns True."""
        assert validate_metadata(valid_metadata) is True

    def test_missing_pre_treatment_score_halts(self, missing_pre_metadata, caplog, capsys):
        """Test that missing pre_treatment_score returns False and logs error."""
        with caplog.at_level(logging.ERROR):
            result = validate_metadata(missing_pre_metadata)
        
        assert result is False
        assert "Missing required metadata fields" in caplog.text
        assert "pre_treatment_score" in caplog.text

    def test_missing_post_treatment_score_halts(self, missing_post_metadata, caplog, capsys):
        """Test that missing post_treatment_score returns False and logs error."""
        with caplog.at_level(logging.ERROR):
            result = validate_metadata(missing_post_metadata)
        
        assert result is False
        assert "Missing required metadata fields" in caplog.text
        assert "post_treatment_score" in caplog.text

    def test_none_score_halts(self, none_score_metadata, caplog, capsys):
        """Test that None score value returns False and logs error."""
        with caplog.at_level(logging.ERROR):
            result = validate_metadata(none_score_metadata)
        
        assert result is False
        assert "is None" in caplog.text

    def test_non_numeric_score_halts(self, non_numeric_metadata, caplog, capsys):
        """Test that non-numeric score value returns False and logs error."""
        with caplog.at_level(logging.ERROR):
            result = validate_metadata(non_numeric_metadata)
        
        assert result is False
        assert "must be numeric" in caplog.text


class TestValidateSubjectMetadataPath:
    def test_file_not_found_returns_false(self, tmp_path):
        """Test that a non-existent file path returns False."""
        fake_path = tmp_path / "nonexistent.json"
        assert validate_subject_metadata_path(fake_path) is False

    def test_invalid_json_returns_false(self, tmp_path):
        """Test that invalid JSON content returns False."""
        file_path = tmp_path / "invalid.json"
        file_path.write_text("{ invalid json }")
        
        assert validate_subject_metadata_path(file_path) is False

    def test_valid_json_file_passes(self, tmp_path, valid_metadata):
        """Test that a valid JSON file with correct metadata passes."""
        file_path = tmp_path / "valid.json"
        with open(file_path, 'w') as f:
            json.dump(valid_metadata, f)
        
        assert validate_subject_metadata_path(file_path) is True

    def test_valid_json_file_missing_keys_fails(self, tmp_path, missing_pre_metadata):
        """Test that a valid JSON file with missing keys fails."""
        file_path = tmp_path / "missing_keys.json"
        with open(file_path, 'w') as f:
            json.dump(missing_pre_metadata, f)
        
        assert validate_subject_metadata_path(file_path) is False
