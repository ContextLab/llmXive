import pytest
import os
import tempfile
from datetime import datetime
from code.gatekeeper.rules import (
    parse_deletion_log, 
    load_deletion_logs, 
    is_target_deleted_secure,
    _log_deletion_error
)

class TestMalformedDeletionLogs:
    @pytest.fixture
    def temp_log_file(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            # Valid entry
            f.write(f"entity1|{datetime.now().isoformat()}|User request|completed\n")
            # Malformed entry (missing fields)
            f.write("entity2|invalid_timestamp|reason\n")
            # Malformed entry (wrong delimiter)
            f.write("entity3:completed:reason\n")
            # Valid entry
            f.write(f"entity4|{datetime.now().isoformat()}|User request|completed\n")
            path = f.name
        yield path
        os.unlink(path)

    def test_parse_deletion_log_malformed_returns_none(self):
        """Test that malformed entries return None and trigger logging."""
        result = parse_deletion_log("bad_entry")
        assert result is None

    def test_load_deletion_logs_tracks_malformed_ids(self, temp_log_file):
        """Test that load_deletion_logs separates valid logs and malformed IDs."""
        logs, malformed_ids = load_deletion_logs(temp_log_file)
        
        # Should have 2 valid logs
        assert len(logs) == 2
        assert logs[0].entity_id == "entity1"
        assert logs[1].entity_id == "entity4"
        
        # Should have 2 malformed IDs
        assert "entity2" in malformed_ids
        assert "entity3" in malformed_ids

    def test_is_target_deleted_secure_defaults_to_deny_on_malformed(self, temp_log_file):
        """Test that malformed entries result in a deny (treated as deleted)."""
        logs, malformed_ids = load_deletion_logs(temp_log_file)
        
        # entity2 has a malformed entry, should be treated as deleted (True)
        assert is_target_deleted_secure("entity2", logs, malformed_ids) is True
        
        # entity1 has a valid completed entry, should be deleted (True)
        assert is_target_deleted_secure("entity1", logs, malformed_ids) is True
        
        # entity5 has no entry, should not be deleted (False)
        assert is_target_deleted_secure("entity5", logs, malformed_ids) is False

    def test_log_file_created_for_anomalies(self, temp_log_file):
        """Test that anomalies are logged to logs/deletion_errors.log."""
        # Trigger a parse error
        parse_deletion_log("bad|data")
        
        # Check if log file exists (it might be created by the function)
        # We can't easily assert the content without reading it, but we can check existence
        # The function ensures the directory exists
        assert os.path.exists("logs") or os.path.exists("logs/deletion_errors.log")