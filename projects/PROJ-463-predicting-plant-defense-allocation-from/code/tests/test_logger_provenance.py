import os
import json
import tempfile
import logging
from pathlib import Path
import pytest
import sys

# Add the code directory to the path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from src.utils.logger import get_logger, setup_logging, set_log_level, PipelineLogger
from src.utils.provenance import (
    ProvenanceRecord, PipelineRun, ProvenanceTracker, 
    get_provenance_tracker, record_provenance
)
from src.utils.config import Config, reset_config

@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary config and data directory structure."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Create a minimal config file
    config_data = {
        "data_path": str(data_dir),
        "seed": 42,
        "log_level": "INFO"
    }
    config_file = tmp_path / "config.json"
    with open(config_file, 'w') as f:
        json.dump(config_data, f)
    
    # Set environment variable for config path
    os.environ["LLMXIVE_CONFIG_PATH"] = str(config_file)
    
    # Reset config to pick up new env var
    reset_config()
    
    return tmp_path

class TestLogger:
    def test_logger_creation(self, temp_config_dir):
        """Test that a logger can be created."""
        logger = get_logger("test_logger")
        assert isinstance(logger, PipelineLogger)
        assert logger.name == "test_logger"

    def test_logger_levels(self, temp_config_dir):
        """Test that logger levels work correctly."""
        logger = get_logger("test_levels")
        
        # Test that we can call logging methods without error
        logger.info("Info message")
        logger.debug("Debug message")
        logger.warning("Warning message")
        logger.error("Error message")
        
        # Verify the underlying logger level
        assert logger.logger.level == logging.INFO

    def test_log_file_creation(self, temp_config_dir):
        """Test that log files are created."""
        # Force setup
        setup_logging()
        logger = get_logger("test_file")
        
        # The logger should have created a log file in the data/logs directory
        log_dir = Path(temp_config_dir) / "data" / "logs"
        assert log_dir.exists()
        
        # Check that at least one log file exists
        log_files = list(log_dir.glob("*.log"))
        assert len(log_files) > 0

    def test_set_log_level(self, temp_config_dir):
        """Test dynamic log level setting."""
        setup_logging()
        set_log_level(logging.DEBUG)
        
        logger = get_logger("test_level_change")
        assert logger.logger.level == logging.DEBUG

class TestProvenanceRecord:
    def test_record_creation(self):
        """Test creation of a ProvenanceRecord."""
        record = ProvenanceRecord(
            record_id="test-123",
            timestamp="2023-01-01T00:00:00",
            step_name="test_step",
            input_files=["input1.txt"],
            output_files=["output1.txt"],
            parameters={"key": "value"}
        )
        
        assert record.step_name == "test_step"
        assert len(record.input_files) == 1
        assert record.parameters["key"] == "value"

    def test_record_checksum(self):
        """Test that checksums are computed correctly."""
        record1 = ProvenanceRecord(
            record_id="test-123",
            timestamp="2023-01-01T00:00:00",
            step_name="test_step",
            input_files=["input1.txt"],
            output_files=["output1.txt"],
            parameters={"key": "value"}
        )
        
        record2 = ProvenanceRecord(
            record_id="test-123",
            timestamp="2023-01-01T00:00:00",
            step_name="test_step",
            input_files=["input1.txt"],
            output_files=["output1.txt"],
            parameters={"key": "value"}
        )
        
        # Same content should produce same checksum
        assert record1.compute_checksum() == record2.compute_checksum()
        
        # Different content should produce different checksum
        record3 = ProvenanceRecord(
            record_id="test-123",
            timestamp="2023-01-01T00:00:00",
            step_name="test_step",
            input_files=["input2.txt"], # Different input
            output_files=["output1.txt"],
            parameters={"key": "value"}
        )
        assert record1.compute_checksum() != record3.compute_checksum()

class TestPipelineRun:
    def test_run_creation(self):
        """Test creation of a PipelineRun."""
        run = PipelineRun(run_id="run-123", start_time="2023-01-01T00:00:00")
        
        assert run.run_id == "run-123"
        assert run.status == "running"
        assert len(run.records) == 0

    def test_add_record(self):
        """Test adding records to a run."""
        run = PipelineRun(run_id="run-123", start_time="2023-01-01T00:00:00")
        
        record = ProvenanceRecord(
            record_id="rec-1",
            timestamp="2023-01-01T00:00:00",
            step_name="step1",
            input_files=[],
            output_files=["out1.txt"],
            parameters={}
        )
        
        run.add_record(record)
        assert len(run.records) == 1
        assert run.records[0].record_id == "rec-1"

    def test_finish_run(self):
        """Test finishing a run."""
        run = PipelineRun(run_id="run-123", start_time="2023-01-01T00:00:00")
        run.finish(status="completed")
        
        assert run.status == "completed"
        assert run.end_time is not None

class TestProvenanceTracker:
    def test_tracker_singleton(self, temp_config_dir):
        """Test that the tracker acts as a singleton."""
        tracker1 = get_provenance_tracker()
        tracker2 = get_provenance_tracker()
        
        assert tracker1 is tracker2

    def test_record_step(self, temp_config_dir):
        """Test recording a step."""
        tracker = get_provenance_tracker()
        
        # Reset for clean test
        tracker.run.records = []
        
        record = tracker.record_step(
            step_name="test_step",
            input_files=["in1.txt"],
            output_files=["out1.txt"],
            parameters={"param": "val"}
        )
        
        assert len(tracker.run.records) == 1
        assert record.step_name == "test_step"

    def test_finish_run_saves_manifest(self, temp_config_dir):
        """Test that finishing a run saves the manifest."""
        tracker = ProvenanceTracker()
        
        tracker.record_step(
            step_name="test_step",
            input_files=[],
            output_files=[],
            parameters={}
        )
        
        tracker.finish_run(status="completed")
        
        # Check that manifest files exist
        manifest_path = tracker._save_dir / f"{tracker.run.run_id}_manifest.json"
        latest_path = tracker._save_dir / "latest_run_manifest.json"
        
        assert manifest_path.exists()
        assert latest_path.exists()
        
        # Verify content
        with open(manifest_path) as f:
            data = json.load(f)
            assert data["status"] == "completed"
            assert len(data["records"]) == 1

    def test_convenience_function(self, temp_config_dir):
        """Test the record_provenance convenience function."""
        # Reset global tracker
        import src.utils.provenance as prov_mod
        prov_mod._tracker = None
        
        record = record_provenance(
            step_name="convenience_test",
            input_files=[],
            output_files=[],
            parameters={}
        )
        
        assert record is not None
        assert record.step_name == "convenience_test"