import pytest
import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent))

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
    """Tests for the base logging infrastructure (T009)."""

    def test_get_logger_initialization(self):
        """Test that a logger is correctly initialized with handlers."""
        logger = get_logger("test_logger_init")
        assert logger is not None
        assert len(logger.handlers) > 0
        assert logger.level == logging.INFO

    def test_get_log_path_structure(self):
        """Test that log paths are generated in the correct directory."""
        ensure_directories()
        path = get_log_path(LogType.EXCLUSION)
        assert path.suffix == ".log"
        assert "data/logs" in str(path)
        assert "exclusion" in path.name

    def test_log_exclusion_functionality(self):
        """Test that exclusion logs are written correctly."""
        # Mock the file writing to avoid actual disk I/O in tests if needed,
        # but here we verify the function runs without error and creates the file.
        ensure_directories()
        log_exclusion(
            record_id="TEST-001",
            reason="Missing required field",
            source="MFQ",
            details={"field": "age", "value": None}
        )
        
        # Verify log file exists
        log_path = get_exclusion_log_path()
        assert log_path.exists(), f"Exclusion log file not found at {log_path}"

    def test_log_vr_mapping_functionality(self):
        """Test that VR mapping logs are written correctly."""
        ensure_directories()
        log_vr_mapping(
            story_id="STORY-101",
            vr_scene_id="SCENE-A",
            salience_level="high",
            blend_shape_params={"jawOpen": 0.5, "mouthSmile": 0.8},
            mapping_confidence=0.95
        )

        log_path = get_vr_mapping_log_path()
        assert log_path.exists(), f"VR mapping log file not found at {log_path}"

    def test_log_pipeline_step_functionality(self):
        """Test that pipeline step logs are written correctly."""
        ensure_directories()
        log_pipeline_step(
            step_name="preprocess",
            status="COMPLETED",
            duration_seconds=12.5,
            records_processed=1000,
            message="Successfully mapped stories to scenes"
        )

        log_path = get_log_path(LogType.PIPELINE_STEP)
        assert log_path.exists(), f"Pipeline log file not found at {log_path}"

    def test_log_types_enum(self):
        """Test that LogType enum values are correct."""
        assert LogType.EXCLUSION.value == "exclusion"
        assert LogType.VR_MAPPING.value == "vr_mapping"
        assert LogType.PIPELINE_STEP.value == "pipeline_step"

    def test_get_exclusion_log_path(self):
        """Test helper function for exclusion log path."""
        path = get_exclusion_log_path()
        assert isinstance(path, Path)
        assert path.suffix == ".log"

    def test_get_vr_mapping_log_path(self):
        """Test helper function for VR mapping log path."""
        path = get_vr_mapping_log_path()
        assert isinstance(path, Path)
        assert path.suffix == ".log"
