"""
Unit tests for code/data/validate.py.
Specifically tests the "Real Data Only" enforcement and failure modes.
"""
import pytest
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.validate import validate_metadata, validate_subject_metadata_path, FatalError
from code.config import Config

class TestValidateMetadata:
    def test_valid_metadata(self):
        """Test validation with all required variables present."""
        metadata = {
            'pre_treatment_score': 15.0,
            'post_treatment_score': 10.0,
            'anxiety_instrument': 'GAD-7'
        }
        is_valid, errors = validate_metadata(metadata)
        assert is_valid is True
        assert errors == []

    def test_missing_pre_treatment_score(self):
        """Test validation fails when pre_treatment_score is missing."""
        metadata = {
            'post_treatment_score': 10.0,
            'anxiety_instrument': 'GAD-7'
        }
        is_valid, errors = validate_metadata(metadata)
        assert is_valid is False
        assert 'pre_treatment_score' in errors

    def test_missing_post_treatment_score(self):
        """Test validation fails when post_treatment_score is missing."""
        metadata = {
            'pre_treatment_score': 15.0,
            'anxiety_instrument': 'GAD-7'
        }
        is_valid, errors = validate_metadata(metadata)
        assert is_valid is False
        assert 'post_treatment_score' in errors

    def test_missing_anxiety_instrument(self):
        """Test validation fails when anxiety_instrument is missing."""
        metadata = {
            'pre_treatment_score': 15.0,
            'post_treatment_score': 10.0
        }
        is_valid, errors = validate_metadata(metadata)
        assert is_valid is False
        assert 'anxiety_instrument' in errors

    def test_invalid_anxiety_instrument(self):
        """Test validation fails with an invalid anxiety instrument."""
        metadata = {
            'pre_treatment_score': 15.0,
            'post_treatment_score': 10.0,
            'anxiety_instrument': 'INVALID_INSTRUMENT'
        }
        is_valid, errors = validate_metadata(metadata)
        assert is_valid is False
        assert 'Invalid anxiety instrument: INVALID_INSTRUMENT' in errors

    def test_none_values(self):
        """Test validation fails when required variables are None."""
        metadata = {
            'pre_treatment_score': None,
            'post_treatment_score': 10.0,
            'anxiety_instrument': 'GAD-7'
        }
        is_valid, errors = validate_metadata(metadata)
        assert is_valid is False
        assert 'pre_treatment_score' in errors

class TestValidateSubjectMetadataPath:
    def test_valid_file(self, tmp_path):
        """Test validation passes with a valid JSON file."""
        valid_data = {'subject_id': 'sub-001', 'data': 'real'}
        file_path = tmp_path / "metadata.json"
        with open(file_path, 'w') as f:
            json.dump(valid_data, f)
        
        assert validate_subject_metadata_path(file_path) is True

    def test_missing_file(self, tmp_path):
        """Test validation raises FatalError when file is missing."""
        file_path = tmp_path / "nonexistent.json"
        with pytest.raises(FatalError) as excinfo:
            validate_subject_metadata_path(file_path)
        assert "Subject metadata file missing" in str(excinfo.value)

    def test_invalid_json(self, tmp_path):
        """Test validation raises FatalError when file is not valid JSON."""
        file_path = tmp_path / "invalid.json"
        with open(file_path, 'w') as f:
            f.write("not valid json {")
        
        with pytest.raises(FatalError) as excinfo:
            validate_subject_metadata_path(file_path)
        assert "Subject metadata file is invalid JSON" in str(excinfo.value)

    def test_empty_file(self, tmp_path):
        """Test validation raises FatalError when file is empty."""
        file_path = tmp_path / "empty.json"
        with open(file_path, 'w') as f:
            f.write("{}") # Empty dict is technically valid JSON but we might want to check content
            # However, the spec says "empty or a placeholder". 
            # Let's test the specific case of an empty file (0 bytes) or just empty dict if logic dictates.
            # The current logic: if not data: raise. {} is falsy in "if not data".
        
        with pytest.raises(FatalError) as excinfo:
            validate_subject_metadata_path(file_path)
        assert "Subject metadata file is empty" in str(excinfo.value)

class TestRealDataOnlyEnforcement:
    """
    Tests specifically for the T043 requirement:
    Ensure the pipeline crashes with a detailed error log on failure,
    and does NOT fall back to synthetic data.
    """
    
    def test_no_synthetic_fallback_on_missing_file(self, tmp_path):
        """
        Verify that when a subject's data file is missing, 
        the system raises FatalError and does not generate synthetic data.
        """
        file_path = tmp_path / "missing_subject.json"
        
        # Attempt to validate - should raise FatalError
        with pytest.raises(FatalError) as excinfo:
            validate_subject_metadata_path(file_path)
        
        # Verify the error message indicates real data requirement
        assert "Real data required" in str(excinfo.value)
        assert "missing" in str(excinfo.value).lower()

    def test_no_synthetic_fallback_on_invalid_json(self, tmp_path):
        """
        Verify that when a subject's data file is corrupt, 
        the system raises FatalError and does not generate synthetic data.
        """
        file_path = tmp_path / "corrupt_subject.json"
        with open(file_path, 'w') as f:
            f.write("{ broken json }")
        
        with pytest.raises(FatalError) as excinfo:
            validate_subject_metadata_path(file_path)
        
        assert "Real data required" in str(excinfo.value)
        assert "invalid JSON" in str(excinfo.value)

    def test_run_validation_halts_on_missing_verified_sources(self, tmp_path, monkeypatch):
        """
        Verify that run_validation raises FatalError if verified_sources.json is missing,
        instead of attempting to fetch synthetic data or proceeding.
        """
        # Mock Config to point to a temp dir where the file doesn't exist
        class MockConfig:
            VERIFIED_SOURCES_PATH = tmp_path / "verified_sources.json"
        
        monkeypatch.setattr("code.data.validate.Config", MockConfig)
        
        from code.data.validate import run_validation
        
        with pytest.raises(FatalError) as excinfo:
            run_validation()
        
        assert "Missing verified dataset source" in str(excinfo.value)
        assert "Run T001a first" in str(excinfo.value)