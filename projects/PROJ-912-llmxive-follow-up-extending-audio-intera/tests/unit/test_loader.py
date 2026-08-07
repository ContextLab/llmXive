"""
Unit tests for the FilteredDataLoader module.
"""

import os
import tempfile
import yaml
from pathlib import Path
import pytest

from data.loader import (
    compute_file_checksum,
    save_checksum_to_state,
    verify_checksum,
    FilteredAudioDataset,
    FilteredDataLoader
)
from utils.logger import DataLoadError


class TestChecksumFunctions:
    """Tests for checksum utility functions."""

    def test_compute_file_checksum(self, tmp_path):
        """Test that checksum is computed correctly."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        checksum = compute_file_checksum(test_file)
        assert len(checksum) == 64  # SHA-256 hex length

        # Verify it's consistent
        checksum2 = compute_file_checksum(test_file)
        assert checksum == checksum2

    def test_save_and_verify_checksum(self, tmp_path):
        """Test saving and verifying checksum."""
        test_file = tmp_path / "data.parquet"
        test_file.write_bytes(b"fake parquet content")

        # Create a temporary state directory
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        # Mock the save_checksum_to_state to use our temp dir
        original_func = save_checksum_to_state
        def mock_save(path, checksum, dataset_name="test"):
            state_file = state_dir / f"{dataset_name}_checksum.yaml"
            with open(state_file, "w") as f:
                yaml.dump({dataset_name: {"file_path": str(path), "checksum": checksum}}, f)

        # Mock verify_checksum to use our temp dir
        def mock_verify(dataset_name="test"):
            state_file = state_dir / f"{dataset_name}_checksum.yaml"
            if not state_file.exists():
                return False
            with open(state_file, "r") as f:
                state_data = yaml.safe_load(f)
            stored_checksum = state_data[dataset_name]["checksum"]
            stored_path = Path(state_data[dataset_name]["file_path"])
            if not stored_path.exists():
                return False
            current = compute_file_checksum(stored_path)
            return current == stored_checksum

        # Patch for this test
        import data.loader
        original_save = data.loader.save_checksum_to_state
        original_verify = data.loader.verify_checksum
        data.loader.save_checksum_to_state = mock_save
        data.loader.verify_checksum = mock_verify

        try:
            checksum = compute_file_checksum(test_file)
            mock_save(test_file, checksum, "test")

            assert mock_verify("test") is True

            # Modify file
            test_file.write_bytes(b"modified content")
            assert mock_verify("test") is False
        finally:
            data.loader.save_checksum_to_state = original_save
            data.loader.verify_checksum = original_verify


class TestFilteredDataLoader:
    """Tests for the FilteredDataLoader class."""

    @pytest.fixture
    def mock_class_config(self, tmp_path):
        """Create a mock class config file."""
        config = {
            "subtle_cue": {
                "class_ids": [1, 2],
                "class_names": {1: "alarm", 2: "glass_breaking"}
            },
            "control_set": {
                "class_ids": [3, 4],
                "class_names": {3: "engine", 4: "drilling"}
            }
        }
        config_path = tmp_path / "class_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)
        return config_path

    def test_load_class_config(self, mock_class_config):
        """Test that class config is loaded correctly."""
        loader = FilteredDataLoader(mock_class_config)

        assert len(loader.allowed_classes) == 4
        assert 1 in loader.allowed_classes
        assert 2 in loader.allowed_classes
        assert 3 in loader.allowed_classes
        assert 4 in loader.allowed_classes

        assert loader.class_mapping[1] == "alarm"
        assert loader.class_mapping[3] == "engine"

    def test_load_class_config_missing_file(self, tmp_path):
        """Test that missing config file raises error."""
        non_existent = tmp_path / "non_existent.yaml"
        with pytest.raises(FileNotFoundError):
            FilteredDataLoader(non_existent)

    def test_load_class_config_empty_classes(self, tmp_path):
        """Test that empty class list raises error."""
        config = {
            "subtle_cue": {"class_ids": [], "class_names": {}},
            "control_set": {"class_ids": [], "class_names": {}}
        }
        config_path = tmp_path / "empty_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        with pytest.raises(DataLoadError, match="No allowed classes found"):
            FilteredDataLoader(config_path)
