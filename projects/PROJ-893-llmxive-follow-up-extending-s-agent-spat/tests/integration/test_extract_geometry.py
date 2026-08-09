"""
Integration tests for extract_geometry.py

Verifies that the extraction pipeline correctly handles:
1. Valid scenes (pass through)
2. Malformed scenes (excluded with reason)
3. Missing fields (excluded with reason)
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to mock the Config to point to our temp directories
# Since extract_geometry imports Config at the top, we can't easily mock it
# unless we use unittest.mock.patch. However, for integration tests,
# it's often cleaner to create a temporary directory structure that mimics
# the real one and patch the Config class if possible, or rely on environment variables.

# Given the constraint to use existing API surface, we will assume the test
# runs in an environment where we can patch the paths or we create a
# minimal stub of Config for the test scope.

# Better approach: Patch the imports in extract_geometry module.
# But since we are writing a test file, we can import the module and patch
# the CONFIG object inside it if we access it via the module.

# Let's assume we can modify the code slightly to allow injection, 
# but the prompt says "extend, don't re-author". 
# We will use a monkeypatch on the module-level CONFIG if possible, 
# or create a temporary directory structure and set environment variables 
# that Config might use (though Config uses hardcoded paths in the provided snippet).

# Since the provided Config snippet shows:
#   class Config:
#       def __init__(self):
#           self.data_raw_dir = Path("data/raw")
#           ...
# We can't easily change this without editing code.
# Instead, we will create a temporary directory structure inside the test
# and copy the relevant files, then run the main function of extract_geometry
# after patching the module's CONFIG.

import sys
from unittest.mock import MagicMock

# Import the module to be tested
import code.data.extract_geometry as extract_module
from code.config import Config

@pytest.fixture
def temp_data_structure():
    """Creates a temporary directory structure mimicking the project layout."""
    temp_dir = tempfile.mkdtemp()
    raw_dir = Path(temp_dir) / "data" / "raw" / "s-agent-300k"
    derived_dir = Path(temp_dir) / "data" / "derived"
    results_dir = Path(temp_dir) / "data" / "results"
    
    raw_dir.mkdir(parents=True)
    derived_dir.mkdir(parents=True)
    results_dir.mkdir(parents=True)

    # Create valid scene
    valid_scene = {
        "scene_id": "valid_001",
        "objects": [
            {"id": "obj1", "type": "box", "dimensions": {"x": 1.0, "y": 1.0, "z": 1.0}, "position": {"x": 0.0, "y": 0.0, "z": 0.0}}
        ],
        "constraints": [{"type": "count", "args": ["box"]}],
        "question": "How many boxes?",
        "answer": 1
    }
    with open(raw_dir / "valid_001.json", 'w') as f:
        json.dump(valid_scene, f)

    # Create malformed scene (missing objects)
    malformed_scene = {
        "scene_id": "malformed_001",
        "constraints": [],
        "question": "Test",
        "answer": 0
    }
    with open(raw_dir / "malformed_001.json", 'w') as f:
        json.dump(malformed_scene, f)

    # Create invalid JSON
    with open(raw_dir / "invalid_json.json", 'w') as f:
        f.write("{ this is not json }")

    yield {
        "temp_dir": temp_dir,
        "raw_dir": raw_dir,
        "derived_dir": derived_dir,
        "results_dir": results_dir
    }

    # Cleanup
    shutil.rmtree(temp_dir)

def test_extract_geometry_integration(temp_data_structure):
    """
    Tests that the extraction logic correctly processes valid scenes
    and excludes invalid ones.
    """
    temp_dir = temp_data_structure["temp_dir"]
    raw_dir = temp_data_structure["raw_dir"]
    derived_dir = temp_data_structure["derived_dir"]
    results_dir = temp_data_structure["results_dir"]

    # Patch the Config in the extract_module
    # We create a mock Config that points to our temp directories
    mock_config = MagicMock(spec=Config)
    mock_config.data_raw_dir = raw_dir.parent # Point to data/raw
    mock_config.derived_dir = derived_dir
    mock_config.results_dir = results_dir

    # Patch the CONFIG object in the module
    original_config = extract_module.CONFIG
    extract_module.CONFIG = mock_config

    try:
        # Run the main function
        extract_module.main()

        # Check outputs
        output_file = derived_dir / "constraints.jsonl"
        exclusion_file = results_dir / "exclusion_log.json"

        assert output_file.exists(), "constraints.jsonl was not created"
        assert exclusion_file.exists(), "exclusion_log.json was not created"

        # Read outputs
        with open(output_file, 'r') as f:
            lines = f.readlines()
        
        valid_count = len(lines)
        assert valid_count == 1, f"Expected 1 valid scene, got {valid_count}"

        valid_data = json.loads(lines[0])
        assert valid_data["scene_id"] == "valid_001"

        # Check exclusion log
        with open(exclusion_file, 'r') as f:
            exclusion_log = json.load(f)

        assert exclusion_log["total_scenes_processed"] == 3
        assert exclusion_log["valid_scenes"] == 1
        assert exclusion_log["excluded_scenes_count"] == 2

        excluded_ids = [item["scene_id"] for item in exclusion_log["excluded"]]
        assert "malformed_001" in excluded_ids
        assert "invalid_json" in excluded_ids

    finally:
        # Restore original config
        extract_module.CONFIG = original_config