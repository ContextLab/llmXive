"""
tests/unit/test_generator.py

Unit tests for code/data/generator.py
Verifies schema compliance and file generation.
"""
import json
import os
import pytest
import tempfile
import shutil
from code.data.generator import (
    generate_dataset,
    generate_scene_id,
    generate_object_id,
    generate_point3d,
    generate_object,
    calculate_depth_diff,
    calculate_occlusion_ratio,
    generate_occlusion_task,
    generate_depth_task,
    generate_relative_task,
    TaskInstance,
    Point3D,
    Object3D,
    GroundTruth3DParams
)
from dataclasses import asdict

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_generate_scene_id():
    """Test that scene_id generation returns a unique string."""
    id1 = generate_scene_id()
    id2 = generate_scene_id()
    assert isinstance(id1, str)
    assert len(id1) == 8
    assert len(id2) == 8
    # While collision is possible, it's extremely unlikely for UUID-based IDs

def test_generate_object_id():
    """Test that object_id generation returns a unique string."""
    id1 = generate_object_id()
    id2 = generate_object_id()
    assert isinstance(id1, str)
    assert len(id1) == 8

def test_generate_point3d():
    """Test Point3D generation within default ranges."""
    point = generate_point3d()
    assert isinstance(point, Point3D)
    assert -10 <= point.x <= 10
    assert -10 <= point.y <= 10
    assert 0 <= point.z <= 10

def test_generate_object():
    """Test Object3D generation."""
    obj = generate_object()
    assert isinstance(obj, Object3D)
    assert isinstance(obj.center, Point3D)
    assert "width" in obj.dimensions
    assert "height" in obj.dimensions
    assert "depth" in obj.dimensions
    assert "roll" in obj.rotation
    assert "pitch" in obj.rotation
    assert "yaw" in obj.rotation

def test_calculate_depth_diff():
    """Test depth difference calculation."""
    obj_a = generate_object()
    obj_b = generate_object()
    # Manually set Z to ensure a known difference
    obj_a.center.z = 1.0
    obj_b.center.z = 3.0
    diff = calculate_depth_diff(obj_a, obj_b)
    assert diff == 2.0

def test_calculate_occlusion_ratio():
    """Test occlusion ratio calculation (returns float 0-1)."""
    obj_a = generate_object()
    obj_b = generate_object()
    ratio = calculate_occlusion_ratio(obj_a, obj_b)
    assert 0.0 <= ratio <= 1.0

def test_generate_occlusion_task_schema():
    """Test occlusion task schema compliance."""
    scene_id = generate_scene_id()
    task = generate_occlusion_task(scene_id)
    assert isinstance(task, TaskInstance)
    assert task.task_type == "occlusion"
    assert task.scene_id == scene_id
    assert "task_id" in task.task_id
    assert "ground_truth_3d_params" in task.__dict__
    gt = task.ground_truth_3d_params
    assert "occlusion_ratio" in gt
    assert "depth_variance" in gt
    assert "relative_position" in gt
    assert "scene_complexity" in gt

def test_generate_depth_task_schema():
    """Test depth task schema compliance."""
    scene_id = generate_scene_id()
    task = generate_depth_task(scene_id)
    assert task.task_type == "depth"
    gt = task.ground_truth_3d_params
    assert "depth_variance" in gt
    assert gt["depth_variance"] > 0.5 # Should be forced by generator logic

def test_generate_relative_task_schema():
    """Test relative task schema compliance."""
    scene_id = generate_scene_id()
    task = generate_relative_task(scene_id)
    assert task.task_type == "relative"
    gt = task.ground_truth_3d_params
    assert "relative_position" in gt
    assert "dx" in gt["relative_position"]
    assert "dy" in gt["relative_position"]
    assert "dz" in gt["relative_position"]

def test_generate_dataset_creates_file(temp_output_dir):
    """Test that generate_dataset creates the output JSON file."""
    output_path = os.path.join(temp_output_dir, "test_spatialclaw.json")
    tasks = generate_dataset(n_tasks=10, seed=42, output_path=output_path)
    
    assert os.path.exists(output_path)
    assert len(tasks) == 10
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert isinstance(data, list)
    assert len(data) == 10
    
    # Verify schema of first item
    item = data[0]
    assert "task_id" in item
    assert "scene_id" in item
    assert "task_type" in item
    assert "ground_truth_3d_params" in item
    assert item["task_type"] in ["occlusion", "depth", "relative"]

def test_generate_dataset_schema_compliance(temp_output_dir):
    """Test full schema compliance of generated dataset."""
    output_path = os.path.join(temp_output_dir, "test_spatialclaw.json")
    generate_dataset(n_tasks=20, seed=42, output_path=output_path)
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    for item in data:
        # Check required top-level fields
        assert "task_id" in item
        assert "scene_id" in item
        assert "task_type" in item
        assert "ground_truth_3d_params" in item
        
        gt = item["ground_truth_3d_params"]
        assert "occlusion_ratio" in gt
        assert "depth_variance" in gt
        assert "relative_position" in gt
        assert "scene_complexity" in gt
        
        # Check relative_position structure
        rel_pos = gt["relative_position"]
        assert "dx" in rel_pos
        assert "dy" in rel_pos
        assert "dz" in rel_pos
