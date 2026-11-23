import json
import os
import tempfile
from pathlib import Path
import pytest

from utils.logger import log_perception_ground_truth
from utils.exceptions import DatasetUnavailableError

@pytest.fixture
def temp_log_path():
    """Create a temporary log file path."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        path = Path(f.name)
    yield path
    if path.exists():
        os.unlink(path)

@pytest.fixture
def temp_gt_path():
    """Create a temporary ground truth file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        # Create a simple ground truth structure
        gt_data = {
            "objects": [
                {"class": "cup", "bbox": [10, 10, 50, 50]},
                {"class": "bowl", "bbox": [100, 100, 150, 150]}
            ]
        }
        json.dump(gt_data, f)
        path = Path(f.name)
    yield path
    if path.exists():
        os.unlink(path)

def test_log_perception_ground_truth_with_match(temp_log_path, temp_gt_path):
    """Test logging when detected objects match ground truth."""
    detected = [
        {"class": "cup", "bbox": [10, 10, 50, 50], "centroid": [35.0, 35.0], "color_hist": [0.1, 0.2, 0.3]}
    ]
    confidences = [0.95]
    
    log_perception_ground_truth(
        log_path=temp_log_path,
        timestamp=1234567890.0,
        detected_objects=detected,
        confidence_scores=confidences,
        ground_truth_path=temp_gt_path
    )
    
    assert temp_log_path.exists()
    with open(temp_log_path, 'r') as f:
        entry = json.loads(f.readline())
    
    assert entry["timestamp"] == 1234567890.0
    assert len(entry["detected_objects"]) == 1
    assert entry["object_missing_if_visible"] is False

def test_log_perception_ground_truth_missing_object(temp_log_path, temp_gt_path):
    """Test logging when a ground truth object is missed."""
    # Only detect one object, but GT has two
    detected = [
        {"class": "cup", "bbox": [10, 10, 50, 50], "centroid": [35.0, 35.0], "color_hist": [0.1, 0.2, 0.3]}
    ]
    confidences = [0.95]
    
    log_perception_ground_truth(
        log_path=temp_log_path,
        timestamp=1234567890.0,
        detected_objects=detected,
        confidence_scores=confidences,
        ground_truth_path=temp_gt_path
    )
    
    with open(temp_log_path, 'r') as f:
        entry = json.loads(f.readline())
    
    # GT has cup and bowl, we only detected cup -> missing is True
    assert entry["object_missing_if_visible"] is True

def test_log_perception_ground_truth_no_gt_file(temp_log_path):
    """Test that DatasetUnavailableError is raised if GT file is missing."""
    detected = [{"class": "cup", "bbox": [10, 10, 50, 50], "centroid": [35.0, 35.0], "color_hist": []}]
    
    with pytest.raises(DatasetUnavailableError):
        log_perception_ground_truth(
            log_path=temp_log_path,
            timestamp=1234567890.0,
            detected_objects=detected,
            confidence_scores=[0.9],
            ground_truth_path=Path("/nonexistent/path/gt.json")
        )

def test_log_perception_ground_truth_empty_gt(temp_log_path):
    """Test logging when ground truth is empty (no objects expected)."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump({"objects": []}, f)
        gt_path = Path(f.name)
    
    try:
        detected = []
        log_perception_ground_truth(
            log_path=temp_log_path,
            timestamp=1234567890.0,
            detected_objects=detected,
            confidence_scores=[],
            ground_truth_path=gt_path
        )
        
        with open(temp_log_path, 'r') as f:
            entry = json.loads(f.readline())
        
        assert entry["object_missing_if_visible"] is False
    finally:
        gt_path.unlink()
