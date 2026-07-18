"""
Unit tests for the prompt-to-scene translation logic.

Tests T014 implementation in src/filtering/prompt_to_scene.py.
"""
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock
import pytest

# Import the module under test
# Note: We need to ensure the code directory is in the path for imports to work
import sys
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.filtering.prompt_to_scene import (
    parse_prompt_for_objects,
    resolve_asset_path,
    parse_initial_pose,
    translate_prompt_to_scene,
    save_scene_config,
    ASSET_MAPPING,
    DEFAULT_POSES
)
from src.utils.io_utils import ensure_dirs

class TestParsePromptForObjects:
    def test_extract_robot_and_object(self):
        prompt = "The panda robot moves the cube on the table."
        result = parse_prompt_for_objects(prompt)
        assert "panda" in result
        assert "cube" in result
        assert "table" in result

    def test_extract_multiple_objects(self):
        prompt = "Place the can and the bottle on the floor."
        result = parse_prompt_for_objects(prompt)
        assert "can" in result
        assert "bottle" in result
        assert "floor" in result

    def test_no_match(self):
        prompt = "The sky is blue and the grass is green."
        result = parse_prompt_for_objects(prompt)
        assert len(result) == 0

    def test_case_insensitivity(self):
        prompt = "The PANDA moves the CUBE."
        result = parse_prompt_for_objects(prompt)
        assert "panda" in result
        assert "cube" in result

    def test_duplicate_removal(self):
        prompt = "The panda moves the cube. The panda stops."
        result = parse_prompt_for_objects(prompt)
        assert result.count("panda") == 1
        assert result.count("cube") == 1

class TestResolveAssetPath:
    @patch('src.filtering.prompt_to_scene.DEFAULT_ASSET_ROOT')
    def test_asset_exists_in_mapping(self, mock_root):
        # Create a temporary file to simulate an existing asset
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_root.__truediv__.return_value.__truediv__.return_value = Path(tmpdir)
            # We need to mock the .exists() method of the resulting path
            # But resolve_asset_path constructs the path. 
            # Let's mock the Path.exists method globally for this test context
            with patch('pathlib.Path.exists', return_value=True):
                path = resolve_asset_path("panda", asset_root=Path(tmpdir))
                assert path is not None
                assert "franka_panda/panda.urdf" in path

    @patch('src.filtering.prompt_to_scene.pybullet_data')
    def test_fallback_to_pybullet_data(self, mock_pybullet_data):
        # Mock pybullet_data.getDataPath to return a temp dir
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create the expected relative path inside tmpdir
            rel_path = "franka_panda/panda.urdf"
            full_path = Path(tmpdir) / rel_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.touch()
            
            mock_pybullet_data.getDataPath.return_value = tmpdir
            
            # Mock DEFAULT_ASSET_ROOT.exists to return False to force fallback
            with patch('src.filtering.prompt_to_scene.DEFAULT_ASSET_ROOT.__truediv__.return_value.exists', return_value=False):
                with patch('pathlib.Path.exists', return_value=True): # For the pybullet path check
                    path = resolve_asset_path("panda")
                    assert path is not None
                    assert tmpdir in path

    def test_missing_asset(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Ensure path does not exist
            result = resolve_asset_path("nonexistent_object_xyz", asset_root=Path(tmpdir))
            assert result is None

class TestParseInitialPose:
    def test_default_pose(self):
        pose = parse_initial_pose("move the block", "block")
        # Should fall back to default or default pose for 'block' (which maps to cube_small)
        # In our logic, 'block' is not in DEFAULT_POSES, so it returns identity
        assert pose == (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0)

    def test_parse_coordinates_at(self):
        prompt = "move the block at (1.0, 2.0, 3.5)"
        pose = parse_initial_pose(prompt, "block")
        assert pose[0] == 1.0
        assert pose[1] == 2.0
        assert pose[2] == 3.5
        # Orientation defaults to identity
        assert pose[6] == 1.0

    def test_parse_coordinates_named(self):
        prompt = "place block x=5.0 y=10.0 z=2.0"
        pose = parse_initial_pose(prompt, "block")
        assert pose[0] == 5.0
        assert pose[1] == 10.0
        assert pose[2] == 2.0

    def test_default_pose_for_known_object(self):
        # 'table' has a specific default pose in DEFAULT_POSES
        pose = parse_initial_pose("place on table", "table")
        assert pose == DEFAULT_POSES["table"]

class TestTranslatePromptToScene:
    def test_full_translation_success(self):
        # Mock resolve_asset_path to return a fake path
        with patch('src.filtering.prompt_to_scene.resolve_asset_path', return_value="/fake/path.urdf"):
            prompt = "The panda moves the cube."
            result = translate_prompt_to_scene(prompt)
            
            assert result["prompt"] == prompt
            assert result["status"] == "success"
            assert len(result["objects"]) == 2 # panda and cube
            
            # Check structure of objects
            for obj in result["objects"]:
                assert "name" in obj
                assert "urdf_path" in obj
                assert "initial_pose" in obj
                assert len(obj["initial_pose"]) == 7

    def test_partial_translation_missing_assets(self):
        # Mock resolve_asset_path to return None for one object
        def mock_resolve(name):
            if name == "panda":
                return "/fake/panda.urdf"
            return None

        with patch('src.filtering.prompt_to_scene.resolve_asset_path', side_effect=mock_resolve):
            prompt = "The panda moves the unknown_gizmo."
            result = translate_prompt_to_scene(prompt)
            
            assert result["status"] == "partial"
            assert "unknown_gizmo" in result["missing_assets"]
            assert len(result["objects"]) == 1 # Only panda

class TestSaveSceneConfig:
    def test_save_to_json(self):
        scene_config = {
            "prompt": "test",
            "objects": [{"name": "panda", "urdf_path": "x.urdf", "initial_pose": [0]*7}],
            "status": "success"
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "scene.json"
            save_scene_config(scene_config, output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            
            assert loaded["prompt"] == "test"
            assert loaded["status"] == "success"