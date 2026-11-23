"""
Contract test for SymbolicObservation schema validation.

Verifies that the output of the symbolic transformation pipeline
strictly adheres to the SymbolicObservation Pydantic model defined
in code/data/models.py.
"""
import pytest
import json
from datetime import datetime
from pydantic import ValidationError

# Import the model from the project code
import sys
from pathlib import Path
# Add the project root to the path to allow imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from data.models import SymbolicObservation

def test_valid_symbolic_observation(sample_symbolic_observation):
    """Test that a valid observation dictionary parses correctly."""
    obs = SymbolicObservation(**sample_symbolic_observation)
    assert obs.trajectory_id == "test_traj_001"
    assert len(obs.objects) == 1
    assert obs.scene_empty is False

def test_missing_required_field():
    """Test that missing required fields raise ValidationError."""
    invalid_data = {
        "timestamp": datetime.now().isoformat(),
        # Missing trajectory_id
        "frame_index": 1,
        "objects": [],
        "scene_empty": True
    }
    with pytest.raises(ValidationError):
        SymbolicObservation(**invalid_data)

def test_invalid_object_structure():
    """Test that an object missing required fields raises ValidationError."""
    invalid_obs = {
        "timestamp": datetime.now().isoformat(),
        "trajectory_id": "test_001",
        "frame_index": 1,
        "objects": [
            {
                "class_label": "cup"
                # Missing bbox, centroid, color_histogram
            }
        ],
        "scene_empty": False
    }
    with pytest.raises(ValidationError):
        SymbolicObservation(**invalid_obs)

def test_empty_objects_list_valid():
    """Test that an empty objects list is valid if scene_empty is True."""
    data = {
        "timestamp": datetime.now().isoformat(),
        "trajectory_id": "test_001",
        "frame_index": 1,
        "objects": [],
        "scene_empty": True
    }
    obs = SymbolicObservation(**data)
    assert len(obs.objects) == 0
    assert obs.scene_empty is True
