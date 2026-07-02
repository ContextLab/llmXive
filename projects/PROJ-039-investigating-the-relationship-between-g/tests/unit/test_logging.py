import pytest
import os
import json
import yaml
from pathlib import Path
import shutil

# Import the logging module
from logging_config import (
    initialize_logging,
    get_preprocess_logger,
    get_analysis_logger,
    log_structured_event,
    flush_yaml_logs,
    save_analysis_results,
    _preprocess_logs,
    _analysis_results
)

class TestLoggingInfrastructure:
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        # Setup: Initialize logging before each test
        initialize_logging()
        yield
        # Teardown: Clean up artifact files if created during test
        if Path("artifacts/preprocess.yaml").exists():
            os.remove("artifacts/preprocess.yaml")
        if Path("artifacts/analysis_results.json").exists():
            os.remove("artifacts/analysis_results.json")
        if Path("artifacts").exists() and not any(Path("artifacts").iterdir()):
            os.rmdir("artifacts")

    def test_preprocess_logger_creates_yaml(self):
        """Test that the preprocess logger writes to preprocess.yaml"""
        logger = get_preprocess_logger()
        log_structured_event(logger, "test_event", {"key": "value"})
        flush_yaml_logs()

        assert Path("artifacts/preprocess.yaml").exists(), "preprocess.yaml was not created"
        
        with open("artifacts/preprocess.yaml", 'r') as f:
            data = yaml.safe_load(f)
        
        assert isinstance(data, list), "preprocess.yaml should contain a list of events"
        assert len(data) > 0, "preprocess.yaml should contain at least one event"
        assert data[0]["event"] == "test_event", "Event name mismatch"
        assert data[0]["key"] == "value", "Event details mismatch"

    def test_analysis_logger_saves_json(self):
        """Test that the analysis logger writes to analysis_results.json"""
        logger = get_analysis_logger()
        log_structured_event(logger, "analysis_start", {"type": "correlation"})
        save_analysis_results({"result": 42, "status": "ok"})

        assert Path("artifacts/analysis_results.json").exists(), "analysis_results.json was not created"
        
        with open("artifacts/analysis_results.json", 'r') as f:
            data = json.load(f)
        
        assert "result" in data, "Result key missing"
        assert data["result"] == 42, "Result value mismatch"
        assert data["status"] == "ok", "Status value mismatch"

    def test_structured_event_format(self):
        """Test that structured events contain required fields"""
        logger = get_preprocess_logger()
        log_structured_event(logger, "my_event", {"data": 123})
        flush_yaml_logs()

        with open("artifacts/preprocess.yaml", 'r') as f:
            data = yaml.safe_load(f)
        
        event = data[0]
        assert "event" in event, "Missing 'event' field"
        assert "timestamp" in event, "Missing 'timestamp' field"
        assert "level" in event, "Missing 'level' field"
        assert event["event"] == "my_event"

    def test_multiple_logs_accumulate(self):
        """Test that multiple log calls accumulate in the list"""
        logger = get_preprocess_logger()
        log_structured_event(logger, "event1", {})
        log_structured_event(logger, "event2", {})
        log_structured_event(logger, "event3", {})
        flush_yaml_logs()

        with open("artifacts/preprocess.yaml", 'r') as f:
            data = yaml.safe_load(f)
        
        assert len(data) == 3, f"Expected 3 events, got {len(data)}"
        assert data[0]["event"] == "event1"
        assert data[1]["event"] == "event2"
        assert data[2]["event"] == "event3"

    def test_analysis_results_update(self):
        """Test that save_analysis_results updates existing results"""
        save_analysis_results({"a": 1})
        save_analysis_results({"b": 2})
        
        # Accessing the internal state directly for this test
        # In a real scenario, we might use get_analysis_results()
        # But here we check the file content
        save_analysis_results({"a": 1}) # Reset for file check
        save_analysis_results({"b": 2})
        
        with open("artifacts/analysis_results.json", 'r') as f:
            data = json.load(f)
        
        assert "a" in data
        assert "b" in data
        assert data["b"] == 2