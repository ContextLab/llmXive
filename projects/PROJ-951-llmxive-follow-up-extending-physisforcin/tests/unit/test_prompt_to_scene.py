import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock
import pytest

import sys
# Ensure the code directory is in the path for imports
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.filtering.prompt_to_scene import (
    parse_prompt_for_objects,
    resolve_asset_path,
    parse_initial_pose,
    translate_prompt_to_scene,
    save_scene_config,
)
from src.utils.io_utils import ensure_dirs


class TestParsePromptForObjects:
    def test_parse_simple_object(self):
        prompt = "A red cube on a table"
        objects = parse_prompt_for_objects(prompt)
        assert len(objects) == 1
        assert objects[0]["type"] == "cube"
        assert objects[0]["color"] == "red"

    def test_parse_multiple_objects(self):
        prompt = "A blue sphere and a green cylinder"
        objects = parse_prompt_for_objects(prompt)
        assert len(objects) == 2
        assert objects[0]["type"] == "sphere"
        assert objects[0]["color"] == "blue"
        assert objects[1]["type"] == "cylinder"
        assert objects[1]["color"] == "green"

    def test_parse_with_attributes(self):
        prompt = "A large metallic ball"
        objects = parse_prompt_for_objects(prompt)
        assert len(objects) == 1
        assert objects[0]["type"] == "ball"
        assert objects[0]["size"] == "large"
        assert objects[0]["material"] == "metallic"

    def test_parse_empty_prompt(self):
        prompt = ""
        objects = parse_prompt_for_objects(prompt)
        assert len(objects) == 0

    def test_parse_unknown_object(self):
        prompt = "A flibber on a table"
        objects = parse_prompt_for_objects(prompt)
        # Should handle unknown objects gracefully (either ignore or default)
        # For this test, we assume it returns an object with type 'unknown' or similar
        # or returns an empty list. Adjust based on actual implementation.
        # Assuming implementation returns an object with type 'unknown'
        assert len(objects) == 1
        assert objects[0]["type"] == "unknown"


class TestResolveAssetPath:
    def test_resolve_known_asset(self):
        asset_name = "cube"
        # Mock the asset directory to exist
        with patch("src.filtering.prompt_to_scene.ASSET_DIR", Path(tempfile.gettempdir())):
            # Create a dummy file to simulate the asset
            dummy_file = Path(tempfile.gettempdir()) / "cube.urdf"
            dummy_file.touch()
            try:
                path = resolve_asset_path(asset_name)
                assert path is not None
                assert path.exists()
            finally:
                dummy_file.unlink()

    def test_resolve_unknown_asset(self):
        asset_name = "nonexistent_asset_xyz"
        with patch("src.filtering.prompt_to_scene.ASSET_DIR", Path(tempfile.gettempdir())):
            path = resolve_asset_path(asset_name)
            assert path is None

    def test_resolve_with_extension(self):
        asset_name = "sphere.urdf"
        with patch("src.filtering.prompt_to_scene.ASSET_DIR", Path(tempfile.gettempdir())):
            dummy_file = Path(tempfile.gettempdir()) / "sphere.urdf"
            dummy_file.touch()
            try:
                path = resolve_asset_path(asset_name)
                assert path is not None
                assert path.exists()
            finally:
                dummy_file.unlink()


class TestParseInitialPose:
    def test_parse_position_only(self):
        prompt = "at position 1.0, 2.0, 3.0"
        pose = parse_initial_pose(prompt)
        assert pose is not None
        assert pose["position"] == [1.0, 2.0, 3.0]
        assert pose["orientation"] == [0.0, 0.0, 0.0, 1.0]  # Default quaternion

    def test_parse_position_and_orientation(self):
        prompt = "at position 0.0, 0.0, 0.0 with orientation 0.0, 0.0, 0.0, 1.0"
        pose = parse_initial_pose(prompt)
        assert pose is not None
        assert pose["position"] == [0.0, 0.0, 0.0]
        assert pose["orientation"] == [0.0, 0.0, 0.0, 1.0]

    def test_parse_no_pose_info(self):
        prompt = "a red cube"
        pose = parse_initial_pose(prompt)
        assert pose is None

    def test_parse_invalid_position(self):
        prompt = "at position 1.0, abc, 3.0"
        pose = parse_initial_pose(prompt)
        assert pose is None

    def test_parse_invalid_orientation(self):
        prompt = "at position 1.0, 2.0, 3.0 with orientation 0.0, 0.0, 0.0"
        pose = parse_initial_pose(prompt)
        # Should handle invalid orientation (e.g., wrong number of components)
        assert pose is None


class TestTranslatePromptToScene:
    def test_translate_full_prompt(self):
        prompt = "A red cube at position 1.0, 2.0, 3.0"
        scene_config = translate_prompt_to_scene(prompt)
        assert scene_config is not None
        assert "objects" in scene_config
        assert "initial_pose" in scene_config

    def test_translate_prompt_with_multiple_objects(self):
        prompt = "A blue sphere at 0,0,0 and a green cylinder at 1,1,1"
        scene_config = translate_prompt_to_scene(prompt)
        assert scene_config is not None
        assert len(scene_config["objects"]) == 2

    def test_translate_prompt_with_unknown_object(self):
        prompt = "A flibber at 0,0,0"
        scene_config = translate_prompt_to_scene(prompt)
        # Should handle unknown objects gracefully
        assert scene_config is not None

    def test_translate_prompt_without_pose(self):
        prompt = "A red cube"
        scene_config = translate_prompt_to_scene(prompt)
        assert scene_config is not None
        assert scene_config["initial_pose"] is None


class TestSaveSceneConfig:
    def test_save_scene_config(self):
        scene_config = {
            "objects": [{"type": "cube", "color": "red"}],
            "initial_pose": {"position": [0.0, 0.0, 0.0], "orientation": [0.0, 0.0, 0.0, 1.0]},
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "scene_config.json"
            save_scene_config(scene_config, str(output_path))
            assert output_path.exists()
            with open(output_path, "r") as f:
                loaded_config = json.load(f)
            assert loaded_config == scene_config

    def test_save_scene_config_creates_dirs(self):
        scene_config = {"objects": []}
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "scene_config.json"
            save_scene_config(scene_config, str(output_path))
            assert output_path.exists()

    def test_save_scene_config_invalid_path(self):
        scene_config = {"objects": []}
        with pytest.raises((OSError, IOError)):
            save_scene_config(scene_config, "/nonexistent_dir/scene_config.json")