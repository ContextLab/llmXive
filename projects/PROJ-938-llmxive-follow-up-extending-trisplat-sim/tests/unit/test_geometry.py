"""
Unit tests for code/models/geometry_only.py.
Specifically tests the max 100 iteration limit (FR-007).
"""
import unittest
from unittest.mock import patch, MagicMock
import torch
import numpy as np
import sys
import os

# Ensure project root is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from models.geometry_only import (
    DifferentiableRaySurfaceLayer,
    GeometryOnlyModel,
    run_geometry_optimization,
    generate_placeholder_mesh_from_failure
)
from utils.mesh_utils import create_placeholder_mesh


class TestGeometryOnlyIterationLimit(unittest.TestCase):
    """Tests for the 100-iteration hard limit in geometry_only.py"""

    def setUp(self):
        """Set up test fixtures."""
        self.device = torch.device("cpu")
        self.batch_size = 1
        self.height = 240
        self.width = 320
        
        # Mock data for testing
        self.mock_views = [
            {
                "image": torch.randn(3, self.height, self.width),
                "camera_pose": torch.eye(4),
                "intrinsics": torch.eye(3)
            }
            for _ in range(2)  # Minimum 2 views
        ]

    def test_max_iterations_enforced_in_run_geometry_optimization(self):
        """
        FR-007: Verify that run_geometry_optimization stops at exactly 100 iterations
        even if convergence is not reached.
        """
        # Create a model that never converges (loss stays high)
        model = GeometryOnlyModel(device=self.device)
        
        # We need to test the internal loop logic.
        # Since run_geometry_optimization is the entry point, we mock the
        # convergence check to always return False to force the limit.
        
        with patch.object(model, 'compute_loss', return_value=torch.tensor(100.0)):
            # Mock the optimizer step to be fast
            with patch.object(model, 'step', return_value=None):
                # Run optimization with a very low tolerance to ensure it doesn't converge early
                result = run_geometry_optimization(
                    views=self.mock_views,
                    model=model,
                    max_iterations=100,
                    tolerance=1e-9,  # Impossible tolerance
                    device=self.device
                )
                
                # Assert that the result indicates max iterations reached
                self.assertIn('converged', result)
                self.assertFalse(result['converged'], "Model should not have converged")
                
                # Assert that iterations count is exactly 100
                self.assertEqual(result['iterations'], 100, 
                               "Should have run exactly 100 iterations")

    def test_convergence_achieved_before_limit(self):
        """
        Verify that if convergence is achieved early, the loop stops immediately.
        """
        model = GeometryOnlyModel(device=self.device)
        
        # Mock a loss that drops below tolerance immediately
        with patch.object(model, 'compute_loss', side_effect=[torch.tensor(0.001)]):
            with patch.object(model, 'step', return_value=None):
                result = run_geometry_optimization(
                    views=self.mock_views,
                    model=model,
                    max_iterations=100,
                    tolerance=0.01,
                    device=self.device
                )
                
                self.assertTrue(result['converged'], "Model should have converged")
                self.assertLessEqual(result['iterations'], 100, 
                                   "Should not exceed max iterations")

    def test_generate_placeholder_mesh_on_timeout(self):
        """
        FR-007 & T043: Verify that generate_placeholder_mesh_from_failure
        creates a valid placeholder mesh when non-convergence occurs.
        """
        # Create a dummy failure result
        failure_result = {
            'converged': False,
            'iterations': 100,
            'reason': 'TIMEOUT_CONVERGENCE_FAILED',
            'points': None,
            'triangles': None
        }
        
        output_path = "tests/unit/output_placeholder.obj"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        mesh_path = generate_placeholder_mesh_from_failure(
            failure_result,
            output_path=output_path,
            device=self.device
        )
        
        # Verify file was created
        self.assertTrue(os.path.exists(mesh_path), "Placeholder mesh file should exist")
        
        # Verify it's a valid mesh file (non-empty)
        with open(mesh_path, 'r') as f:
            content = f.read()
            self.assertGreater(len(content), 0, "Mesh file should not be empty")
            self.assertIn('v ', content, "Mesh file should contain vertices")

    def test_differentiable_layer_forward_pass(self):
        """
        Verify the DifferentiableRaySurfaceLayer can perform a forward pass
        within the iteration limit context.
        """
        layer = DifferentiableRaySurfaceLayer(device=self.device)
        
        # Create dummy rays and surfaces
        rays_o = torch.randn(10, 3)
        rays_d = torch.randn(10, 3)
        surface_points = torch.randn(10, 3)
        normals = torch.randn(10, 3)
        
        # Forward pass should not raise errors
        try:
            intersections, depths = layer(rays_o, rays_d, surface_points, normals)
            self.assertEqual(intersections.shape[0], 10)
            self.assertEqual(depths.shape[0], 10)
        except Exception as e:
            self.fail(f"DifferentiableRaySurfaceLayer forward pass failed: {e}")


if __name__ == '__main__':
    unittest.main()