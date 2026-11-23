import pytest
import json
import os
from pathlib import Path
from code.logging import setup_logging, log_pipeline_start, log_pipeline_end, log_data_event
from code.utils import log_audit_event

class TestLoggingInfrastructure:
    
    def test_audit_log_file_creation(self):
        """Test that audit_log.json is created if it doesn't exist."""
        audit_path = Path("data/audit_log.json")
        # Remove if exists for clean test
        if audit_path.exists():
            audit_path.unlink()
        
        # Trigger creation via setup_logging or direct call
        setup_logging("test_logger")
        
        assert audit_path.exists(), "data/audit_log.json was not created"
        
        with open(audit_path, 'r') as f:
            content = f.read().strip()
            assert content == "[]", "New audit log should be an empty JSON array"

    def test_log_audit_event_appends(self):
        """Test that log_audit_event appends to the existing log."""
        audit_path = Path("data/audit_log.json")
        
        # Ensure file exists with some data
        initial_data = [{"timestamp": "2023-01-01", "type": "INIT", "name": "test", "details": {}}]
        with open(audit_path, 'w') as f:
            json.dump(initial_data, f)
        
        log_audit_event("TEST", "TestEvent", {"key": "value"})
        
        with open(audit_path, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 2, f"Expected 2 entries, got {len(data)}"
        assert data[1]["type"] == "TEST"
        assert data[1]["name"] == "TestEvent"
        assert data[1]["details"]["key"] == "value"

    def test_log_pipeline_start(self):
        """Test logging pipeline start."""
        log_pipeline_start("synthetic", {"seed": 42})
        
        audit_path = Path("data/audit_log.json")
        with open(audit_path, 'r') as f:
            data = json.load(f)
        
        # Find the last entry
        last_entry = data[-1]
        assert last_entry["type"] == "PIPELINE_START"
        assert last_entry["name"] == "Pipeline Execution"
        assert last_entry["details"]["mode"] == "synthetic"
        assert last_entry["details"]["config"]["seed"] == 42

    def test_log_pipeline_end(self):
        """Test logging pipeline end."""
        log_pipeline_end("SUCCESS", 120.5)
        
        audit_path = Path("data/audit_log.json")
        with open(audit_path, 'r') as f:
            data = json.load(f)
        
        last_entry = data[-1]
        assert last_entry["type"] == "PIPELINE_END"
        assert last_entry["details"]["status"] == "SUCCESS"
        assert last_entry["details"]["duration_seconds"] == 120.5

    def test_logger_returns_instance(self):
        """Test that setup_logging returns a valid logger."""
        logger = setup_logging("test_unit")
        assert logger is not None
        assert logger.name == "test_unit"
        assert len(logger.handlers) > 0
        
        # Verify handlers include StreamHandler
        handler_types = [type(h).__name__ for h in logger.handlers]
        assert "StreamHandler" in handler_types