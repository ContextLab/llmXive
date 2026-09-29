import os
import sys
import pytest
from pathlib import Path
import hashlib

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from code.data.ingest_netflow import (
    calculate_md5,
    calculate_sha256,
    download_file,
    load_state,
    update_state,
    ensure_data_dirs,
    DATASETS
)

class TestDataIngestion:
    def test_ensure_data_dirs(self, tmp_path):
        """Test that data directories are created."""
        # Temporarily override DATA_RAW_DIR for testing
        import code.data.ingest_netflow as ingest_module
        original_dir = ingest_module.DATA_RAW_DIR
        ingest_module.DATA_RAW_DIR = tmp_path / "data" / "raw"

        try:
            ensure_data_dirs()
            assert ingest_module.DATA_RAW_DIR.exists()
        finally:
            ingest_module.DATA_RAW_DIR = original_dir

    def test_calculate_md5(self, tmp_path):
        """Test MD5 checksum calculation."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)

        calculated_md5 = calculate_md5(test_file)
        expected_md5 = hashlib.md5(test_content).hexdigest()

        assert calculated_md5 == expected_md5

    def test_calculate_sha256(self, tmp_path):
        """Test SHA256 checksum calculation."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)

        calculated_sha256 = calculate_sha256(test_file)
        expected_sha256 = hashlib.sha256(test_content).hexdigest()

        assert calculated_sha256 == expected_sha256

    def test_load_state_empty(self, tmp_path):
        """Test loading state when file doesn't exist."""
        import code.data.ingest_netflow as ingest_module
        original_state_file = ingest_module.STATE_FILE
        ingest_module.STATE_FILE = tmp_path / "state.yaml"

        try:
            state = load_state()
            assert state["project_id"] == "PROJ-041-evaluating-the-use-of-graph-neural-netwo"
            assert "artifact_hashes" in state
            assert "dataset_info" in state
        finally:
            ingest_module.STATE_FILE = original_state_file

    def test_update_state(self, tmp_path):
        """Test updating state file."""
        import code.data.ingest_netflow as ingest_module
        original_state_file = ingest_module.STATE_FILE
        ingest_module.STATE_FILE = tmp_path / "state.yaml"

        try:
            state = {
                "project_id": "PROJ-041-evaluating-the-use-of-graph-neural-netwo",
                "artifact_hashes": {},
                "dataset_info": {"test": "data"},
                "updated_at": None
            }
            update_state(state)

            assert ingest_module.STATE_FILE.exists()
            loaded_state = load_state()
            assert loaded_state["dataset_info"]["test"] == "data"
            assert loaded_state["updated_at"] is not None
        finally:
            ingest_module.STATE_FILE = original_state_file

    def test_download_file_invalid_url(self, tmp_path):
        """Test download with invalid URL."""
        dest_path = tmp_path / "invalid.txt"
        success = download_file("https://invalid.url/that/does/not/exist", dest_path)
        assert success is False
        assert not dest_path.exists()

    def test_dataset_config_exists(self):
        """Test that dataset configurations exist."""
        assert "ctu" in DATASETS
        assert "bot_iot" in DATASETS
        assert DATASETS["bot_iot"]["name"] == "NF-BoT-IoT Dataset"
        assert "url" in DATASETS["bot_iot"]
        assert "checksum" in DATASETS["bot_iot"]
