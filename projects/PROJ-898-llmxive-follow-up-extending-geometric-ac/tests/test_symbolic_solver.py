"""
Unit tests for the SymbolicSolver module.
"""

import pytest
import numpy as np
import sys
import os

# Add code directory to path if running from tests/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from code.symbolic_solver import SymbolicSolver, ConstraintMatrix, TimeoutError, TimeoutHandler


class TestSymbolicSolver:
    """Test suite for SymbolicSolver."""

    def setup_method(self):
        """Setup test fixtures."""
        self.solver = SymbolicSolver()
        self.vertices = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [1.0, 1.0, 0.0]
        ])
        self.obstacles = [
            {"normal": [0, 0, 1], "offset": 0.1}
        ]
        self.joint_angles = np.array([0.1, 0.2])
        self.joint_limits = [(-1.57, 1.57), (-1.57, 1.57)]

    def test_build_non_penetration_constraints(self):
        """Test non-penetration constraint matrix generation."""
        A, b = self.solver._build_non_penetration_constraints(self.vertices, self.obstacles)

        assert A.shape[0] == 3  # 3 vertices, 1 constraint each
        assert A.shape[1] == 9  # 3 vertices * 3 dimensions
        assert b.shape[0] == 3
        assert np.allclose(b, [0.1, 0.1, 0.1])

    def test_build_joint_limit_constraints(self):
        """Test joint limit constraint matrix generation."""
        A, b = self.solver._build_joint_limit_constraints(self.joint_angles, self.joint_limits)

        assert A.shape[0] == 4  # 2 joints * 2 constraints (min, max)
        assert A.shape[1] == 2  # 2 joints
        assert b.shape[0] == 4
        # Check lower bounds
        assert np.isclose(b[0], 1.57) # -(-1.57)
        assert np.isclose(b[2], 1.57)
        # Check upper bounds
        assert np.isclose(b[1], 1.57)
        assert np.isclose(b[3], 1.57)

    def test_build_problem_structure(self):
        """Test full problem structure building."""
        cm = self.solver.build_problem_structure(
            topology_id="test_001",
            vertices=self.vertices,
            obstacles=self.obstacles,
            joint_angles=self.joint_angles,
            joint_limits=self.joint_limits
        )

        assert isinstance(cm, ConstraintMatrix)
        assert cm.topology_id == "test_001"
        assert cm.A.shape[1] == 3 * 3 + 2  # vertices + joints
        assert cm.metadata["n_vertices"] == 3
        assert cm.metadata["n_joints"] == 2

    def test_solve_with_timeout_optimal(self):
        """Test solving with a feasible problem."""
        cm = self.solver.build_problem_structure(
            topology_id="test_opt",
            vertices=self.vertices,
            obstacles=self.obstacles,
            joint_angles=self.joint_angles,
            joint_limits=self.joint_limits
        )
        # Create a dummy objective
        objective = np.zeros(cm.A.shape[1])
        solution, meta = self.solver.solve_with_timeout(cm, objective, timeout_seconds=10.0)

        # We expect a solution or at least a valid status
        assert meta["status"] in ["optimal", "optimal_inaccurate", "unknown_status_"]
        assert not meta["timeout"]

    def test_timeout_handler(self):
        """Test the TimeoutHandler context manager."""
        if sys.platform == 'win32':
            pytest.skip("TimeoutHandler uses SIGALRM which is not available on Windows")

        with pytest.raises(TimeoutError):
            with TimeoutHandler(0.1):
                time.sleep(0.5)

    def test_empty_obstacles(self):
        """Test building constraints with no obstacles."""
        cm = self.solver.build_problem_structure(
            topology_id="test_empty",
            vertices=self.vertices,
            obstacles=[],
            joint_angles=self.joint_angles,
            joint_limits=self.joint_limits
        )
        # Should still build joint constraints
        assert cm.A.shape[0] > 0 # At least joint limits

    def test_invalid_vertex_dimension(self):
        """Test error handling for invalid vertex dimensions."""
        with pytest.raises(ValueError):
            self.solver._build_non_penetration_constraints(
                np.array([[0, 0]]), # 2D
                self.obstacles
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
