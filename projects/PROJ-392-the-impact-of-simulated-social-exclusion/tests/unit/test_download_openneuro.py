"""
Unit tests for download_openneuro.py
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data_download.download_openneuro import (
    check_dependencies,
    download_with_curl,
    validate_bids_structure,
    process_dataset,
    DATASETS
)


class TestCheckDependencies:
    def test_check_dependencies_returns_tuple(self):
        """Test that check_dependencies returns a tuple of bool and list."""
        result = check_dependencies()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], list)

    def test_check_dependencies_has_expected_structure(self):
        """Test that the return values have expected types."""
        is_available, missing = check_dependencies()
        assert isinstance(is_available, bool)
        assert isinstance(missing, list)
        # Missing should contain strings
        for item in missing:
            assert isinstance(item, str)


class TestDownloadWithCurl:
    def test_download_with_curl_invalid_dataset_id(self):
        """Test that invalid dataset ID returns False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = download_with_curl("invalid_dataset", output_dir)
            assert result is False

    def test_download_with_curl_creates_output_dir(self):
        """Test that download creates output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "new_dir"
            assert not output_dir.exists()
            
            # This will fail to download but should create the directory
            # We're testing directory creation, not download success
            try:
                download_with_curl("ds000246", output_dir)
            except Exception:
                pass  # Expected to fail in test environment
            
            # Directory should exist after the call
            assert output_dir.exists()


class TestValidateBidsStructure:
    def test_validate_bids_structure_missing_required_files(self):
        """Test validation fails when required files are missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = Path(tmpdir)
            # Create empty directory without required files
            is_valid, errors = validate_bids_structure(dataset_path)
            
            assert is_valid is False
            assert len(errors) > 0
            assert any("dataset_description.json" in error for error in errors)
            assert any("participants.tsv" in error for error in errors)

    def test_validate_bids_structure_with_required_files(self):
        """Test validation passes when required files exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = Path(tmpdir)
            
            # Create required files
            (dataset_path / "dataset_description.json").write_text(
                '{"Name": "Test", "BIDSVersion": "1.6.0"}'
            )
            (dataset_path / "participants.tsv").write_text("participant_id\nsub-01")
            
            # Create a fake subject directory
            sub_dir = dataset_path / "sub-01"
            sub_dir.mkdir()
            func_dir = sub_dir / "func"
            func_dir.mkdir()
            
            is_valid, errors = validate_bids_structure(dataset_path)
            
            # Should pass validation
            assert is_valid is True
            assert len(errors) == 0

    def test_validate_bids_structure_invalid_json(self):
        """Test validation fails when dataset_description.json is invalid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = Path(tmpdir)
            
            # Create invalid JSON
            (dataset_path / "dataset_description.json").write_text("{invalid json}")
            (dataset_path / "participants.tsv").write_text("participant_id\nsub-01")
            
            sub_dir = dataset_path / "sub-01"
            sub_dir.mkdir()
            
            is_valid, errors = validate_bids_structure(dataset_path)
            
            assert is_valid is False
            assert any("not valid JSON" in error for error in errors)


class TestProcessDataset:
    def test_process_dataset_creates_output_dir(self):
        """Test that process_dataset creates the output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_base = Path(tmpdir)
            dataset_id = "ds000246"
            
            result = process_dataset(dataset_id, output_base)
            
            # Directory should be created even if download fails
            output_dir = output_base / dataset_id
            assert output_dir.exists()

    def test_process_dataset_returns_false_for_invalid_dataset(self):
        """Test that process_dataset returns False for invalid dataset ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_base = Path(tmpdir)
            result = process_dataset("invalid_dataset", output_base)
            assert result is False


class TestDatasetConfig:
    def test_datasets_contains_required_ids(self):
        """Test that DATASETS contains both required dataset IDs."""
        assert "ds000246" in DATASETS
        assert "ds004738" in DATASETS

    def test_datasets_has_required_fields(self):
        """Test that each dataset has required configuration fields."""
        required_fields = ["name", "description", "url", "dataset_id", "task_label"]
        
        for dataset_id, config in DATASETS.items():
            for field in required_fields:
                assert field in config, f"Missing field '{field}' in {dataset_id}"

    def test_ds000246_is_exclusion_dataset(self):
        """Test that ds000246 is configured as exclusion dataset."""
        config = DATASETS["ds000246"]
        assert "exclusion" in config["name"].lower() or "cyberball" in config["name"].lower()

    def test_ds004738_is_reward_dataset(self):
        """Test that ds004738 is configured as reward dataset."""
        config = DATASETS["ds004738"]
        assert "reward" in config["name"].lower()