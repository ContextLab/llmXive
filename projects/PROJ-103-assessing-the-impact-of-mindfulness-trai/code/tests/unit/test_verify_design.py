"""
Unit tests for the dataset design verification module.
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.datasets.verify_design import (
    DesignVerificationError,
    DesignMetadata,
    validate_metadata_fields,
    validate_design_logic,
    verify_dataset_design,
    verify_all_datasets
)


class TestValidateMetadataFields:
    """Tests for validate_metadata_fields function."""

    def test_valid_metadata(self):
        """Test with fully valid metadata."""
        metadata = {
            "pre_scan_count": 10,
            "post_scan_count": 10,
            "intervention_type": "mindfulness",
            "scan_type": "rs-fMRI"
        }
        is_valid, errors = validate_metadata_fields(metadata)
        assert is_valid is True
        assert len(errors) == 0

    def test_missing_field(self):
        """Test with a missing required field."""
        metadata = {
            "pre_scan_count": 10,
            "post_scan_count": 10,
            "intervention_type": "mindfulness"
        }
        is_valid, errors = validate_metadata_fields(metadata)
        assert is_valid is False
        assert "Missing required field: scan_type" in errors

    def test_invalid_pre_scan_count_zero(self):
        """Test with pre_scan_count = 0."""
        metadata = {
            "pre_scan_count": 0,
            "post_scan_count": 10,
            "intervention_type": "mindfulness",
            "scan_type": "rs-fMRI"
        }
        is_valid, errors = validate_metadata_fields(metadata)
        assert is_valid is False
        assert any("pre_scan_count must be > 0" in e for e in errors)

    def test_invalid_intervention_type(self):
        """Test with invalid intervention type."""
        metadata = {
            "pre_scan_count": 10,
            "post_scan_count": 10,
            "intervention_type": "yoga",
            "scan_type": "rs-fMRI"
        }
        is_valid, errors = validate_metadata_fields(metadata)
        assert is_valid is False
        assert any("intervention_type must match" in e for e in errors)

    def test_case_insensitive_intervention(self):
        """Test case-insensitive intervention type matching."""
        metadata = {
            "pre_scan_count": 10,
            "post_scan_count": 10,
            "intervention_type": "MBSR",
            "scan_type": "resting"
        }
        is_valid, errors = validate_metadata_fields(metadata)
        assert is_valid is True

    def test_invalid_scan_type(self):
        """Test with invalid scan type."""
        metadata = {
            "pre_scan_count": 10,
            "post_scan_count": 10,
            "intervention_type": "mindfulness",
            "scan_type": "task-fMRI"
        }
        is_valid, errors = validate_metadata_fields(metadata)
        assert is_valid is False
        assert any("scan_type must be one of" in e for e in errors)


class TestValidateDesignLogic:
    """Tests for validate_design_logic function."""

    def test_valid_logic(self):
        """Test with valid design logic."""
        metadata = {
            "pre_scan_count": 5,
            "post_scan_count": 5,
            "intervention_type": "MBC",
            "scan_type": "resting"
        }
        is_valid, errors = validate_design_logic(metadata)
        assert is_valid is True
        assert len(errors) == 0

    def test_zero_pre_scan(self):
        """Test with zero pre_scan_count."""
        metadata = {
            "pre_scan_count": 0,
            "post_scan_count": 5,
            "intervention_type": "mindfulness",
            "scan_type": "rs-fMRI"
        }
        is_valid, errors = validate_design_logic(metadata)
        assert is_valid is False
        assert any("pre and post scans" in e for e in errors)


class TestVerifyDatasetDesign:
    """Tests for verify_dataset_design function."""

    @patch("src.datasets.verify_design.get_data_dir")
    def test_missing_design_file(self, mock_get_data_dir):
        """Test when design.json is missing."""
        mock_get_data_dir.return_value = "/mock/data"
        dataset_id = "ds000001"

        result = verify_dataset_design(dataset_id)

        assert result.is_valid is False
        assert "Design metadata file not found" in result.validation_errors[0]

    @patch("src.datasets.verify_design.get_data_dir")
    def test_valid_design_file(self, mock_get_data_dir):
        """Test with a valid design.json file."""
        mock_get_data_dir.return_value = "/mock/data"
        dataset_id = "ds000001"

        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_dir = Path(tmpdir) / "raw" / dataset_id
            raw_dir.mkdir(parents=True)
            design_file = raw_dir / "design.json"

            metadata = {
                "pre_scan_count": 10,
                "post_scan_count": 10,
                "intervention_type": "mindfulness",
                "scan_type": "rs-fMRI"
            }
            with open(design_file, "w") as f:
                json.dump(metadata, f)

            with patch("src.datasets.verify_design.get_data_dir", return_value=tmpdir):
                result = verify_dataset_design(dataset_id)

            assert result.is_valid is True
            assert result.pre_scan_count == 10
            assert result.post_scan_count == 10
            assert result.intervention_type == "mindfulness"
            assert result.scan_type == "rs-fMRI"

    @patch("src.datasets.verify_design.get_data_dir")
    def test_invalid_json(self, mock_get_data_dir):
        """Test with invalid JSON in design file."""
        mock_get_data_dir.return_value = "/mock/data"
        dataset_id = "ds000001"

        with tempfile.TemporaryDirectory() as tmpdir:
            raw_dir = Path(tmpdir) / "raw" / dataset_id
            raw_dir.mkdir(parents=True)
            design_file = raw_dir / "design.json"

            with open(design_file, "w") as f:
                f.write("{ invalid json }")

            with patch("src.datasets.verify_design.get_data_dir", return_value=tmpdir):
                result = verify_dataset_design(dataset_id)

            assert result.is_valid is False
            assert any("Invalid JSON" in e for e in result.validation_errors)


class TestVerifyAllDatasets:
    """Tests for verify_all_datasets function."""

    @patch("src.datasets.verify_design.get_data_dir")
    def test_verify_all_discovered(self, mock_get_data_dir):
        """Test verifying all datasets in the raw directory."""
        mock_get_data_dir.return_value = "/mock/data"

        with tempfile.TemporaryDirectory() as tmpdir:
            raw_dir = Path(tmpdir) / "raw"
            raw_dir.mkdir()

            # Create two valid datasets
            for ds_id in ["ds000001", "ds000002"]:
                ds_dir = raw_dir / ds_id
                ds_dir.mkdir()
                design_file = ds_dir / "design.json"
                with open(design_file, "w") as f:
                    json.dump({
                        "pre_scan_count": 5,
                        "post_scan_count": 5,
                        "intervention_type": "mindfulness",
                        "scan_type": "rs-fMRI"
                    }, f)

            with patch("src.datasets.verify_design.get_data_dir", return_value=tmpdir):
                results = verify_all_datasets()

            assert len(results) == 2
            assert all(r.is_valid for r in results)

    def test_verify_specific_ids(self):
        """Test verifying a specific list of dataset IDs."""
        # This test would require mocking the file system access
        # For now, we verify the function signature and basic logic
        # by ensuring it returns an empty list if directory doesn't exist
        with patch("src.datasets.verify_design.get_data_dir") as mock_get:
            mock_get.return_value = "/nonexistent/path"
            results = verify_all_datasets(["ds000001"])
            assert results == []