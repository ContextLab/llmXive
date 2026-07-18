"""
Tests for logging and provenance tracking modules.
"""
import os
import json
import tempfile
import logging
from pathlib import Path
import pytest
import sys
import datetime

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import get_logger, setup_logging, PipelineLogger, set_log_level
from src.utils.provenance import (
    ProvenanceRecord,
    PipelineRun,
    ProvenanceTracker,
    get_provenance_tracker,
    record_provenance
)


class TestLogger:
    """Tests for the logging module."""
    
    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logging.Logger instance."""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "plant_defense_pipeline.test_module"
    
    def test_setup_logging_creates_handlers(self):
        """Test that setup_logging creates console and file handlers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            logger = setup_logging(log_dir=log_dir, log_file="test.log")
            
            assert len(logger.handlers) >= 2  # Console + File
            
            # Verify file handler exists
            file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) > 0
    
    def test_pipeline_logger_context_manager(self):
        """Test PipelineLogger context manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            setup_logging(log_dir=log_dir, log_file="test.log")
            
            with PipelineLogger("test_stage") as stage_logger:
                stage_logger.progress("Test message")
            
            # Verify log file was created
            log_file = log_dir / "test.log"
            assert log_file.exists()
            
            # Check log content
            content = log_file.read_text()
            assert "test_stage" in content
            assert "Test message" in content
    
    def test_set_log_level(self):
        """Test that set_log_level updates handler levels."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            logger = setup_logging(level=logging.WARNING, log_dir=log_dir, log_file="test.log")
            
            set_log_level(logging.ERROR)
            
            for handler in logger.handlers:
                assert handler.level == logging.ERROR


class TestProvenanceRecord:
    """Tests for ProvenanceRecord dataclass."""
    
    def test_record_creation(self):
        """Test creating a ProvenanceRecord."""
        record = ProvenanceRecord(
            artifact_id="test_001",
            artifact_type="raw_data",
            source_type="real",
            created_at=datetime.datetime.now().isoformat(),
            created_by="test_user"
        )
        
        assert record.artifact_id == "test_001"
        assert record.artifact_type == "raw_data"
        assert record.source_type == "real"
    
    def test_record_serialization(self):
        """Test ProvenanceRecord to_dict and to_json."""
        record = ProvenanceRecord(
            artifact_id="test_002",
            artifact_type="processed_data",
            source_type="derived",
            created_at=datetime.datetime.now().isoformat(),
            created_by="test_user",
            input_artifacts=["input_001"],
            parameters={"param1": "value1"},
            checksum="abc123"
        )
        
        # Test to_dict
        record_dict = record.to_dict()
        assert record_dict["artifact_id"] == "test_002"
        assert record_dict["input_artifacts"] == ["input_001"]
        
        # Test to_json
        json_str = record.to_json()
        assert "test_002" in json_str
        assert "abc123" in json_str
        
        # Test from_dict
        restored = ProvenanceRecord.from_dict(record_dict)
        assert restored.artifact_id == record.artifact_id
        assert restored.checksum == record.checksum


class TestPipelineRun:
    """Tests for PipelineRun dataclass."""
    
    def test_run_creation(self):
        """Test creating a PipelineRun."""
        run = PipelineRun(
            run_id="run_001",
            started_at=datetime.datetime.now().isoformat()
        )
        
        assert run.run_id == "run_001"
        assert run.status == "running"
        assert run.ended_at is None
    
    def test_run_serialization(self):
        """Test PipelineRun serialization."""
        run = PipelineRun(
            run_id="run_002",
            started_at=datetime.datetime.now().isoformat(),
            config_snapshot={"key": "value"}
        )
        
        run.steps.append({"step": "test"})
        run.artifacts_created.append("artifact_001")
        
        json_str = run.to_json()
        assert "run_002" in json_str
        assert "artifact_001" in json_str


class TestProvenanceTracker:
    """Tests for ProvenanceTracker class."""
    
    @pytest.fixture
    def tracker(self, tmp_path):
        """Create a ProvenanceTracker with temporary manifest directory."""
        manifest_dir = tmp_path / "manifests"
        return ProvenanceTracker(manifest_dir=manifest_dir)
    
    def test_tracker_initialization(self, tracker):
        """Test ProvenanceTracker initialization."""
        assert tracker.manifest_dir.exists()
        assert tracker.records == []
        assert tracker.current_run is None
    
    def test_start_run(self, tracker):
        """Test starting a pipeline run."""
        run_id = tracker.start_run(config={"param": "value"})
        
        assert tracker.current_run is not None
        assert tracker.current_run.run_id == run_id
        assert tracker.current_run.status == "running"
        assert tracker.current_run.config_snapshot == {"param": "value"}
    
    def test_end_run(self, tracker):
        """Test ending a pipeline run."""
        tracker.start_run()
        tracker.end_run(status="completed")
        
        assert tracker.current_run.status == "completed"
        assert tracker.current_run.ended_at is not None
    
    def test_add_step(self, tracker):
        """Test adding a step to a run."""
        tracker.start_run()
        tracker.add_step("download_data", "download", {"source": "NCBI"})
        
        assert len(tracker.current_run.steps) == 1
        step = tracker.current_run.steps[0]
        assert step["step_name"] == "download_data"
        assert step["step_type"] == "download"
    
    def test_record_artifact(self, tracker):
        """Test recording an artifact."""
        tracker.start_run()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            record = tracker.record_artifact(
                artifact_id="test_artifact",
                artifact_type="raw_data",
                source_type="real",
                file_path=temp_path
            )
            
            assert len(tracker.records) == 1
            assert record.artifact_id == "test_artifact"
            assert record.source_type == "real"
            assert record.file_path == temp_path
            assert record.checksum is not None
            assert len(record.checksum) == 64  # SHA256 hex length
        finally:
            os.unlink(temp_path)
    
    def test_compute_checksum(self, tracker):
        """Test checksum computation."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test content for checksum")
            temp_path = f.name
        
        try:
            checksum = tracker.compute_checksum(temp_path)
            assert len(checksum) == 64
            assert all(c in '0123456789abcdef' for c in checksum)
        finally:
            os.unlink(temp_path)
    
    def test_save_manifest(self, tracker):
        """Test saving provenance manifest."""
        tracker.start_run()
        tracker.add_step("test_step", "test")
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("content")
            temp_path = f.name
        
        try:
            tracker.record_artifact(
                artifact_id="test_art",
                artifact_type="data",
                source_type="synthetic",
                file_path=temp_path
            )
            
            manifest_path = tracker.save_manifest("test_manifest.json")
            
            assert manifest_path.exists()
            
            with open(manifest_path) as f:
                manifest_data = json.load(f)
            
            assert manifest_data["total_records"] == 1
            assert manifest_data["records"][0]["artifact_id"] == "test_art"
        finally:
            os.unlink(temp_path)
    
    def test_global_tracker_singleton(self):
        """Test that get_provenance_tracker returns a singleton."""
        tracker1 = get_provenance_tracker()
        tracker2 = get_provenance_tracker()
        
        assert tracker1 is tracker2
    
    def test_record_provenance_convenience_function(self, tmp_path):
        """Test the record_provenance convenience function."""
        # Create a temporary tracker
        tracker = ProvenanceTracker(manifest_dir=tmp_path)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test")
            temp_path = f.name
        
        try:
            # Temporarily replace global tracker
            import src.utils.provenance as prov_module
            original_tracker = prov_module._tracker
            prov_module._tracker = tracker
            
            try:
                record = record_provenance(
                    artifact_id="convenience_test",
                    artifact_type="test",
                    source_type="synthetic",
                    file_path=temp_path
                )
                
                assert record.artifact_id == "convenience_test"
                assert len(tracker.records) == 1
            finally:
                prov_module._tracker = original_tracker
        finally:
            os.unlink(temp_path)