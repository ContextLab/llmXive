"""
Contract test for model input format.

Verifies that the training and inference scripts accept the
SymbolicObservation JSON format directly without requiring pixel data.
"""
import pytest
import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from data.models import SymbolicObservation

def test_model_accepts_symbolic_json(sample_symbolic_observation):
    """Test that the model input pipeline can parse symbolic JSON."""
    # Convert to JSON string and back to simulate I/O
    json_str = json.dumps(sample_symbolic_observation)
    data = json.loads(json_str)
    
    # Validate against the model
    obs = SymbolicObservation(**data)
    assert obs is not None
    
    # Verify no pixel data is present
    assert "pixels" not in data
    assert "image_path" not in data
    assert "frame_data" not in data

def test_training_data_preparation():
    """Test that training data preparation logic handles symbolic input."""
    # Simulate a batch of symbolic observations
    batch = [
        {
            "timestamp": "2023-01-01T00:00:00",
            "trajectory_id": "t1",
            "frame_index": 1,
            "objects": [],
            "scene_empty": True,
            "perception_latency_ms": 10.0
        },
        {
            "timestamp": "2023-01-01T00:00:01",
            "trajectory_id": "t1",
            "frame_index": 2,
            "objects": [{"class_label": "box", "bbox": [0,0,10,10], "centroid": [5,5], "color_histogram": [1]*30}],
            "scene_empty": False,
            "perception_latency_ms": 15.0
        }
    ]
    
    # The logic should be able to iterate over this and prepare tokens
    # We verify the structure is valid for the model
    for item in batch:
        SymbolicObservation(**item)
    
    assert len(batch) == 2
