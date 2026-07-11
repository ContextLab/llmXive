"""
Unit tests for error handling in physics_engine.py
"""

import pytest
import os
import json
import tempfile
from pathlib import Path
from simulation.physics_engine import (
    load_scene_descriptions,
    run_physics_simulation,
    SceneDescriptionNotFoundError,
    InvalidSceneDescriptionError,
    SimulationError
)

class TestLoadSceneDescriptions:
    def test_file_not_found(self):
        """Test that SceneDescriptionNotFoundError is raised for missing file."""
        with pytest.raises(SceneDescriptionNotFoundError):
            load_scene_descriptions("/nonexistent/path/scenes.csv")

    def test_empty_file(self):
        """Test that SceneDescriptionNotFoundError is raised for empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = f.name

        try:
            with pytest.raises(SceneDescriptionNotFoundError):
                load_scene_descriptions(temp_path)
        finally:
            os.unlink(temp_path)

    def test_invalid_format(self):
        """Test that InvalidSceneDescriptionError is raised for missing columns."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("wrong_col1,wrong_col2\n")
            f.write("val1,val2\n")
            temp_path = f.name

        try:
            with pytest.raises(InvalidSceneDescriptionError):
                load_scene_descriptions(temp_path)
        finally:
            os.unlink(temp_path)

    def test_valid_csv(self):
        """Test successful loading of valid CSV."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("scene_id,description\n")
            f.write("1,A ball on a table\n")
            f.write("2,A box next to a cup\n")
            temp_path = f.name

        try:
            scenes = load_scene_descriptions(temp_path)
            assert len(scenes) == 2
            assert scenes[0]['scene_id'] == '1'
            assert scenes[0]['description'] == 'A ball on a table'
        finally:
            os.unlink(temp_path)

class TestRunPhysicsSimulation:
    def test_missing_input_file(self):
        """Test that run_physics_simulation handles missing input gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "output")
            log_path = os.path.join(tmpdir, "log.json")

            # Should return 0 and not crash
            result = run_physics_simulation(
                "/nonexistent/path/scenes.csv",
                output_dir,
                log_path
            )
            assert result == 0

    def test_empty_output_dir_creation(self):
        """Test that output directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_csv = os.path.join(tmpdir, "scenes.csv")
            output_dir = os.path.join(tmpdir, "output", "new_dir")
            log_path = os.path.join(tmpdir, "log.json")

            # Create a minimal valid CSV
            with open(input_csv, 'w') as f:
                f.write("scene_id,description\n")
                f.write("1,A simple scene\n")

            # This should create the output directory
            result = run_physics_simulation(input_csv, output_dir, log_path)
            assert result >= 0 # May be 0 if simulation fails, but shouldn't crash
            assert os.path.exists(output_dir)

    def test_log_file_creation(self):
        """Test that log file is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_csv = os.path.join(tmpdir, "scenes.csv")
            output_dir = os.path.join(tmpdir, "output")
            log_path = os.path.join(tmpdir, "log.json")

            # Create a minimal valid CSV
            with open(input_csv, 'w') as f:
                f.write("scene_id,description\n")
                f.write("1,A simple scene\n")

            run_physics_simulation(input_csv, output_dir, log_path)
            assert os.path.exists(log_path)

            # Verify log file is valid JSON
            with open(log_path, 'r') as f:
                data = json.load(f)
                assert isinstance(data, list)