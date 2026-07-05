"""
Tests for logging utilities.
"""
import pytest
import json
import os
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

# Import the module under test
from code.utils.logging_utils import (
    get_logger,
    log_exclusion,
    log_vr_mapping,
    log_pipeline_step,
    LogType
)

class TestLoggingUtilities:
    """Test cases for logging utilities."""
    
    def test_get_logger_creates_instance(self):
        """Test that get_logger returns a configured logger."""
        logger = get_logger("test_logger")
        assert logger is not None
        assert logger.name == "test_logger"
        assert len(logger.handlers) > 0
    
    def test_log_exclusion_creates_structured_entry(self, caplog):
        """Test that log_exclusion creates a structured JSON entry."""
        with caplog.at_level("WARNING"):
            log_exclusion(
                record_id="MFQ_001",
                reason="schema_validation_failed",
                source="MFQ",
                details={"missing_fields": ["age", "gender"]}
            )
        
        # Verify log contains structured data
        assert any("MFQ_001" in record.message for record in caplog.records)
        assert any("schema_validation_failed" in record.message for record in caplog.records)
        assert any("MFQ" in record.message for record in caplog.records)
    
    def test_log_vr_mapping_creates_structured_entry(self, caplog):
        """Test that log_vr_mapping creates a structured JSON entry."""
        blend_params = {
            "jawOpen": 0.5,
            "browInnerUp": 0.3,
            "eyeBlinkLeft": 0.0
        }
        
        with caplog.at_level("INFO"):
            log_vr_mapping(
                story_id="story_123",
                vr_scene_id="scene_456",
                salience_level="high",
                blend_shape_params=blend_params,
                mapping_rule="high_emotional_intensity"
            )
        
        # Verify log contains structured data
        assert any("story_123" in record.message for record in caplog.records)
        assert any("scene_456" in record.message for record in caplog.records)
        assert any("high" in record.message for record in caplog.records)
        assert any("high_emotional_intensity" in record.message for record in caplog.records)
    
    def test_log_pipeline_step_started(self, caplog):
        """Test logging a pipeline step as started."""
        with caplog.at_level("DEBUG"):
            log_pipeline_step(
                step_name="ingest_data",
                status="started",
                message="Beginning data ingestion"
            )
        
        assert any("ingest_data" in record.message for record in caplog.records)
        assert any("started" in record.message for record in caplog.records)
    
    def test_log_pipeline_step_completed(self, caplog):
        """Test logging a pipeline step as completed."""
        with caplog.at_level("INFO"):
            log_pipeline_step(
                step_name="preprocess",
                status="completed",
                metrics={"rows_processed": 1000, "rows_excluded": 5}
            )
        
        assert any("preprocess" in record.message for record in caplog.records)
        assert any("completed" in record.message for record in caplog.records)
        assert any("1000" in record.message for record in caplog.records)
    
    def test_log_pipeline_step_failed(self, caplog):
        """Test logging a pipeline step as failed."""
        with caplog.at_level("ERROR"):
            log_pipeline_step(
                step_name="model_fit",
                status="failed",
                message="Convergence not achieved"
            )
        
        assert any("model_fit" in record.message for record in caplog.records)
        assert any("failed" in record.message for record in caplog.records)
        assert any("ERROR" in record.message for record in caplog.records)
    
    def test_log_exclusion_with_missing_details(self, caplog):
        """Test that log_exclusion handles missing details gracefully."""
        with caplog.at_level("WARNING"):
            log_exclusion(
                record_id="STORY_999",
                reason="missing_content",
                source="MoralStories"
                # No details provided
            )
        
        assert any("STORY_999" in record.message for record in caplog.records)
        assert any("missing_content" in record.message for record in caplog.records)
    
    def test_log_vr_mapping_low_salience(self, caplog):
        """Test logging a low salience VR mapping."""
        with caplog.at_level("INFO"):
            log_vr_mapping(
                story_id="story_789",
                vr_scene_id="scene_012",
                salience_level="low",
                blend_shape_params={"jawOpen": 0.1, "browInnerUp": 0.0},
                mapping_rule="neutral_expression"
            )
        
        assert any("story_789" in record.message for record in caplog.records)
        assert any("low" in record.message for record in caplog.records)
        assert any("neutral_expression" in record.message for record in caplog.records)