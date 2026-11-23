import json
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.generators.data_writer import write_dataset, register_checksum, generate_and_save_training_data, DataWriteError
from src.utils.checksums import load_checksums

class TestDataWriter:
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test artifacts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_write_dataset_creates_file(self, temp_dir):
        """Test that write_dataset creates a valid JSON file."""
        data = [{"id": 1, "value": "test"}, {"id": 2, "value": "test2"}]
        output_path = os.path.join(temp_dir, "test_data.json")
        
        write_dataset(data, output_path)
        
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            loaded_data = json.load(f)
        
        assert loaded_data == data

    def test_write_dataset_creates_directories(self, temp_dir):
        """Test that write_dataset creates parent directories if they don't exist."""
        data = [{"id": 1}]
        output_path = os.path.join(temp_dir, "subdir", "nested", "data.json")
        
        write_dataset(data, output_path)
        
        assert os.path.exists(output_path)

    def test_register_checksum_updates_file(self, temp_dir):
        """Test that register_checksum updates the checksums.json file."""
        data = [{"id": 1}]
        data_path = os.path.join(temp_dir, "data.json")
        checksums_path = os.path.join(temp_dir, "checksums.json")
        
        write_dataset(data, data_path)
        register_checksum(data_path, checksums_path)
        
        assert os.path.exists(checksums_path)
        checksums = load_checksums(checksums_path)
        
        # Verify the file is in the checksums
        assert data_path in checksums
        assert "sha256" in checksums[data_path]

    def test_generate_and_save_training_data(self, temp_dir):
        """Test the full pipeline of saving proofs and grids."""
        proofs = [{"id": "p1", "domain": "logic", "rule_set": "A"}]
        grids = [{"id": "g1", "domain": "grid", "rule_set": "B"}]
        
        generate_and_save_training_data(proofs, grids, data_dir=temp_dir)
        
        proofs_path = os.path.join(temp_dir, "generated_proofs.json")
        grids_path = os.path.join(temp_dir, "generated_grids.json")
        checksums_path = os.path.join(temp_dir, "checksums.json")
        
        assert os.path.exists(proofs_path)
        assert os.path.exists(grids_path)
        assert os.path.exists(checksums_path)

        with open(proofs_path, 'r') as f:
            loaded_proofs = json.load(f)
        assert loaded_proofs == proofs

        with open(grids_path, 'r') as f:
            loaded_grids = json.load(f)
        assert loaded_grids == grids
