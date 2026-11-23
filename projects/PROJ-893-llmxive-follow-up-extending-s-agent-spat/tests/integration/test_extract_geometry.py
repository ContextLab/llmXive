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
import sys
from unittest.mock import MagicMock, patch

# Import the module to be tested
# We need to ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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

    # We need to patch the module-level CONFIG in extract_geometry
    # Since extract_geometry imports Config and instantiates it, we patch the attribute
    # on the module after import.
    
    # Create a mock config object that mimics the real Config structure
    # but points to our temp directories.
    mock_config = MagicMock()
    # The real Config has attributes like data_raw_dir, derived_dir, results_dir
    # We need to match the names used in extract_geometry.py
    # Based on typical patterns, it likely uses:
    #   CONFIG.data_raw_dir -> raw_dir parent (data/raw)
    #   CONFIG.derived_dir -> derived_dir
    #   CONFIG.results_dir -> results_dir
    
    mock_config.data_raw_dir = raw_dir.parent 
    mock_config.derived_dir = derived_dir
    mock_config.results_dir = results_dir

    # Patch the CONFIG object in the module
    original_config = getattr(extract_module, 'CONFIG', None)
    extract_module.CONFIG = mock_config

    try:
        # Run the main function
        # We need to ensure the working directory allows relative paths if used
        # But since we patched CONFIG to use absolute paths, it should be fine.
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
        if original_config is not None:
            extract_module.CONFIG = original_config
        elif hasattr(extract_module, 'CONFIG'):
            delattr(extract_module, 'CONFIG')