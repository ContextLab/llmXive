"""
Pytest configuration and shared fixtures for the llmXive project.

Provides fixtures for:
- Temporary data directories
- Mocked configuration states
- Sample symbolic trajectories for testing
"""
import os
import json
import tempfile
import pytest
from pathlib import Path
from datetime import datetime

# Ensure project root is in path for imports if running from tests/
# Note: In the actual runner, the working directory should be set correctly.

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory structure mimicking the project data layout."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        (base / "raw").mkdir()
        (base / "processed").mkdir()
        (base / "artifacts").mkdir()
        yield base
    
@pytest.fixture
def sample_symbolic_observation():
    """Generate a minimal valid SymbolicObservation dictionary for testing."""
    return {
        "timestamp": datetime.now().isoformat(),
        "trajectory_id": "test_traj_001",
        "frame_index": 1,
        "objects": [
            {
                "class_label": "cup",
                "bbox": [10.0, 20.0, 100.0, 120.0],
                "centroid": [60.0, 70.0],
                "color_histogram": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0] * 3
            }
        ],
        "scene_empty": False,
        "perception_latency_ms": 45.2
    }

@pytest.fixture
def sample_trajectory_json(sample_symbolic_observation):
    """Create a temporary JSON file representing a trajectory."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        data = {
            "trajectory_id": "test_traj_001",
            "task": "pick_and_place",
            "frames": [sample_symbolic_observation, sample_symbolic_observation]
        }
        json.dump(data, f)
        path = f.name
    yield path
    os.unlink(path)
