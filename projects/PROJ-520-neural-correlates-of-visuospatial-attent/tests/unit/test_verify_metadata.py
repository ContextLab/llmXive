"""
Unit tests for verify_metadata.py (T051 verification script).
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from verify_metadata import (
    load_metadata,
    verify_required_fields,
    check_for_synthetic_indicators,
    validate_metadata
)

class TestLoadMetadata:
    def test_load_valid_metadata(self, tmp_path):
        """Test loading a valid metadata file."""
        metadata_file = tmp_path / "metadata.json"
        test_data = {
            "data_source_url": "https://openneuro.org/datasets/ds0001171",
            "fetch_method": "mne.datasets.openneuro.fetch"
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(test_data, f)
        
        result = load_metadata(metadata_file)
        assert result is not None
        assert result["data_source_url"] == test_data["data_source_url"]
        assert result["fetch_method"] == test_data["fetch_method"]

    def test_load_missing_file(self, tmp_path):
        """Test loading a non-existent file."""
        missing_file = tmp_path / "nonexistent.json"
        result = load_metadata(missing_file)
        assert result is None

    def test_load_invalid_json(self, tmp_path):
        """Test loading a file with invalid JSON."""
        metadata_file = tmp_path / "invalid.json"
        with open(metadata_file, 'w') as f:
            f.write("{ invalid json }")
        
        result = load_metadata(metadata_file)
        assert result is None

class TestVerifyRequiredFields:
    def test_all_fields_present(self):
        """Test when all required fields are present."""
        metadata = {
            "data_source_url": "https://example.com",
            "fetch_method": "method_name",
            "other_field": "value"
        }
        assert verify_required_fields(metadata) is True

    def test_missing_data_source_url(self):
        """Test when data_source_url is missing."""
        metadata = {
            "fetch_method": "method_name"
        }
        assert verify_required_fields(metadata) is False

    def test_missing_fetch_method(self):
        """Test when fetch_method is missing."""
        metadata = {
            "data_source_url": "https://example.com"
        }
        assert verify_required_fields(metadata) is False

    def test_empty_data_source_url(self):
        """Test when data_source_url is empty."""
        metadata = {
            "data_source_url": "",
            "fetch_method": "method_name"
        }
        assert verify_required_fields(metadata) is False

class TestCheckForSyntheticIndicators:
    def test_clean_metadata(self):
        """Test metadata without synthetic indicators."""
        metadata = {
            "data_source_url": "https://openneuro.org/datasets/ds0001171",
            "fetch_method": "mne.datasets.openneuro.fetch",
            "subject_count": 10,
            "processing_date": "2024-01-01"
        }
        assert check_for_synthetic_indicators(metadata) is True

    def test_synthetic_in_value(self):
        """Test metadata with synthetic in value."""
        metadata = {
            "data_source_url": "https://example.com/synthetic_data",
            "fetch_method": "method_name"
        }
        assert check_for_synthetic_indicators(metadata) is False

    def test_fallback_in_key(self):
        """Test metadata with fallback in key."""
        metadata = {
            "data_source_url": "https://example.com",
            "fallback_method": "landmark_timestamps"
        }
        assert check_for_synthetic_indicators(metadata) is False

    def test_nested_synthetic(self, tmp_path):
        """Test metadata with synthetic in nested structure."""
        metadata = {
            "data_source_url": "https://example.com",
            "fetch_method": "method_name",
            "processing_info": {
                "status": "generated",
                "details": "This is fake data"
            }
        }
        assert check_for_synthetic_indicators(metadata) is False

class TestValidateMetadata:
    def test_full_validation_success(self, tmp_path):
        """Test complete validation with valid metadata."""
        metadata_file = tmp_path / "metadata.json"
        test_data = {
            "data_source_url": "https://openneuro.org/datasets/ds0001171",
            "fetch_method": "mne.datasets.openneuro.fetch",
            "subject_count": 10
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(test_data, f)
        
        result = validate_metadata(metadata_file)
        assert result is True

    def test_full_validation_missing_fields(self, tmp_path):
        """Test complete validation with missing fields."""
        metadata_file = tmp_path / "metadata.json"
        test_data = {
            "fetch_method": "method_name"
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(test_data, f)
        
        result = validate_metadata(metadata_file)
        assert result is False

    def test_full_validation_synthetic(self, tmp_path):
        """Test complete validation with synthetic indicators."""
        metadata_file = tmp_path / "metadata.json"
        test_data = {
            "data_source_url": "https://example.com/synthetic",
            "fetch_method": "method_name"
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(test_data, f)
        
        result = validate_metadata(metadata_file)
        assert result is False