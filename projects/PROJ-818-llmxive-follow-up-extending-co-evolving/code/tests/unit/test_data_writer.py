"""
Unit tests for data writing functionality.
"""

import pytest
import json
import tempfile
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.generators.data_writer import (
    write_dataset,
    register_checksum,
    generate_and_save_training_data,
    DataWriteError
)
from src.utils.config import Config, get_default_config


class TestDataWriter:
    """Test cases for data writing functionality."""

    @pytest.fixture
    def temp_config(self):
        """Create a temporary config for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = get_default_config()
            config.data_dir = Path(tmpdir)
            config.num_logic_proofs = 5
            config.num_grid_worlds = 5
            yield config

    @pytest.fixture
    def sample_data(self):
        """Create sample dataset for testing."""
        return [
            {"id": 1, "type": "logic", "proof": "A -> B"},
            {"id": 2, "type": "logic", "proof": "B -> C"},
            {"id": 3, "type": "grid", "grid": [[0, 1], [1, 0]]}
        ]

    def test_write_dataset_creates_file(self, temp_config, sample_data):
        """Test that write_dataset creates a valid JSON file."""
        output_path = temp_config.data_dir / "test_output.json"

        # Write data
        result_path = write_dataset(sample_data, output_path)

        # Verify file exists
        assert result_path.exists()
        assert result_path == output_path

        # Verify content
        with open(result_path, 'r') as f:
            loaded_data = json.load(f)

        assert loaded_data == sample_data

    def test_write_dataset_creates_parent_dirs(self, temp_config, sample_data):
        """Test that write_dataset creates parent directories if needed."""
        output_path = temp_config.data_dir / "subdir" / "nested" / "test.json"

        # This should not raise an error
        result_path = write_dataset(sample_data, output_path)

        assert result_path.exists()
        assert result_path.parent.exists()

    def test_write_dataset_empty_list(self, temp_config):
        """Test writing an empty list."""
        output_path = temp_config.data_dir / "empty.json"

        result_path = write_dataset([], output_path)

        assert result_path.exists()
        with open(result_path, 'r') as f:
            data = json.load(f)
        assert data == []

    def test_register_checksum_updates_file(self, temp_config, sample_data):
        """Test that register_checksum creates and updates checksums.json."""
        # First write a dataset
        output_path = temp_config.data_dir / "test_data.json"
        write_dataset(sample_data, output_path)

        # Register checksum
        register_checksum(output_path, "test_dataset", temp_config)

        # Verify checksums file exists
        checksums_path = temp_config.data_dir / "checksums.json"
        assert checksums_path.exists()

        # Verify content
        with open(checksums_path, 'r') as f:
            checksums = json.load(f)

        assert "test_dataset" in checksums
        assert "sha256" in checksums["test_dataset"]
        assert "file" in checksums["test_dataset"]
        assert "size_bytes" in checksums["test_dataset"]

        # Verify the file path is relative
        assert checksums["test_dataset"]["file"] == "test_data.json"

    def test_register_checksum_overwrites_existing(self, temp_config, sample_data):
        """Test that register_checksum updates existing entries."""
        output_path = temp_config.data_dir / "test_data.json"
        write_dataset(sample_data, output_path)

        # Register checksum twice
        register_checksum(output_path, "test_dataset", temp_config)
        register_checksum(output_path, "test_dataset", temp_config)

        # Should still have only one entry
        checksums_path = temp_config.data_dir / "checksums.json"
        with open(checksums_path, 'r') as f:
            checksums = json.load(f)

        assert len(checksums) == 1
        assert "test_dataset" in checksums

    def test_generate_and_save_training_data_creates_files(self, temp_config):
        """Test that generate_and_save_training_data creates both datasets."""
        # Set small numbers for testing
        temp_config.num_logic_proofs = 3
        temp_config.num_grid_worlds = 3

        result = generate_and_save_training_data(temp_config)

        # Check return value
        assert "logic_proofs_train" in result
        assert "grid_worlds_train" in result

        # Verify files exist
        logic_path = Path(result["logic_proofs_train"])
        grid_path = Path(result["grid_worlds_train"])

        assert logic_path.exists()
        assert grid_path.exists()

        # Verify checksums file
        checksums_path = temp_config.data_dir / "checksums.json"
        assert checksums_path.exists()

        with open(checksums_path, 'r') as f:
            checksums = json.load(f)

        assert "logic_proofs_train" in checksums
        assert "grid_worlds_train" in checksums

    def test_generate_and_save_training_data_valid_content(self, temp_config):
        """Test that generated datasets have valid content."""
        temp_config.num_logic_proofs = 2
        temp_config.num_grid_worlds = 2

        result = generate_and_save_training_data(temp_config)

        # Verify logic proofs
        with open(result["logic_proofs_train"], 'r') as f:
            logic_data = json.load(f)

        assert isinstance(logic_data, list)
        assert len(logic_data) == temp_config.num_logic_proofs
        for item in logic_data:
            assert "id" in item
            assert "proof" in item or "axioms" in item

        # Verify grid worlds
        with open(result["grid_worlds_train"], 'r') as f:
            grid_data = json.load(f)

        assert isinstance(grid_data, list)
        assert len(grid_data) == temp_config.num_grid_worlds
        for item in grid_data:
            assert "id" in item
            assert "grid" in item or "nodes" in item

    def test_write_dataset_invalid_path(self, temp_config, sample_data):
        """Test writing to an invalid path raises error."""
        # Use a path that should fail (e.g., trying to write to a file that is a directory)
        invalid_path = temp_config.data_dir / "invalid"

        # Create a directory with the same name
        invalid_path.mkdir(parents=True, exist_ok=True)

        with pytest.raises(DataWriteError):
            write_dataset(sample_data, invalid_path)