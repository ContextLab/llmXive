"""
Unit tests for T016: Logging Integration.
Verifies that data sources are logged and VLM calls are tracked (and expected to be zero).
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from src.data_synthesis.logging_integration import LabelingAuditLogger
from src.data_synthesis.visual_labeler import VisualLabeler, FrameLabel
from src.data_synthesis.models import SyntheticVideoFrame
from src.utils.logging import get_logger


@pytest.fixture
def temp_dirs():
    """Create temporary input and output directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_dir = Path(tmpdir) / "raw"
        output_dir = Path(tmpdir) / "labeled"
        input_dir.mkdir()
        output_dir.mkdir()
        
        # Create a dummy input file
        dummy_file = input_dir / "test_chunk.jsonl"
        with open(dummy_file, 'w') as f:
            f.write(json.dumps({"frame_id": 1, "activity": "sitting"}) + "\n")
        
        yield {
            "input_dir": input_dir,
            "output_dir": output_dir,
            "dummy_file": dummy_file
        }


@pytest.fixture
def mock_labeler():
    """Create a mock VisualLabeler that returns dummy labels."""
    labeler = MagicMock(spec=VisualLabeler)
    mock_label = FrameLabel(
        frame_id=1,
        timestamp=0.0,
        is_critical=False,
        confidence=0.9,
        label_source="YOLO_RULES"
    )
    labeler.label_video_stream.return_value = [mock_label]
    return labeler


def test_log_data_source(temp_dirs, caplog):
    """Test that data sources are correctly logged."""
    logger = LabelingAuditLogger(str(temp_dirs["output_dir"]))
    
    with patch("src.data_synthesis.logging_integration.log_data_event") as mock_log_event:
        logger.log_data_source(str(temp_dirs["dummy_file"]), "chunk_001")
        
        # Verify the log_data_event was called
        assert mock_log_event.called
        call_args = mock_log_event.call_args
        assert call_args[1]["event_type"] == "DATA_SOURCE_LOADED"
        assert call_args[1]["details"]["path"] == str(temp_dirs["dummy_file"])
        assert call_args[1]["details"]["chunk_id"] == "chunk_001"
        
        # Verify internal tracking
        assert len(logger.data_sources_logged) == 1
        assert temp_dirs["dummy_file"] in logger.data_sources_logged


def test_vlm_call_tracking(temp_dirs):
    """Test that VLM calls are tracked and counted."""
    logger = LabelingAuditLogger(str(temp_dirs["output_dir"]))
    
    # Simulate a VLM call detection (should not happen in real visual labeling)
    with patch("src.data_synthesis.logging_integration.log_vlm_call") as mock_log_vlm:
        logger._on_vlm_call_detected({"test": "context"})
        
        assert logger.vlm_call_count == 1
        mock_log_vlm.assert_called_once()
        assert mock_log_vlm.call_args[1]["reason"] == "VIOLATION: Visual labeling should not use VLM"


def test_label_video_stream_no_vlm(temp_dirs, mock_labeler, caplog):
    """Test that the labeling process logs zero VLM calls."""
    logger = LabelingAuditLogger(str(temp_dirs["output_dir"]))
    
    with patch("src.data_synthesis.logging_integration.log_no_vlm_call") as mock_log_no_vlm:
        logger.label_video_stream(
            labeler=mock_labeler,
            video_path=str(temp_dirs["dummy_file"]),
            output_path=str(temp_dirs["output_dir"] / "output.jsonl")
        )
        
        # Verify no VLM calls were made
        assert logger.vlm_call_count == 0
        
        # Verify the 'no VLM' log was recorded
        mock_log_no_vlm.assert_called_once()
        assert mock_log_no_vlm.call_args[1]["reason"] == "Visual labeling completed using rule-based object detection"
        
        # Verify output file was created
        output_file = Path(temp_dirs["output_dir"]) / "output.jsonl"
        assert output_file.exists()


def test_generate_audit_report_pass(temp_dirs, mock_labeler):
    """Test audit report generation when VLM calls are zero."""
    logger = LabelingAuditLogger(str(temp_dirs["output_dir"]))
    
    logger.label_video_stream(
        labeler=mock_labeler,
        video_path=str(temp_dirs["dummy_file"]),
        output_path=str(temp_dirs["output_dir"] / "output.jsonl")
    )
    
    report_path = str(temp_dirs["output_dir"] / "audit.json")
    report = logger.generate_audit_report(report_path)
    
    assert report["verdict"] == "PASS"
    assert report["vlm_api_calls_detected"] == 0
    assert report["data_sources_processed"] == 1
    
    # Verify file content
    with open(report_path, 'r') as f:
        saved_report = json.load(f)
        assert saved_report["verdict"] == "PASS"


def test_generate_audit_report_fail(temp_dirs):
    """Test audit report generation when VLM calls are detected."""
    logger = LabelingAuditLogger(str(temp_dirs["output_dir"]))
    
    # Manually inject a VLM call count to simulate failure
    logger.vlm_call_count = 1
    logger.data_sources_logged.append(str(temp_dirs["dummy_file"]))
    
    report_path = str(temp_dirs["output_dir"] / "audit_fail.json")
    report = logger.generate_audit_report(report_path)
    
    assert report["verdict"] == "FAIL"
    assert report["vlm_api_calls_detected"] == 1
    assert "VIOLATION" in report["log_message"]