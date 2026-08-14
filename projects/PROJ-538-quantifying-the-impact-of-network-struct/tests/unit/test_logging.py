import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# We need to test the logger initialization and audit file writing
# Since the logger is a singleton, we need to mock the config path to avoid polluting the real project data
# during tests, or ensure we clean up. For this test, we will patch the config.

def test_audit_log_creation():
    """Test that the audit log file is created and entries are written correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mock_config = MagicMock()
        mock_config.data_dir = tmpdir
        
        with patch("code.utils.config", mock_config):
            # Force re-initialization by deleting the module cache if needed, 
            # but simpler to just import fresh in a subprocess or rely on the lock logic.
            # Here we assume the test runner handles module reloads or we test the handler logic directly.
            
            # Re-import to pick up the mocked config if possible, 
            # but since utils is imported by main.py etc., we test the handler class directly.
            from code.utils import _ensure_audit_handler
            
            # Clear the global handler to force recreation with new path
            import code.utils
            code.utils._audit_handler = None
            
            handler = _ensure_audit_handler()
            
            # Verify file exists
            audit_path = Path(tmpdir) / "audit_log.json"
            assert audit_path.exists()
            
            # Log a test message
            record = handler.makeRecord(
                name="test_logger",
                level=20, # INFO
                fn="test.py",
                lno=1,
                msg="Test audit message",
                args=(),
                exc_info=None
            )
            handler.emit(record)
            
            # Verify content
            with open(audit_path, "r") as f:
                lines = f.readlines()
            
            assert len(lines) == 1
            entry = json.loads(lines[0])
            
            assert entry["message"] == "Test audit message"
            assert entry["level"] == "INFO"
            assert "timestamp" in entry

def test_logger_singleton():
    """Test that get_logger returns the same instance."""
    from code.utils import get_logger
    
    logger1 = get_logger("test_singleton")
    logger2 = get_logger("test_singleton")
    
    assert logger1 is logger2