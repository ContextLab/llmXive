"""
Unit tests for the extract_geometry module.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add code directory to path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "code"))

from data.extract_geometry import load_scene_data, validate_scene_constraints, extract_constraints

def test_validate_scene_valid():
    scene = {
        "id": "scene_001",
        "geometry": {"objects": [{"x": 1.0, "y": 2.0}]},
        "label": 5
    }
    is_valid, reason = validate_scene_constraints(scene)
    assert is_valid is True
    assert reason is None

def test_validate_scene_missing_geometry():
    scene = {
        "id": "scene_002",
        "label": 5
    }
    is_valid, reason = validate_scene_constraints(scene)
    assert is_valid is False
    assert reason == "Missing geometry"

def test_validate_scene_missing_label():
    scene = {
        "id": "scene_003",
        "geometry": {"objects": []}
    }
    is_valid, reason = validate_scene_constraints(scene)
    assert is_valid is False
    assert reason == "Missing label"

def test_validate_scene_malformed_json():
    scene = {
        "id": "scene_004",
        "error": "Invalid JSON structure"
    }
    is_valid, reason = validate_scene_constraints(scene)
    assert is_valid is False
    assert reason == "Malformed JSON"

def test_extract_constraints():
    scenes = [
        {
            "id": "valid_1",
            "geometry": {"objects": [{"x": 1.0}]},
            "label": 1
        },
        {
            "id": "invalid_1",
            "label": 2
        },
        {
            "id": "valid_2",
            "geometry": {"objects": [{"x": 2.0}]},
            "label": 3
        }
    ]
    valid, exclusions = extract_constraints(scenes)
    
    assert len(valid) == 2
    assert len(exclusions) == 1
    assert exclusions[0]["scene_id"] == "invalid_1"
    assert exclusions[0]["reason"] == "Missing geometry"

def test_load_scene_data(tmp_path):
    # Create a temporary JSONL file
    jsonl_file = tmp_path / "test_data.jsonl"
    data = [
        {"id": "s1", "geometry": {"a": 1}, "label": 1},
        {"id": "s2", "geometry": {"a": 2}, "label": 2},
        {"id": "s3", "invalid": "json"} # This one will be marked as error by load_scene_data if it fails to parse, but here it parses as dict
    ]
    with open(jsonl_file, 'w') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')
    
    # Rename to expected name
    expected_file = tmp_path / "s_agent_k_subset.jsonl"
    jsonl_file.rename(expected_file)

    scenes = load_scene_data(tmp_path)
    assert len(scenes) == 3
    assert scenes[0]["id"] == "s1"
    assert scenes[2]["id"] == "s3"

def test_load_scene_data_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_scene_data(Path("/nonexistent/path"))
