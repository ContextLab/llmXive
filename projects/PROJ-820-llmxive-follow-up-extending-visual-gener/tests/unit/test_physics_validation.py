"""
Unit tests for physics validation and contradiction logging logic in physics_engine.py.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from simulation.physics_engine import (
    PhysicsConstraint,
    update_contradiction_log,
    run_physics_simulation,
    load_scene_descriptions,
    parse_scene_description,
    simulate_physics
)

class TestPhysicsConstraint:
    """Tests for the PhysicsConstraint class."""
    
    def test_constraint_creation(self):
        """Test that a PhysicsConstraint can be created and serialized."""
        constraint = PhysicsConstraint("test_scene_001")
        assert constraint.scene_id == "test_scene_001"
        assert constraint.is_valid is True
        assert constraint.contradiction_reason is None
        assert len(constraint.bounding_boxes) == 0
        assert len(constraint.collision_rules) == 0
    
    def test_constraint_with_contradiction(self):
        """Test that a PhysicsConstraint can be marked as invalid."""
        constraint = PhysicsConstraint("test_scene_002")
        constraint.is_valid = False
        constraint.contradiction_reason = "Cycle detected"
        
        assert constraint.is_valid is False
        assert constraint.contradiction_reason == "Cycle detected"
    
    def test_constraint_to_dict(self):
        """Test serialization of PhysicsConstraint to dictionary."""
        constraint = PhysicsConstraint("test_scene_003")
        constraint.bounding_boxes.append({"object": "box1", "x": 100, "y": 200, "width": 50, "height": 50})
        constraint.collision_rules.append({"type": "overlap", "objects": ["box1", "box2"]})
        constraint.is_valid = True
        
        data = constraint.to_dict()
        assert data["scene_id"] == "test_scene_003"
        assert len(data["bounding_boxes"]) == 1
        assert len(data["collision_rules"]) == 1
        assert data["is_valid"] is True
        assert data["contradiction_reason"] is None

class TestUpdateContradictionLog:
    """Tests for the update_contradiction_log function."""
    
    def test_create_new_log(self):
        """Test that a new contradiction log is created correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "contradiction_log.json"
            constraint = PhysicsConstraint("test_scene")
            constraint.is_valid = True
            
            update_contradiction_log(constraint, str(log_path))
            
            assert log_path.exists()
            with open(log_path, 'r') as f:
                log_data = json.load(f)
            
            assert log_data["total_scenes"] == 1
            assert log_data["contradiction_count"] == 0
            assert len(log_data["log_entries"]) == 1
            assert len(log_data["contradictions"]) == 0
    
    def test_add_contradiction(self):
        """Test that a contradiction is correctly added to the log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "contradiction_log.json"
            constraint = PhysicsConstraint("test_scene")
            constraint.is_valid = False
            constraint.contradiction_reason = "Invalid physics"
            
            update_contradiction_log(constraint, str(log_path))
            
            with open(log_path, 'r') as f:
                log_data = json.load(f)
            
            assert log_data["contradiction_count"] == 1
            assert len(log_data["contradictions"]) == 1
            assert log_data["contradictions"][0]["scene_id"] == "test_scene"
            assert log_data["contradictions"][0]["reason"] == "Invalid physics"
    
    def test_contradiction_rate_calculation(self):
        """Test that contradiction rate is calculated correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "contradiction_log.json"
            
            # Add one valid scene
            constraint1 = PhysicsConstraint("valid_scene")
            constraint1.is_valid = True
            update_contradiction_log(constraint1, str(log_path))
            
            # Add one invalid scene
            constraint2 = PhysicsConstraint("invalid_scene")
            constraint2.is_valid = False
            constraint2.contradiction_reason = "Error"
            update_contradiction_log(constraint2, str(log_path))
            
            with open(log_path, 'r') as f:
                log_data = json.load(f)
            
            assert log_data["total_scenes"] == 2
            assert log_data["contradiction_count"] == 1
            assert abs(log_data["contradiction_rate"] - 0.5) < 0.001
    
    def test_log_persistence(self):
        """Test that the log is updated correctly across multiple calls."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "contradiction_log.json"
            
            # Add three scenes: 2 valid, 1 invalid
            for i in range(3):
                constraint = PhysicsConstraint(f"scene_{i}")
                constraint.is_valid = (i != 2)  # Last one is invalid
                if not constraint.is_valid:
                    constraint.contradiction_reason = f"Error {i}"
                update_contradiction_log(constraint, str(log_path))
            
            with open(log_path, 'r') as f:
                log_data = json.load(f)
            
            assert log_data["total_scenes"] == 3
            assert log_data["contradiction_count"] == 1
            assert len(log_data["log_entries"]) == 3
            assert len(log_data["contradictions"]) == 1

class TestParseSceneDescription:
    """Tests for the parse_scene_description function."""
    
    def test_parse_on(self):
        """Test parsing 'A on B' pattern."""
        interactions = parse_scene_description("A on B")
        assert len(interactions) == 1
        assert interactions[0] == ("A", "on", "B")
    
    def test_parse_multiple(self):
        """Test parsing multiple interactions."""
        description = "A on B and C next to D"
        interactions = parse_scene_description(description)
        assert len(interactions) == 2
        assert ("A", "on", "B") in interactions
        assert ("C", "next_to", "D") in interactions
    
    def test_parse_case_insensitive(self):
        """Test that parsing is case insensitive."""
        interactions = parse_scene_description("a ON b")
        assert len(interactions) == 1
        assert interactions[0] == ("a", "on", "b")

class TestSimulatePhysics:
    """Tests for the simulate_physics function (basic structure checks)."""
    
    def test_simulate_empty_interactions(self):
        """Test simulation with no interactions."""
        constraint = simulate_physics("empty_scene", [])
        assert constraint.scene_id == "empty_scene"
        assert constraint.is_valid is True
        assert constraint.contradiction_reason is None
    
    def test_simulate_simple_on(self):
        """Test simulation with a simple 'on' interaction."""
        interactions = [("A", "on", "B")]
        constraint = simulate_physics("simple_on", interactions)
        assert constraint.scene_id == "simple_on"
        # The simulation might succeed or fail depending on physics, but it should run
        assert constraint.bounding_boxes is not None

class TestLoadSceneDescriptions:
    """Tests for the load_scene_descriptions function."""
    
    def test_load_valid_csv(self):
        """Test loading a valid CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "scenes.csv"
            with open(csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['scene_id', 'description'])
                writer.writerow(['scene_1', 'A on B'])
                writer.writerow(['scene_2', 'C next to D'])
            
            scenes = load_scene_descriptions(str(csv_path))
            assert len(scenes) == 2
            assert scenes[0]['scene_id'] == 'scene_1'
            assert scenes[1]['scene_id'] == 'scene_2'
    
    def test_load_missing_file(self):
        """Test that an error is raised for a missing file."""
        with pytest.raises(Exception):  # SceneDescriptionNotFoundError
            load_scene_descriptions("/nonexistent/path.csv")
    
    def test_load_invalid_csv(self):
        """Test that an error is raised for a malformed CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "scenes.csv"
            with open(csv_path, 'w') as f:
                f.write("wrong_header\nvalue\n")
            
            with pytest.raises(Exception):  # InvalidSceneDescriptionError
                load_scene_descriptions(str(csv_path))

if __name__ == '__main__':
    pytest.main([__file__, '-v'])