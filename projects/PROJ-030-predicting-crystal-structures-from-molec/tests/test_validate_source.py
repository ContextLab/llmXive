"""
Tests for the Reference-Validator integration (T008b).
"""

import pytest
import json
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import the module under test
# Note: We assume the test runner sets up the path correctly to import 'ingestion'
from code.ingestion.validate_source import (
    validate_source,
    get_dataset_metadata,
    verify_citation,
    save_validation_manifest,
    TARGET_DATASET_ID,
    EXPECTED_AUTHOR,
    EXPECTED_LICENSE,
    VALIDATION_MANIFEST_PATH
)
from code.exceptions import DownloadError, ValidationError


class TestGetDatasetMetadata:
    @patch('code.ingestion.validate_source.HfApi')
    def test_fetches_metadata_successfully(self, mock_hf_api_class):
        # Setup mock
        mock_api_instance = MagicMock()
        mock_hf_api_class.return_value = mock_api_instance

        mock_dataset_info = MagicMock()
        mock_dataset_info.id = TARGET_DATASET_ID
        mock_dataset_info.author = EXPECTED_AUTHOR
        mock_dataset_info.cardData = {
            "license": EXPECTED_LICENSE,
            "citation": "Test Citation",
            "description": "Test Description"
        }
        mock_dataset_info.lastModified = None

        mock_api_instance.dataset_info.return_value = mock_dataset_info

        # Execute
        result = get_dataset_metadata(TARGET_DATASET_ID)

        # Assert
        assert result["id"] == TARGET_DATASET_ID
        assert result["author"] == EXPECTED_AUTHOR
        assert result["license"] == EXPECTED_LICENSE
        mock_api_instance.dataset_info.assert_called_once_with(dataset_id=TARGET_DATASET_ID)

    @patch('code.ingestion.validate_source.HfApi')
    def test_raises_download_error_on_failure(self, mock_hf_api_class):
        mock_api_instance = MagicMock()
        mock_hf_api_class.return_value = mock_api_instance
        mock_api_instance.dataset_info.side_effect = Exception("Network Error")

        with pytest.raises(DownloadError, match="Unable to access dataset"):
            get_dataset_metadata(TARGET_DATASET_ID)


class TestVerifyCitation:
    def test_verifies_correct_author_and_license(self):
        metadata = {
            "author": "Crystallography Open Database",
            "license": "CC0-1.0"
        }
        # Should not raise
        result = verify_citation(metadata, EXPECTED_AUTHOR, EXPECTED_LICENSE)
        assert result is True

    def test_raises_validation_error_on_author_mismatch(self):
        metadata = {
            "author": "Fake Database",
            "license": "CC0-1.0"
        }
        with pytest.raises(ValidationError, match="Citation Author Mismatch"):
            verify_citation(metadata, EXPECTED_AUTHOR, EXPECTED_LICENSE)

    def test_raises_validation_error_on_license_mismatch(self):
        metadata = {
            "author": "Crystallography Open Database",
            "license": "MIT"
        }
        with pytest.raises(ValidationError, match="Citation License Mismatch"):
            verify_citation(metadata, EXPECTED_AUTHOR, EXPECTED_LICENSE)

    def test_case_insensitive_author_check(self):
        metadata = {
            "author": "crystallography open database",
            "license": "CC0-1.0"
        }
        # Should pass due to case insensitivity
        result = verify_citation(metadata, EXPECTED_AUTHOR, EXPECTED_LICENSE)
        assert result is True


class TestSaveValidationManifest:
    def test_saves_json_correctly(self, tmp_path):
        output_dir = tmp_path / "validation"
        output_file = output_dir / "manifest.json"

        metadata = {
            "id": "test/id",
            "author": "Test Author",
            "license": "CC0-1.0"
        }

        save_validation_manifest(metadata, "PASSED", str(output_file))

        assert output_file.exists()
        with open(output_file, 'r') as f:
            data = json.load(f)

        assert data["dataset_id"] == "test/id"
        assert data["verification_status"] == "PASSED"
        assert "timestamp" in data


class TestValidateSourceIntegration:
    @patch('code.ingestion.validate_source.get_dataset_metadata')
    @patch('code.ingestion.validate_source.verify_citation')
    @patch('code.ingestion.validate_source.save_validation_manifest')
    @patch('code.ingestion.validate_source.get_path_absolute')
    def test_full_validation_flow_success(
        self,
        mock_get_path,
        mock_save,
        mock_verify,
        mock_get_meta
    ):
        # Setup
        mock_get_path.return_value = "/tmp/test_manifest.json"
        mock_meta = {"id": "test", "author": "Test", "license": "CC0-1.0"}
        mock_get_meta.return_value = mock_meta

        # Execute
        result = validate_source()

        # Assert
        assert result is True
        mock_get_meta.assert_called_once()
        mock_verify.assert_called_once()
        mock_save.assert_called_once()

    @patch('code.ingestion.validate_source.get_dataset_metadata')
    def test_validation_fails_if_metadata_unavailable(self, mock_get_meta):
        mock_get_meta.side_effect = DownloadError("Network issue")

        with pytest.raises(DownloadError):
            validate_source()

    @patch('code.ingestion.validate_source.get_dataset_metadata')
    @patch('code.ingestion.validate_source.verify_citation')
    def test_validation_fails_if_citation_invalid(self, mock_verify, mock_get_meta):
        mock_meta = {"id": "test", "author": "Fake", "license": "CC0-1.0"}
        mock_get_meta.return_value = mock_meta
        mock_verify.side_effect = ValidationError("Author mismatch")

        with pytest.raises(ValidationError):
            validate_source()