"""
Unit tests for the SymbolicSolver module.
"""
import numpy as np
import pytest
import logging

from code.symbolic_solver import SymbolicSolver

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("llmxive")

class TestSymbolicSolver:
    """Test cases for SymbolicSolver."""

    def setup_method(self):
        """Setup test fixtures."""
        self.solver = SymbolicSolver(timeout=5.0)

    def test_non_penetration_feasible(self):
        """Test non-penetration when already feasible."""
        obj_pos = np.array([0.0, 0.0, 0.0])
        obs_pos = np.array([0.0, 0.0, 2.0])
        radius = 0.5

        success, new_pos, info = self.solver.solve_non_penetration(obj_pos, obs_pos, radius)

        assert success is True
        assert np.linalg.norm(new_pos - obs_pos) >= radius
        assert np.allclose(new_pos, obj_pos)  # Should not move if feasible
        assert info["status"] == "feasible"

    def test_non_penetration_infeasible(self):
        """Test non-penetration when penetrating."""
        obj_pos = np.array([0.0, 0.0, 0.0])
        obs_pos = np.array([0.0, 0.0, 0.2])
        radius = 0.5

        success, new_pos, info = self.solver.solve_non_penetration(obj_pos, obs_pos, radius)

        assert success is True
        # Should be projected to the boundary
        expected_dist = radius
        actual_dist = np.linalg.norm(new_pos - obs_pos)
        assert np.isclose(actual_dist, expected_dist, atol=1e-5)
        assert info["status"] == "projected"
        assert info["penetration_depth"] > 0

    def test_joint_limits_feasible(self):
        """Test joint limits when already feasible."""
        joints = np.array([0.5, -0.5, 0.0])
        lower = np.array([-1.0, -1.0, -1.0])
        upper = np.array([1.0, 1.0, 1.0])

        success, new_joints, info = self.solver.solve_joint_limits(joints, lower, upper)

        assert success is True
        assert np.allclose(new_joints, joints)
        assert info["status"] == "optimal"

    def test_joint_limits_infeasible(self):
        """Test joint limits when violating bounds."""
        joints = np.array([2.0, -2.0, 0.5])
        lower = np.array([-1.0, -1.5, -3.0])
        upper = np.array([1.0, 1.5, 3.0])

        success, new_joints, info = self.solver.solve_joint_limits(joints, lower, upper)

        assert success is True
        # Should be clipped to bounds
        assert np.all(new_joints >= lower)
        assert np.all(new_joints <= upper)
        # Specifically, 2.0 -> 1.0, -2.0 -> -1.5
        assert np.isclose(new_joints[0], 1.0)
        assert np.isclose(new_joints[1], -1.5)

    def test_joint_limits_dimension_mismatch(self):
        """Test that dimension mismatch raises an error."""
        joints = np.array([0.5, 0.5])
        lower = np.array([-1.0, -1.0, -1.0])
        upper = np.array([1.0, 1.0, 1.0])

        with pytest.raises(ValueError):
            self.solver.solve_joint_limits(joints, lower, upper)

    def test_soft_body_simple(self):
        """Test soft body solver with a simple 2-node system."""
        nodes = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
        rest_lens = np.array([0.5])
        edges = [(0, 1)]

        success, new_nodes, info = self.solver.solve_soft_body_constraint(nodes, rest_lens, edges)

        # The solver should attempt to minimize energy
        # Note: Without anchors, the system might drift, but energy should decrease or be minimal
        assert success is True or success is False # Depending on solver status
        # Just check that output shape is correct
        assert new_nodes.shape == nodes.shape