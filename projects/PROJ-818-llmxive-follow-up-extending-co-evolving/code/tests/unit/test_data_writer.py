import json
import os
import tempfile
from pathlib import Path
import pytest
import sys

from src.generators.data_writer import (
    write_dataset,
    register_checksum,
    generate_and_save_training_data,
    DataWriteError
)
from src.utils.config import Config

class TestDataWriter:
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            yield Path(tmp)

    def test_write_dataset_creates_file(self, temp_dir):
        data = [{"id": 1, "value": "test"}]
        output_path = temp_dir / "test.json"
        
        write_dataset(data, output_path)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        assert loaded == data

    def test_register_checksum_updates_manifest(self, temp_dir):
        # Create a dummy file
        file_path = temp_dir / "dummy.txt"
        file_path.write_text("test content")
        
        checksums_path = temp_dir / "checksums.json"
        checksums_path.write_text("{}") # Initialize empty manifest
        
        register_checksum(file_path, checksums_path)
        
        with open(checksums_path, 'r') as f:
            checksums = json.load(f)
        
        assert str(file_path) in checksums
        assert checksums[str(file_path)] is not None
        assert len(checksums[str(file_path)]) == 64 # SHA-256 hex length

    def test_generate_and_save_training_data(self, temp_dir):
        logic_data = [{"type": "logic", "proof": "A->B"}]
        grid_data = [{"type": "grid", "map": "111"}]
        
        config = Config(
            seed=42,
            num_logic_proofs=1,
            num_grid_worlds=1,
            data_dir=str(temp_dir)
        )
        
        files = generate_and_save_training_data(logic_data, grid_data, config)
        
        assert len(files) == 2
        assert any("logic_training.json" in str(f) for f in files)
        assert any("grid_training.json" in str(f) for f in files)
        
        # Verify checksums file exists and contains entries
        checksums_path = temp_dir / "checksums.json"
        assert checksums_path.exists()
        
        with open(checksums_path, 'r') as f:
            checksums = json.load(f)
        
        assert len(checksums) == 2

    def test_write_dataset_creates_directories(self, temp_dir):
        deep_path = temp_dir / "sub" / "deep" / "data.json"
        data = [{"test": True}]
        
        write_dataset(data, deep_path)
        
        assert deep_path.exists()
        assert deep_path.parent.exists()

    def test_register_checksum_fails_if_file_missing(self, temp_dir):
        non_existent = temp_dir / "missing.txt"
        checksums_path = temp_dir / "checksums.json"
        checksums_path.write_text("{}")
        
        with pytest.raises(DataWriteError):
            register_checksum(non_existent, checksums_path)