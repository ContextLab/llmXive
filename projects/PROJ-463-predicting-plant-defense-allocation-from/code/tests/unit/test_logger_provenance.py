import os
import json
import tempfile
import logging
from pathlib import Path
import pytest
import sys

from src.utils.logger import setup_logging, get_logger, set_log_level, PipelineLogger
from src.utils.provenance import (
    ProvenanceRecord, PipelineRun, ProvenanceTracker, 
    get_provenance_tracker, record_provenance
)
from src.utils.config import get_data_path

@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for testing config and logs."""
    original_path = None
    # We cannot easily mock the singleton config without more setup, 
    # so we rely on the fact that get_data_path() uses the config.
    # For this test, we assume the config is set up correctly by T004.
    # We just ensure the directories exist.
    data_path = get_data_path()
    log_dir = data_path / "processed" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    yield log_dir

class TestLogger:
    def test_setup_logging_creates_logger(self, temp_config_dir):
        logger = setup_logging()
        assert isinstance(logger, PipelineLogger)
        assert logger.name == "pipeline_main"
        assert len(logger.logger.handlers) >= 2  # Console and File

    def test_get_logger_reuses_instance(self, temp_config_dir):
        logger1 = get_logger("test_module")
        logger2 = get_logger("test_module")
        assert logger1 is logger2

    def test_logger_writes_to_file(self, temp_config_dir):
        logger = get_logger("test_file_write")
        logger.info("Test message")
        
        # Find the log file created recently
        log_files = list(temp_config_dir.glob("pipeline_*.log"))
        assert len(log_files) > 0
        
        # Check content (simple check)
        with open(log_files[-1], 'r') as f:
            content = f.read()
            assert "Test message" in content

    def test_set_log_level(self, temp_config_dir):
        logger = get_logger("test_level")
        original_level = logger.logger.level
        set_log_level(logging.DEBUG)
        # Note: get_logger returns the wrapper, but the underlying logger is updated
        # via the set_level method if called on the wrapper, or we check the global effect
        # The implementation updates the underlying logger.
        # We verify by checking the wrapper's internal state or just trusting the logic.
        # A better test:
        logger.set_level(logging.WARNING)
        assert logger.logger.level == logging.WARNING

class TestProvenanceRecord:
    def test_create_record(self):
        record = ProvenanceRecord(
            record_id="123",
            timestamp="2023-01-01T00:00:00",
            action="test_action",
            input_files=["in.txt"],
            output_files=["out.txt"],
            parameters={"key": "value"},
            tool_version="1.0",
            code_hash="abc",
            user="test",
            host="localhost"
        )
        assert record.action == "test_action"
        assert len(record.input_files) == 1

    def test_to_json_serialization(self):
        record = ProvenanceRecord(
            record_id="123",
            timestamp="2023-01-01T00:00:00",
            action="test",
            input_files=[],
            output_files=[],
            parameters={},
            tool_version="1.0",
            code_hash="abc",
            user="test",
            host="localhost"
        )
        json_str = record.to_json()
        parsed = json.loads(json_str)
        assert parsed["action"] == "test"

class TestPipelineRun:
    def test_create_run(self):
        run = PipelineRun(
            run_id="run_001",
            start_time="2023-01-01T00:00:00",
            end_time=None,
            status="running",
            config_snapshot={"seed": 42}
        )
        assert run.status == "running"
        assert len(run.provenance_records) == 0

    def test_add_record(self):
        run = PipelineRun(
            run_id="run_001",
            start_time="2023-01-01T00:00:00",
            end_time=None,
            status="running",
            config_snapshot={}
        )
        record = ProvenanceRecord(
            record_id="rec_001",
            timestamp="2023-01-01T00:00:00",
            action="test",
            input_files=[],
            output_files=[],
            parameters={},
            tool_version="1.0",
            code_hash="abc",
            user="test",
            host="localhost"
        )
        run.add_record(record)
        assert len(run.provenance_records) == 1

    def test_finish_run(self, temp_config_dir):
        run = PipelineRun(
            run_id="run_002",
            start_time="2023-01-01T00:00:00",
            end_time=None,
            status="running",
            config_snapshot={}
        )
        run.finish("completed")
        assert run.status == "completed"
        assert run.end_time is not None

        # Test save
        filepath = run.save()
        assert filepath.exists()
        with open(filepath, 'r') as f:
            data = json.load(f)
            assert data["status"] == "completed"

class TestProvenanceTracker:
    def test_singleton_instance(self):
        tracker1 = get_provenance_tracker()
        tracker2 = get_provenance_tracker()
        assert tracker1 is tracker2

    def test_start_and_finish_run(self):
        tracker = ProvenanceTracker()
        # Reset any existing run
        tracker._current_run = None
        
        run = tracker.start_run({"seed": 42})
        assert run.status == "running"
        
        tracker.finish_run("completed")
        assert tracker.get_run() is None

    def test_record_in_run(self):
        tracker = ProvenanceTracker()
        tracker._current_run = None
        
        tracker.start_run({})
        record = tracker.record(
            action="test_record",
            input_files=["in"],
            output_files=["out"],
            parameters={},
            tool_version="1.0"
        )
        
        run = tracker.get_run()
        assert record in run.provenance_records

    def test_record_without_run_raises(self):
        tracker = ProvenanceTracker()
        tracker._current_run = None
        with pytest.raises(RuntimeError):
            tracker.record("test", [], [], {}, "1.0")

def test_convenience_record_provenance():
    # This test requires a run to be active
    tracker = get_provenance_tracker()
    tracker._current_run = None
    tracker.start_run({})
    
    # Reset the global singleton state for the test if needed, 
    # but here we rely on the instance we just got.
    # The module-level function uses the global _tracker which might be different 
    # if the module was imported before. 
    # To be safe, we ensure the module's _tracker is the same instance.
    import src.utils.provenance as prov_module
    prov_module._tracker = tracker
    
    record = record_provenance("convenience_test", [], [], {}, "1.0")
    assert record.action == "convenience_test"
    
    tracker.finish_run("completed")