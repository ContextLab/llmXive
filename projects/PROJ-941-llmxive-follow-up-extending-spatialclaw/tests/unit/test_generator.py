"""
tests/unit/test_generator.py

Unit tests for the data generator module.
Verifies that tasks are generated correctly and constraints are met.
"""

import os
import json
import pytest
import sys
import math

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.data.generator import (
    generate_occlusion_task,
    generate_depth_task,
    generate_relative_task,
    calculate_2d_overlap_ratio,
    calculate_occlusion_in_3d,
    MIN_OVERLAP_RATIO,
    MIN_DEPTH_VARIANCE
)

class TestOcclusionTaskGeneration:
    def test_2d_overlap_constraint(self):
        """Ensure occlusion tasks have overlapping 2D bounding boxes."""
        task = generate_occlusion_task(seed=12345)
        obj_a, obj_b = task.ground_truth_3d_params.objects
        
        overlap = calculate_2d_overlap_ratio(obj_a, obj_b)
        assert overlap >= MIN_OVERLAP_RATIO, f"2D overlap {overlap} is below minimum {MIN_OVERLAP_RATIO}"

    def test_depth_variance_constraint(self):
        """Ensure occlusion tasks have sufficient depth difference."""
        task = generate_occlusion_task(seed=54321)
        depth_var = task.ground_truth_3d_params.depth_variance
        assert depth_var >= 0.5, f"Depth variance {depth_var} is below minimum 0.5"

    def test_schema_structure(self):
        """Verify the schema of the generated task."""
        task = generate_occlusion_task(seed=999)
        assert task.task_type == "occlusion"
        assert hasattr(task, 'task_id')
        assert hasattr(task, 'seed')
        assert len(task.ground_truth_3d_params.objects) == 2
        assert hasattr(task.ground_truth_3d_params, 'gt_3d_is_occluded')

class TestDepthTaskGeneration:
    def test_depth_variance_constraint(self):
        """Ensure depth tasks have sufficient depth difference."""
        task = generate_depth_task(seed=111)
        depth_var = task.ground_truth_3d_params.depth_variance
        assert depth_var >= MIN_DEPTH_VARIANCE, f"Depth variance {depth_var} is below minimum {MIN_DEPTH_VARIANCE}"

    def test_schema_structure(self):
        """Verify the schema of the generated task."""
        task = generate_depth_task(seed=222)
        assert task.task_type == "depth"
        assert len(task.ground_truth_3d_params.objects) == 2

class TestRelativeTaskGeneration:
    def test_schema_structure(self):
        """Verify the schema of the generated task."""
        task = generate_relative_task(seed=333)
        assert task.task_type == "relative"
        assert len(task.ground_truth_3d_params.objects) == 2

class TestGeometryCalculations:
    def test_2d_overlap_calculation(self):
        """Test 2D overlap ratio calculation."""
        # Create two identical objects at same position
        from code.data.generator import Object3D, Point3D
        
        obj1 = Object3D(id="1", type="cube", center=Point3D(0, 0, 0), size=2.0)
        obj2 = Object3D(id="2", type="cube", center=Point3D(0, 0, 1), size=2.0)
        
        overlap = calculate_2d_overlap_ratio(obj1, obj2)
        assert overlap == 1.0 # Fully overlapping

        # Create two non-overlapping objects
        obj3 = Object3D(id="3", type="cube", center=Point3D(10, 0, 0), size=2.0)
        overlap_no = calculate_2d_overlap_ratio(obj1, obj3)
        assert overlap_no == 0.0

    def test_3d_occlusion_logic(self):
        """Test 3D occlusion logic."""
        from code.data.generator import Object3D, Point3D
        
        # B is in front of A, and they overlap in 2D
        obj_a = Object3D(id="A", type="cube", center=Point3D(0, 0, 5), size=2.0)
        obj_b = Object3D(id="B", type="cube", center=Point3D(0, 0, 2), size=2.0)
        
        assert calculate_occlusion_in_3d(obj_a, obj_b) is True

        # B is behind A
        obj_c = Object3D(id="C", type="cube", center=Point3D(0, 0, 8), size=2.0)
        assert calculate_occlusion_in_3d(obj_a, obj_c) is False

        # No 2D overlap
        obj_d = Object3D(id="D", type="cube", center=Point3D(10, 10, 2), size=2.0)
        assert calculate_occlusion_in_3d(obj_a, obj_d) is False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])