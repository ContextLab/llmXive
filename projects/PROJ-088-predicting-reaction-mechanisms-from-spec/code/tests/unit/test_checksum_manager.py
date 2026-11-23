import json
import os
import tempfile
from pathlib import Path
import pytest
import yaml

from src.utils.checksum_manager import update_artifact_checksum, calculate_batch_checksums, _update_state_file
from src.utils.io import write_json_file

class TestChecksumManager:
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def test_file(self, temp_dir):
        file_path = temp_dir / "test_data.json"
        data = {"key": "value", "number": 123}
        with open(file_path, 'w') as f:
            json.dump(data, f)
        return str(file_path)

    @pytest.fixture
    def checksums_file(self, temp_dir):
        return str(temp_dir / "checksums.json")

    @pytest.fixture
    def state_file(self, temp_dir):
        return str(temp_dir / "state.yaml")

    def test_update_artifact_checksum_creates_file(self, test_file, checksums_file, state_file):
        result = update_artifact_checksum(test_file, checksums_file, state_file)
        
        assert "path" in result
        assert "checksum" in result
        assert result["path"] == test_file
        assert len(result["checksum"]) == 64  # SHA-256 hex length

        # Verify checksums file was created and contains data
        assert os.path.exists(checksums_file)
        with open(checksums_file, 'r') as f:
            stored = json.load(f)
        assert test_file in stored

        # Verify state file was updated
        assert os.path.exists(state_file)
        with open(state_file, 'r') as f:
            state = yaml.safe_load(f)
        assert "artifact_hashes" in state
        assert test_file in state["artifact_hashes"]
        assert state["artifact_hashes"][test_file] == result["checksum"]

    def test_update_artifact_checksum_updates_existing(self, test_file, checksums_file, state_file):
        # Initial call
        update_artifact_checksum(test_file, checksums_file, state_file)
        
        # Modify file
        with open(test_file, 'w') as f:
            json.dump({"new": "data"}, f)
        
        # Second call
        result = update_artifact_checksum(test_file, checksums_file, state_file)
        
        # Verify checksum changed
        with open(checksums_file, 'r') as f:
            stored = json.load(f)
        assert stored[test_file] == result["checksum"]

    def test_batch_checksums(self, temp_dir, checksums_file, state_file):
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file1.write_text("content 1")
        file2.write_text("content 2")
        
        files = [str(file1), str(file2)]
        results = calculate_batch_checksums(files, checksums_file, state_file)
        
        assert len(results) == 2
        paths = [r["path"] for r in results]
        assert str(file1) in paths
        assert str(file2) in paths

    def test_file_not_found(self, checksums_file, state_file):
        with pytest.raises(FileNotFoundError):
            update_artifact_checksum("nonexistent_file.txt", checksums_file, state_file)
