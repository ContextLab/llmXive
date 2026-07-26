"""
Unit tests for logging and provenance tracking functionality.
"""

import os
import json
import tempfile
import logging
from pathlib import Path
import pytest
import sys
from datetime import datetime
import time

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.utils.logger import setup_logging, set_log_level, get_logger, PipelineLogger
from src.utils.provenance import (
    ProvenanceTracker,
    ProvenanceRecord,
    PipelineRun,
    ArtifactType,
    get_provenance_tracker,
    record_provenance,
    start_pipeline_run,
    complete_pipeline_run
)


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for test configuration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestLogger:
    """Tests for the logging functionality."""

    def test_setup_logging_creates_logger(self, temp_config_dir):
        """Test that setup_logging creates a valid logger instance."""
        logger = setup_logging(log_dir=str(temp_config_dir / "logs"))
        assert isinstance(logger, PipelineLogger)
        assert logger.get_logger() is not None
        assert logger.get_logger().name == "plant_defense_pipeline"

    def test_log_messages(self, temp_config_dir):
        """Test that log messages are written correctly."""
        logger = setup_logging(log_dir=str(temp_config_dir / "logs"))
        test_message = "Test log message"
        logger.info(test_message)
        
        # Check that the log file exists
        log_files = list(temp_config_dir.glob("logs/*.log"))
        assert len(log_files) > 0
        
        # Verify the message is in the log
        log_content = log_files[0].read_text()
        assert test_message in log_content

    def test_different_log_levels(self, temp_config_dir):
        """Test setting different log levels."""
        logger = setup_logging(log_dir=str(temp_config_dir / "logs"), log_level=logging.DEBUG)
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        
        log_files = list(temp_config_dir.glob("logs/*.log"))
        log_content = log_files[0].read_text()
        
        assert "Debug message" in log_content
        assert "Info message" in log_content
        assert "Warning message" in log_content

    def test_get_logger_by_name(self, temp_config_dir):
        """Test getting a logger with a specific name."""
        setup_logging(log_dir=str(temp_config_dir / "logs"))
        child_logger = get_logger("child_module")
        assert child_logger.name == "plant_defense_pipeline.child_module"

    def test_set_log_level(self, temp_config_dir):
        """Test changing log level dynamically."""
        logger = setup_logging(log_dir=str(temp_config_dir / "logs"), log_level=logging.WARNING)
        set_log_level(logging.DEBUG)
        
        # The level should have changed
        assert logger.get_logger().level == logging.DEBUG

    def test_log_exception(self, temp_config_dir):
        """Test logging an exception."""
        logger = setup_logging(log_dir=str(temp_config_dir / "logs"))
        try:
            raise ValueError("Test exception")
        except ValueError:
            logger.exception("An error occurred")
        
        log_files = list(temp_config_dir.glob("logs/*.log"))
        log_content = log_files[0].read_text()
        
        assert "An error occurred" in log_content
        assert "ValueError" in log_content


class TestProvenanceRecord:
    """Tests for the ProvenanceRecord dataclass."""

    def test_create_record(self):
        """Test creating a ProvenanceRecord."""
        record = ProvenanceRecord(
            artifact_id="test_001",
            artifact_type=ArtifactType.RAW_DATA,
            file_path="/path/to/file.txt",
            checksum="abc123",
            created_at=datetime.now().isoformat(),
            created_by="test_module"
        )
        
        assert record.artifact_id == "test_001"
        assert record.artifact_type == ArtifactType.RAW_DATA
        assert record.checksum == "abc123"

    def test_record_to_dict(self):
        """Test converting a record to dictionary."""
        record = ProvenanceRecord(
            artifact_id="test_001",
            artifact_type=ArtifactType.PROCESSED_DATA,
            file_path="/path/to/file.csv",
            checksum="def456",
            created_at=datetime.now().isoformat(),
            created_by="test_module",
            parameters={"param1": "value1"},
            input_artifacts=["input_001"],
            metadata={"key": "value"}
        )
        
        record_dict = record.to_dict()
        assert record_dict["artifact_id"] == "test_001"
        assert record_dict["artifact_type"] == "processed_data"
        assert record_dict["parameters"]["param1"] == "value1"
        assert record_dict["input_artifacts"] == ["input_001"]

    def test_record_from_dict(self):
        """Test creating a record from dictionary."""
        data = {
            "artifact_id": "test_002",
            "artifact_type": "model",
            "file_path": "/path/to/model.pkl",
            "checksum": "ghi789",
            "created_at": datetime.now().isoformat(),
            "created_by": "model_module",
            "parameters": {},
            "input_artifacts": [],
            "metadata": {}
        }
        
        record = ProvenanceRecord.from_dict(data)
        assert record.artifact_id == "test_002"
        assert record.artifact_type == ArtifactType.MODEL

    def test_compute_checksum(self, temp_config_dir):
        """Test computing file checksum."""
        test_file = temp_config_dir / "test_file.txt"
        test_file.write_text("Test content for checksum")
        
        record = ProvenanceRecord(
            artifact_id="test_003",
            artifact_type=ArtifactType.OTHER,
            file_path=str(test_file),
            checksum="",
            created_at=datetime.now().isoformat(),
            created_by="test_module"
        )
        
        checksum = record.compute_checksum()
        assert len(checksum) == 64  # SHA256 hex length

    def test_update_checksum(self, temp_config_dir):
        """Test updating the checksum field."""
        test_file = temp_config_dir / "test_file2.txt"
        test_file.write_text("Update checksum test")
        
        record = ProvenanceRecord(
            artifact_id="test_004",
            artifact_type=ArtifactType.MANIFEST,
            file_path=str(test_file),
            checksum="old_checksum",
            created_at=datetime.now().isoformat(),
            created_by="test_module"
        )
        
        record.update_checksum()
        assert record.checksum != "old_checksum"
        assert len(record.checksum) == 64


class TestPipelineRun:
    """Tests for the PipelineRun dataclass."""

    def test_create_run(self):
        """Test creating a PipelineRun."""
        run = PipelineRun(
            run_id="run_001",
            start_time=datetime.now().isoformat()
        )
        
        assert run.run_id == "run_001"
        assert run.status == "running"
        assert run.end_time is None

    def test_complete_run(self):
        """Test completing a pipeline run."""
        run = PipelineRun(
            run_id="run_002",
            start_time=datetime.now().isoformat()
        )
        
        run.complete(status="completed")
        assert run.status == "completed"
        assert run.end_time is not None

    def test_add_artifact(self):
        """Test adding an artifact to a run."""
        run = PipelineRun(
            run_id="run_003",
            start_time=datetime.now().isoformat()
        )
        
        artifact = ProvenanceRecord(
            artifact_id="art_001",
            artifact_type=ArtifactType.RAW_DATA,
            file_path="/path/to/data.csv",
            checksum="abc",
            created_at=datetime.now().isoformat(),
            created_by="test_module"
        )
        
        run.add_artifact(artifact)
        assert len(run.artifacts) == 1
        assert run.artifacts[0].artifact_id == "art_001"

    def test_get_artifact(self):
        """Test retrieving an artifact by ID."""
        run = PipelineRun(
            run_id="run_004",
            start_time=datetime.now().isoformat()
        )
        
        artifact = ProvenanceRecord(
            artifact_id="art_002",
            artifact_type=ArtifactType.MODEL,
            file_path="/path/to/model.pkl",
            checksum="def",
            created_at=datetime.now().isoformat(),
            created_by="test_module"
        )
        run.add_artifact(artifact)
        
        retrieved = run.get_artifact("art_002")
        assert retrieved is not None
        assert retrieved.artifact_id == "art_002"

    def test_run_to_dict(self):
        """Test converting a run to dictionary."""
        run = PipelineRun(
            run_id="run_005",
            start_time=datetime.now().isoformat(),
            parameters={"param": "value"}
        )
        
        run_dict = run.to_dict()
        assert run_dict["run_id"] == "run_005"
        assert run_dict["parameters"]["param"] == "value"

    def test_run_from_dict(self):
        """Test creating a run from dictionary."""
        data = {
            "run_id": "run_006",
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "status": "running",
            "user": "test_user",
            "host": "test_host",
            "python_version": "3.11.0",
            "platform": "Linux",
            "artifacts": [],
            "parameters": {}
        }
        
        run = PipelineRun.from_dict(data)
        assert run.run_id == "run_006"
        assert run.user == "test_user"


class TestProvenanceTracker:
    """Tests for the ProvenanceTracker class."""

    def test_tracker_singleton(self):
        """Test that the tracker is a singleton."""
        tracker1 = get_provenance_tracker()
        tracker2 = get_provenance_tracker()
        assert tracker1 is tracker2

    def test_start_run(self, temp_config_dir):
        """Test starting a new pipeline run."""
        tracker = get_provenance_tracker(provenance_dir=str(temp_config_dir / "provenance"))
        run = tracker.start_run(parameters={"test": "param"})
        
        assert run is not None
        assert run.run_id is not None
        assert run.parameters["test"] == "param"

    def test_record_artifact(self, temp_config_dir):
        """Test recording an artifact."""
        tracker = get_provenance_tracker(provenance_dir=str(temp_config_dir / "provenance"))
        tracker.start_run()
        
        test_file = temp_config_dir / "test_artifact.txt"
        test_file.write_text("Artifact content")
        
        record = tracker.record_artifact(
            artifact_id="art_003",
            artifact_type=ArtifactType.PROCESSED_DATA,
            file_path=str(test_file),
            created_by="test_module"
        )
        
        assert record.artifact_id == "art_003"
        assert len(record.checksum) == 64
        assert len(tracker.get_current_run().artifacts) == 1

    def test_complete_run(self, temp_config_dir):
        """Test completing a pipeline run."""
        tracker = get_provenance_tracker(provenance_dir=str(temp_config_dir / "provenance"))
        tracker.start_run()
        
        run_id = tracker.complete_run(status="completed")
        
        assert run_id is not None
        assert (temp_config_dir / "provenance" / f"run_{run_id}.json").exists()

    def test_get_run(self, temp_config_dir):
        """Test retrieving a saved run."""
        tracker = get_provenance_tracker(provenance_dir=str(temp_config_dir / "provenance"))
        tracker.start_run()
        run_id = tracker.complete_run()
        
        retrieved_run = tracker.get_run(run_id)
        assert retrieved_run is not None
        assert retrieved_run.run_id == run_id

    def test_list_runs(self, temp_config_dir):
        """Test listing all runs."""
        tracker = get_provenance_tracker(provenance_dir=str(temp_config_dir / "provenance"))
        
        tracker.start_run()
        run_id1 = tracker.complete_run()
        
        tracker.start_run()
        run_id2 = tracker.complete_run()
        
        runs = tracker.list_runs()
        assert len(runs) == 2
        assert run_id1 in runs
        assert run_id2 in runs

    def test_export_provenance(self, temp_config_dir):
        """Test exporting all provenance data."""
        tracker = get_provenance_tracker(provenance_dir=str(temp_config_dir / "provenance"))
        
        tracker.start_run()
        tracker.complete_run()
        
        output_file = temp_config_dir / "exported_provenance.json"
        tracker.export_provenance(output_file)
        
        assert output_file.exists()
        with open(output_file) as f:
            data = json.load(f)
        assert "runs" in data
        assert len(data["runs"]) == 1

    def test_record_artifact_without_run(self, temp_config_dir):
        """Test that recording an artifact without a run raises an error."""
        tracker = get_provenance_tracker(provenance_dir=str(temp_config_dir / "provenance"))
        
        with pytest.raises(RuntimeError, match="No active pipeline run"):
            tracker.record_artifact(
                artifact_id="art_004",
                artifact_type=ArtifactType.OTHER,
                file_path="/fake/path",
                created_by="test_module"
            )

    def test_complete_run_without_start(self, temp_config_dir):
        """Test that completing a run without starting raises an error."""
        tracker = get_provenance_tracker(provenance_dir=str(temp_config_dir / "provenance"))
        
        with pytest.raises(RuntimeError, match="No active pipeline run"):
            tracker.complete_run()

def test_convenience_record_provenance(temp_config_dir):
    """Test the convenience function for recording provenance."""
    tracker = get_provenance_tracker(provenance_dir=str(temp_config_dir / "provenance"))
    tracker.start_run()
    
    test_file = temp_config_dir / "convenience_test.txt"
    test_file.write_text("Convenience test")
    
    record = record_provenance(
        artifact_id="art_005",
        artifact_type=ArtifactType.MANIFEST,
        file_path=str(test_file),
        created_by="test_module",
        parameters={"test": "value"}
    )
    
    assert record.artifact_id == "art_005"
    assert record.parameters["test"] == "value"

def test_convenience_start_complete_run(temp_config_dir):
    """Test convenience functions for starting and completing runs."""
    tracker = get_provenance_tracker(provenance_dir=str(temp_config_dir / "provenance"))
    
    run = start_pipeline_run(parameters={"global": "param"})
    assert run is not None
    
    run_id = complete_pipeline_run(status="completed")
    assert run_id is not None
    assert (temp_config_dir / "provenance" / f"run_{run_id}.json").exists()