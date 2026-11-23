"""
Unit tests for VisualLabeler module.

These tests verify that the labeling logic relies solely on visual events
and does not invoke any VLM APIs.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import cv2
import numpy as np

from src.data_synthesis.visual_labeler import VisualLabeler, FrameLabel, CRITICAL_CLASSES, CONFIDENCE_THRESHOLD, GROUND_THRESHOLD
from src.utils.logging import log_no_vlm_call

# Mock YOLO to avoid dependency issues during testing
@pytest.fixture
def mock_yolo():
    with patch('src.data_synthesis.visual_labeler.YOLO') as mock_yolo_class:
        mock_model = MagicMock()
        mock_yolo_class.return_value = mock_model
        mock_model.names = {0: 'person', 1: 'car'}
        yield mock_model

@pytest.fixture
def labeler(mock_yolo):
    return VisualLabeler(model_path="dummy.pt", device="cpu")

def create_test_frame(h=480, w=640, color=(0, 0, 0)):
    """Create a blank OpenCV frame."""
    return np.zeros((h, w, 3), dtype=np.uint8)

def test_frame_label_dataclass():
    """Test FrameLabel dataclass creation and validation."""
    label = FrameLabel(
        frame_id="test_001",
        timestamp=1.5,
        label="critical",
        confidence=0.9,
        detected_objects=[],
        metadata={"test": True}
    )
    assert label.frame_id == "test_001"
    assert label.label == "critical"
    assert label.confidence == 0.9
    assert isinstance(label.metadata, dict)

def test_detect_objects_returns_list(labeler, mock_yolo):
    """Test that _detect_objects returns a list of detections."""
    frame = create_test_frame()
    
    # Mock YOLO result
    mock_box = MagicMock()
    mock_box.cls = [0]
    mock_box.conf = [0.9]
    mock_box.xyxy = [[0, 0, 100, 100]]
    
    mock_result = MagicMock()
    mock_result.boxes = mock_box
    mock_result.names = {0: 'person'}
    
    mock_yolo.return_value.return_value = [mock_result]
    
    detections = labeler._detect_objects(frame)
    assert isinstance(detections, list)
    assert len(detections) == 1
    assert detections[0]["class_id"] == 0
    assert detections[0]["confidence"] == 0.9

def test_classify_critical_person_on_ground(labeler):
    """Test that a person detected on the ground is classified as critical."""
    frame = create_test_frame(h=480, w=640)
    h, w = frame.shape[:2]
    
    # Person in lower 20% of frame (y_center > 0.8 * h)
    # h=480, 0.8*h = 384. y_center should be > 384.
    detections = [
        {
            "class_id": 0,
            "class_name": "person",
            "confidence": 0.9,
            "bbox": [100, 400, 200, 480],
            "center_x": 150,
            "center_y": 440  # > 384
        }
    ]
    
    label, conf = labeler._classify_frame(frame, detections)
    assert label == "critical"
    assert conf == 0.9

def test_classify_silence_person_high(labeler):
    """Test that a person detected standing (high in frame) is classified as silence."""
    frame = create_test_frame(h=480, w=640)
    
    # Person in upper part of frame
    detections = [
        {
            "class_id": 0,
            "class_name": "person",
            "confidence": 0.9,
            "bbox": [100, 50, 200, 200],
            "center_x": 150,
            "center_y": 125  # < 384
        }
    ]
    
    label, conf = labeler._classify_frame(frame, detections)
    assert label == "silence"
    assert conf == 0.0

def test_classify_silence_no_person(labeler):
    """Test that no person detected results in silence."""
    frame = create_test_frame()
    detections = [
        {
            "class_id": 1,
            "class_name": "car",
            "confidence": 0.9,
            "bbox": [0, 0, 100, 100],
            "center_x": 50,
            "center_y": 50
        }
    ]
    
    label, conf = labeler._classify_frame(frame, detections)
    assert label == "silence"

def test_classify_low_confidence_person(labeler):
    """Test that low confidence person detection is ignored."""
    frame = create_test_frame()
    detections = [
        {
            "class_id": 0,
            "class_name": "person",
            "confidence": 0.3, # Below threshold
            "bbox": [0, 400, 100, 480],
            "center_x": 50,
            "center_y": 440
        }
    ]
    
    label, conf = labeler._classify_frame(frame, detections)
    assert label == "silence"

def test_label_frame_integration(labeler, mock_yolo):
    """Test end-to-end frame labeling."""
    frame = create_test_frame()
    mock_box = MagicMock()
    mock_box.cls = [0]
    mock_box.conf = [0.9]
    mock_box.xyxy = [[0, 400, 100, 480]] # Person on ground
    
    mock_result = MagicMock()
    mock_result.boxes = mock_box
    mock_result.names = {0: 'person'}
    mock_yolo.return_value.return_value = [mock_result]
    
    result = labeler.label_frame(frame, "frame_001", 1.0)
    
    assert isinstance(result, FrameLabel)
    assert result.frame_id == "frame_001"
    assert result.label == "critical"
    assert result.confidence == 0.9
    assert len(result.detected_objects) == 1

def test_no_vlm_call_logged():
    """Verify that log_no_vlm_call is invoked during initialization."""
    with patch('src.data_synthesis.visual_labeler.log_no_vlm_call') as mock_log:
        with patch('src.data_synthesis.visual_labeler.YOLO') as mock_yolo:
            mock_model = MagicMock()
            mock_model.names = {0: 'person'}
            mock_yolo.return_value = mock_model
            
            labeler = VisualLabeler(model_path="dummy.pt", device="cpu")
            
            # Check that log_no_vlm_call was called
            mock_log.assert_called_once()
            args, kwargs = mock_log.call_args
            assert "visual_labeler" in args
            assert "YOLO" in args[1] or "object detection" in args[1]

def test_label_video_stream_writes_jsonl(labeler, mock_yolo, tmp_path):
    """Test that label_video_stream writes valid JSONL to disk."""
    # Create a dummy video file (or mock the video capture)
    input_video = tmp_path / "test.mp4"
    output_file = tmp_path / "labels.jsonl"
    
    # Mock cv2.VideoCapture to return a simple frame
    with patch('cv2.VideoCapture') as mock_cap:
        mock_capture = MagicMock()
        mock_capture.isOpened.return_value = True
        mock_capture.get.side_effect = [
            10, # Frame count
            30.0 # FPS
        ]
        mock_capture.read.side_effect = [
            (True, create_test_frame()), # First frame
            (False, None) # End
        ]
        mock_cap.return_value = mock_capture
        
        # Mock YOLO detection
        mock_box = MagicMock()
        mock_box.cls = [0]
        mock_box.conf = [0.9]
        mock_box.xyxy = [[0, 400, 100, 480]]
        mock_result = MagicMock()
        mock_result.boxes = mock_box
        mock_result.names = {0: 'person'}
        mock_yolo.return_value.return_value = [mock_result]
        
        labeler.label_video_stream(str(input_video), str(output_file))
        
        assert output_file.exists()
        with open(output_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 1
            data = json.loads(lines[0])
            assert data['label'] == 'critical'
            assert data['frame_id'] == 'frame_000000'

def test_label_directory_processing(labeler, mock_yolo, tmp_path):
    """Test processing a directory of frames."""
    input_dir = tmp_path / "frames"
    input_dir.mkdir()
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    
    # Create dummy frames
    for i in range(3):
        img_path = input_dir / f"frame_{i:03d}.png"
        cv2.imwrite(str(img_path), create_test_frame())
    
    with patch('cv2.VideoCapture') as mock_cap:
        # Mock directory processing logic (it doesn't use VideoCapture for dirs)
        pass
    
    # Mock YOLO
    mock_box = MagicMock()
    mock_box.cls = [0]
    mock_box.conf = [0.9]
    mock_box.xyxy = [[0, 400, 100, 480]]
    mock_result = MagicMock()
    mock_result.boxes = mock_box
    mock_result.names = {0: 'person'}
    mock_yolo.return_value.return_value = [mock_result]
    
    labeler.label_directory(str(input_dir), str(output_dir))
    
    output_file = output_dir / "frames_labels.jsonl"
    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        lines = f.readlines()
        assert len(lines) == 3
        for line in lines:
            data = json.loads(line)
            assert data['label'] == 'critical'