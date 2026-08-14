"""
Contract tests for the Reference Validator Agent.
"""
import os
import json
import yaml
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code/ to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from reference_validator import (
    ReferenceValidator,
    VerificationStatus,
    VerificationResult,
    CitationSchema
)


class TestCitationSchema:
    def test_valid_citation(self):
        data = {
            "doi": "10.1038/s41591-023-02456-7",
            "title": "Test Title",
            "source_type": "journal",
            "verified_date": "2023-01-01"
        }
        citation = CitationSchema(data)
        assert citation.data["doi"] == "10.1038/s41591-023-02456-7"

    def test_missing_field(self):
        data = {
            "doi": "10.1038/s41591-023-02456-7",
            "title": "Test Title"
            # missing source_type and verified_date
        }
        with pytest.raises(ValueError):
            CitationSchema(data)


class TestReferenceValidatorValidationMode:
    @pytest.fixture
    def mock_validation_mode(self, tmp_path):
        # Create a temporary directory structure mimicking the project
        metadata_dir = tmp_path / "data" / "metadata"
        metadata_dir.mkdir(parents=True)
        flag_file = metadata_dir / "validation_mode_flag.json"
        flag_file.write_text(json.dumps({"active": True}))
        return tmp_path

    def test_validation_mode_detected(self, mock_validation_mode):
        validator = ReferenceValidator()
        # Override the path for testing
        validator.VALIDATION_MODE_FLAG_PATH = mock_validation_mode / "data" / "metadata" / "validation_mode_flag.json"

        assert validator.is_validation_mode() is True

    def test_logic_only_status(self, mock_validation_mode):
        validator = ReferenceValidator()
        validator.VALIDATION_MODE_FLAG_PATH = mock_validation_mode / "data" / "metadata" / "validation_mode_flag.json"
        validator.VERIFIED_DOIS_PATH = mock_validation_mode / "data" / "citations" / "verified_dois.yaml" # Does not exist

        # Should pass without checking DOIs because mode is active
        result = validator.verify_citations()
        assert result.status == VerificationStatus.LOGIC_ONLY
        assert "Validation mode active" in result.message


class TestReferenceValidatorRealMode:
    @pytest.fixture
    def mock_real_mode(self, tmp_path):
        # Create structure without validation flag
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        return tmp_path

    def test_missing_citation_file_fails(self, mock_real_mode):
        validator = ReferenceValidator()
        validator.VALIDATION_MODE_FLAG_PATH = mock_real_mode / "data" / "metadata" / "validation_mode_flag.json"
        validator.VERIFIED_DOIS_PATH = mock_real_mode / "data" / "citations" / "verified_dois.yaml"

        result = validator.verify_citations()
        assert result.status == VerificationStatus.FAILED
        assert "not found" in result.message.lower()

    def test_empty_citation_registry_fails(self, mock_real_mode):
        # Create empty DOIs file
        citations_dir = mock_real_mode / "data" / "citations"
        citations_dir.mkdir()
        doi_file = citations_dir / "verified_dois.yaml"
        doi_file.write_text("dois: []")

        validator = ReferenceValidator()
        validator.VALIDATION_MODE_FLAG_PATH = mock_real_mode / "data" / "metadata" / "validation_mode_flag.json"
        validator.VERIFIED_DOIS_PATH = doi_file

        result = validator.verify_citations()
        assert result.status == VerificationStatus.FAILED
        assert "No verified DOIs found" in result.message

    def test_valid_citations_pass(self, mock_real_mode):
        # Create valid DOIs file
        citations_dir = mock_real_mode / "data" / "citations"
        citations_dir.mkdir()
        doi_file = citations_dir / "verified_dois.yaml"
        doi_file.write_text(yaml.dump({
            "dois": [
                {
                    "doi": "10.1038/s41591-023-02456-7",
                    "title": "Test",
                    "source_type": "journal",
                    "verified_date": "2023-01-01"
                }
            ]
        }))

        validator = ReferenceValidator()
        validator.VALIDATION_MODE_FLAG_PATH = mock_real_mode / "data" / "metadata" / "validation_mode_flag.json"
        validator.VERIFIED_DOIS_PATH = doi_file

        result = validator.verify_citations()
        assert result.status == VerificationStatus.PASSED
        assert "Verification passed" in result.message
