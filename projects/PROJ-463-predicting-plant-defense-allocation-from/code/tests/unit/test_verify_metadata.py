"""
Unit tests for metadata verification module.
"""

import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.verify_metadata import (
    verify_metadata_requirements,
    verify_fastq_metadata,
    verify_synthetic_metadata,
    save_verification_report,
)


class TestVerifyMetadataRequirements:
    """Tests for verify_metadata_requirements function."""

    def test_valid_metadata(self):
        """Test with valid metadata that meets all requirements."""
        metadata = {
            "species": "Arabidopsis thaliana",
            "tissue": "leaf",
            "treatment": "herbivory",
            "replicates": 3,
        }
        is_valid, reason = verify_metadata_requirements(metadata)
        assert is_valid is True
        assert reason is None

    def test_missing_tissue(self):
        """Test with missing tissue metadata."""
        metadata = {
            "species": "Arabidopsis thaliana",
            "tissue": None,
            "treatment": "herbivory",
            "replicates": 3,
        }
        is_valid, reason = verify_metadata_requirements(metadata)
        assert is_valid is False
        assert "tissue" in reason

    def test_insufficient_replicates(self):
        """Test with insufficient replicates."""
        metadata = {
            "species": "Arabidopsis thaliana",
            "tissue": "leaf",
            "treatment": "herbivory",
            "replicates": 1,
        }
        is_valid, reason = verify_metadata_requirements(metadata)
        assert is_valid is False
        assert "replicates" in reason

    def test_empty_treatment(self):
        """Test with empty treatment metadata."""
        metadata = {
            "species": "Arabidopsis thaliana",
            "tissue": "leaf",
            "treatment": "",
            "replicates": 3,
        }
        is_valid, reason = verify_metadata_requirements(metadata)
        assert is_valid is False
        assert "treatment" in reason


class TestVerifySyntheticMetadata:
    """Tests for verify_synthetic_metadata function."""

    def test_valid_synthetic_report(self):
        """Test with a valid synthetic report file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            report_data = {
                "studies": [
                    {
                        "accession_id": "SYNTH_001",
                        "species": "Arabidopsis thaliana",
                        "tissue": "leaf",
                        "treatment": "herbivory",
                        "replicates": 3,
                        "exclusion_reason": None,
                    }
                ]
            }
            json.dump(report_data, f)
            temp_path = f.name

        try:
            result = verify_synthetic_metadata(temp_path)
            assert result["accession_id"] == "SYNTH_001"
            assert result["species"] == "Arabidopsis thaliana"
            assert result["tissue"] == "leaf"
            assert result["treatment"] == "herbivory"
            assert result["replicates"] == 3
            assert result["exclusion_reason"] is None
            assert result["mode"] == "synthetic"
            assert result["real_data_available"] is False
        finally:
            os.unlink(temp_path)

    def test_invalid_report_file(self):
        """Test with an invalid report file path."""
        result = verify_synthetic_metadata("/nonexistent/path/report.json")
        assert result["exclusion_reason"] is not None
        assert "Failed to read" in result["exclusion_reason"]
        assert result["mode"] == "synthetic"
        assert result["real_data_available"] is False


class TestSaveVerificationReport:
    """Tests for save_verification_report function."""

    def test_save_report(self):
        """Test saving a verification report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_report.json")
            report = {
                "studies": [
                    {
                        "accession_id": "TEST_001",
                        "species": "Test Species",
                        "tissue": "test_tissue",
                        "treatment": "test_treatment",
                        "replicates": 2,
                        "exclusion_reason": None,
                        "mode": "synthetic",
                        "real_data_available": False,
                    }
                ]
            }

            save_verification_report(report, output_path)

            # Verify file was created
            assert os.path.exists(output_path)

            # Verify content
            with open(output_path, "r") as f:
                saved_report = json.load(f)

            assert saved_report == report