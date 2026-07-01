"""
Unit tests for the dataset design verification module.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path

from src.datasets.verify_design import (
    validate_metadata_fields,
    validate_design_logic,
    verify_dataset_design,
    DesignVerificationError
)


class TestValidateMetadataFields:
    """Tests for validate_metadata_fields function."""

    def test_valid_metadata(self):
        """Test with all required fields present and correct types."""
        metadata = {
            'pre_scan_count': 1,
            'post_scan_count': 1,
            'intervention_type': 'mindfulness',
            'scan_type': 'rs-fMRI'
        }
        is_valid, errors = validate_metadata_fields(metadata)
        assert is_valid is True
        assert errors == []

    def test_missing_field(self):
        """Test with a missing required field."""
        metadata = {
            'pre_scan_count': 1,
            'post_scan_count': 1,
            'intervention_type': 'mindfulness'
        }
        is_valid, errors = validate_metadata_fields(metadata)
        assert is_valid is False
        assert "Missing required field: scan_type" in errors

    def test_wrong_type(self):
        """Test with incorrect field types."""
        metadata = {
            'pre_scan_count': '1',  # Should be int
            'post_scan_count': 1,
            'intervention_type': 'mindfulness',
            'scan_type': 'rs-fMRI'
        }
        is_valid, errors = validate_metadata_fields(metadata)
        assert is_valid is False
        assert any("pre_scan_count" in err for err in errors)

    def test_multiple_errors(self):
        """Test with multiple missing and invalid fields."""
        metadata = {
            'pre_scan_count': '1',
            'intervention_type': 123
        }
        is_valid, errors = validate_metadata_fields(metadata)
        assert is_valid is False
        assert len(errors) == 3  # pre_scan_count type, intervention_type type, missing post_scan_count, missing scan_type


class TestValidateDesignLogic:
    """Tests for validate_design_logic function."""

    def test_valid_design(self):
        """Test with valid design logic."""
        metadata = {
            'pre_scan_count': 2,
            'post_scan_count': 2,
            'intervention_type': 'MBSR Training',
            'scan_type': 'rs-fMRI'
        }
        is_valid, errors = validate_design_logic(metadata)
        assert is_valid is True
        assert errors == []

    def test_zero_pre_scan(self):
        """Test with zero pre-scan count."""
        metadata = {
            'pre_scan_count': 0,
            'post_scan_count': 2,
            'intervention_type': 'mindfulness',
            'scan_type': 'resting'
        }
        is_valid, errors = validate_design_logic(metadata)
        assert is_valid is False
        assert any("pre_scan_count" in err for err in errors)

    def test_invalid_intervention_type(self):
        """Test with invalid intervention type."""
        metadata = {
            'pre_scan_count': 1,
            'post_scan_count': 1,
            'intervention_type': 'Yoga',
            'scan_type': 'rs-fMRI'
        }
        is_valid, errors = validate_design_logic(metadata)
        assert is_valid is False
        assert any("intervention_type" in err for err in errors)

    def test_invalid_scan_type(self):
        """Test with invalid scan type."""
        metadata = {
            'pre_scan_count': 1,
            'post_scan_count': 1,
            'intervention_type': 'mindfulness',
            'scan_type': 'task-fMRI'
        }
        is_valid, errors = validate_design_logic(metadata)
        assert is_valid is False
        assert any("scan_type" in err for err in errors)

    def test_case_insensitive_intervention(self):
        """Test that intervention type matching is case-insensitive."""
        metadata = {
            'pre_scan_count': 1,
            'post_scan_count': 1,
            'intervention_type': 'MBC Program',
            'scan_type': 'resting'
        }
        is_valid, errors = validate_design_logic(metadata)
        assert is_valid is True

    def test_resting_scan_type(self):
        """Test that 'resting' is a valid scan type."""
        metadata = {
            'pre_scan_count': 1,
            'post_scan_count': 1,
            'intervention_type': 'mindfulness',
            'scan_type': 'resting'
        }
        is_valid, errors = validate_design_logic(metadata)
        assert is_valid is True


class TestVerifyDatasetDesign:
    """Tests for verify_dataset_design function."""

    def test_verify_with_valid_metadata_file(self):
        """Test verification with a valid metadata file."""
        metadata = {
            'pre_scan_count': 1,
            'post_scan_count': 1,
            'intervention_type': 'mindfulness',
            'scan_type': 'rs-fMRI'
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(metadata, f)
            temp_path = f.name

        try:
            result = verify_dataset_design("test_dataset", temp_path)
            assert result["verified"] is True
            assert result["dataset_id"] == "test_dataset"
            assert result["metadata"] == metadata
        finally:
            os.unlink(temp_path)

    def test_verify_with_invalid_metadata_file(self):
        """Test verification with invalid metadata (missing fields)."""
        metadata = {
            'pre_scan_count': 0,
            'intervention_type': 'Yoga'
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(metadata, f)
            temp_path = f.name

        try:
            result = verify_dataset_design("test_dataset", temp_path)
            assert result["verified"] is False
            assert len(result["field_validation"]["errors"]) > 0
            assert len(result["logic_validation"]["errors"]) > 0
        finally:
            os.unlink(temp_path)

    def test_verify_with_nonexistent_file(self):
        """Test verification when metadata file does not exist."""
        result = verify_dataset_design("test_dataset", "/nonexistent/path/file.json")
        assert result["verified"] is False
        assert "No metadata file found" in result["message"]
        assert result["field_validation"]["errors"] == ["No metadata file found"]