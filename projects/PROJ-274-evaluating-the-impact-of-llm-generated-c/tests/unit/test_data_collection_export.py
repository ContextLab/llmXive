import os
import json
import tempfile
import shutil
import pytest
from unittest.mock import patch, MagicMock

# Add parent to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from data_collection import (
    ensure_data_directory,
    load_existing_logs,
    save_logs,
    calculate_checksum,
    update_checksums,
    log_session_start,
    log_help_request,
    log_session_end,
    calculate_cognitive_load_proxy,
    export_raw_data,
    PARTICIPANT_LOGS_FILE,
    CHECKSUM_FILE
)

class TestDataCollectionExport:
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.original_data_dir = os.getcwd()
        
        # Mock the global paths to point to temp dir
        self.temp_raw_dir = os.path.join(self.temp_dir, "data", "raw")
        os.makedirs(self.temp_raw_dir, exist_ok=True)
        
        # Patch the module constants
        import data_collection
        self.original_logs_path = data_collection.PARTICIPANT_LOGS_FILE
        self.original_checksum_path = data_collection.CHECKSUM_FILE
        self.original_raw_dir = data_collection.RAW_DIR
        
        data_collection.PARTICIPANT_LOGS_FILE = os.path.join(self.temp_raw_dir, "participant_logs.json")
        data_collection.CHECKSUM_FILE = os.path.join(self.temp_dir, "checksums.txt")
        data_collection.RAW_DIR = self.temp_raw_dir
        
        yield
        
        # Restore and cleanup
        data_collection.PARTICIPANT_LOGS_FILE = self.original_logs_path
        data_collection.CHECKSUM_FILE = self.original_checksum_path
        data_collection.RAW_DIR = self.original_raw_dir
        shutil.rmtree(self.temp_dir)

    def test_export_raw_data_creates_file(self):
        """Test that export_raw_data creates the participant_logs.json file."""
        logs = [
            log_session_start("P001", "LLM"),
            log_session_end(logs[0], 100.0)
        ]
        
        export_raw_data(logs)
        
        assert os.path.exists(data_collection.PARTICIPANT_LOGS_FILE)
        assert os.path.getsize(data_collection.PARTICIPANT_LOGS_FILE) > 0

    def test_export_raw_data_generates_checksum(self):
        """Test that export_raw_data updates the checksums.txt file."""
        logs = [log_session_start("P001", "LLM")]
        
        export_raw_data(logs)
        
        assert os.path.exists(data_collection.CHECKSUM_FILE)
        with open(data_collection.CHECKSUM_FILE, 'r') as f:
            content = f.read()
            assert "participant_logs.json" in content or "checksum" in content.lower()

    def test_export_raw_data_includes_cognitive_load_proxy(self):
        """Test that the exported JSON includes the cognitive_load_proxy_score."""
        logs = [log_session_start("P001", "LLM")]
        logs[0] = log_help_request(logs[0], "How do I do this?")
        logs[0] = log_session_end(logs[0], 100.0)
        
        export_raw_data(logs)
        
        with open(data_collection.PARTICIPANT_LOGS_FILE, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert "cognitive_load_proxy_score" in data[0]
        # Score should be 0 if no time delta can be calculated
        assert isinstance(data[0]["cognitive_load_proxy_score"], (int, float))

    def test_export_raw_data_preserves_all_fields(self):
        """Test that all session fields are preserved in export."""
        logs = [log_session_start("P001", "LLM")]
        logs[0] = log_help_request(logs[0], "Help me")
        logs[0] = log_session_end(logs[0], 120.5)
        logs[0]["subjective_helpfulness"] = 4.5
        
        export_raw_data(logs)
        
        with open(data_collection.PARTICIPANT_LOGS_FILE, 'r') as f:
            data = json.load(f)
        
        assert data[0]["participant_id"] == "P001"
        assert data[0]["condition"] == "LLM"
        assert data[0]["final_time"] == 120.5
        assert data[0]["subjective_helpfulness"] == 4.5
        assert len(data[0]["help_requests"]) == 1

    def test_export_raw_data_handles_empty_logs(self):
        """Test that export_raw_data handles an empty list of logs."""
        export_raw_data([])
        
        assert os.path.exists(data_collection.PARTICIPANT_LOGS_FILE)
        with open(data_collection.PARTICIPANT_LOGS_FILE, 'r') as f:
            data = json.load(f)
        assert data == []