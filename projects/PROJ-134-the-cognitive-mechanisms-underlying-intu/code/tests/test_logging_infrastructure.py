"""
Unit tests for the base logging infrastructure (T009).
Verifies that exclusion reasons and VR mapping logs are captured correctly.
"""
import pytest
import os
import sys
import logging
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

# Ensure code directory is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.logging_utils import (
    LogType,
    get_logger,
    get_log_path,
    log_exclusion,
    log_vr_mapping,
    log_pipeline_step,
    get_exclusion_log_path,
    get_vr_mapping_log_path
)
from code.config import ensure_directories


class TestLoggingInfrastructure:
    """Tests for the logging infrastructure."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up temporary directories for logging tests."""
        self.tmp_dir = tmp_path
        self.log_dir = self.tmp_dir / "data" / "logs"
        self.log_dir.mkdir(parents=True)

        # Patch ensure_directories to use our temp directory
        with patch('code.utils.logging_utils.ensure_directories') as mock_ensure:
            mock_ensure.side_effect = lambda dirs: [d.mkdir(parents=True, exist_ok=True) for d in dirs if isinstance(d, Path)]
            yield

    def test_get_logger_creates_handlers(self):
        """Test that get_logger creates appropriate handlers."""
        logger = get_logger("test_logger")
        assert logger is not None
        assert len(logger.handlers) > 0
        assert logging.INFO in [h.level for h in logger.handlers]

    def test_get_log_path_returns_correct_location(self):
        """Test that log paths are generated correctly."""
        path = get_log_path("exclusion")
        assert path.suffix == ".log"
        assert "exclusion" in path.name

        path_vr = get_log_path("vr_mapping")
        assert "vr_mapping" in path_vr.name

        path_cat = get_log_path("pipeline", category="test")
        assert "pipeline_test" in path_cat.name

    def test_log_exclusion_creates_entry(self, tmp_path):
        """Test that exclusion logging creates a valid entry."""
        # Mock file writing to avoid disk I/O in tests
        with patch('code.utils.logging_utils.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            log_exclusion(
                record_id="test_123",
                reason="Missing required field",
                context={"field": "age"}
            )

            # Verify file was called with correct content
            assert mock_open.called
            call_args = mock_open.call_args[0][0]
            assert "exclusion" in str(call_args)

            # Verify log entry content
            write_call = mock_file.write.call_args[0][0]
            entry = json.loads(write_call.strip())
            assert entry["record_id"] == "test_123"
            assert entry["reason"] == "Missing required field"
            assert entry["context"]["field"] == "age"
            assert "timestamp" in entry

    def test_log_vr_mapping_creates_entry(self):
        """Test that VR mapping logging creates a valid entry."""
        with patch('code.utils.logging_utils.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            blend_shapes = {
                "jawOpen": 0.5,
                "mouthSmile": 0.8,
                "eyeBlinkLeft": 0.0
            }

            log_vr_mapping(
                story_id="story_456",
                vr_scene_id="scene_789",
                salience_level="high",
                blend_shapes=blend_shapes,
                mapping_confidence=0.95
            )

            write_call = mock_file.write.call_args[0][0]
            entry = json.loads(write_call.strip())

            assert entry["story_id"] == "story_456"
            assert entry["vr_scene_id"] == "scene_789"
            assert entry["salience_level"] == "high"
            assert entry["mapping_confidence"] == 0.95
            assert entry["blend_shapes"] == blend_shapes

    def test_log_pipeline_step(self):
        """Test that pipeline step logging works for different statuses."""
        statuses = ["STARTED", "COMPLETED", "FAILED"]

        for status in statuses:
            with patch('code.utils.logging_utils.open', create=True) as mock_open:
                mock_file = MagicMock()
                mock_open.return_value.__enter__.return_value = mock_file

                log_pipeline_step(
                    step_name="data_ingestion",
                    status=status,
                    details={"rows_processed": 100}
                )

                write_call = mock_file.write.call_args[0][0]
                entry = json.loads(write_call.strip())

                assert entry["step_name"] == "data_ingestion"
                assert entry["status"] == status
                assert entry["details"]["rows_processed"] == 100

    def test_log_type_constants(self):
        """Test that LogType constants are defined correctly."""
        assert LogType.EXCLUSION == "exclusion"
        assert LogType.VR_MAPPING == "vr_mapping"
        assert LogType.PIPELINE_STEP == "pipeline_step"
        assert LogType.ERROR == "error"

    def test_get_exclusion_log_path(self):
        """Test helper function for exclusion log path."""
        path = get_exclusion_log_path()
        assert "exclusion" in path.name
        assert path.suffix == ".log"

    def test_get_vr_mapping_log_path(self):
        """Test helper function for VR mapping log path."""
        path = get_vr_mapping_log_path()
        assert "vr_mapping" in path.name
        assert path.suffix == ".log"
