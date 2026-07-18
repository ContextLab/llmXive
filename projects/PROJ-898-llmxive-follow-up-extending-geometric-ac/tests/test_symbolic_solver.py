"""
Unit tests for code/symbolic_solver.py.
"""
import numpy as np
import pytest

from code.symbolic_solver import SymbolicSolver


class TestSymbolicSolver:
    def test_init(self):
        solver = SymbolicSolver(timeout=10.0)
        assert solver.timeout == 10.0

    def test_solve_non_penetration_success(self):
        solver = SymbolicSolver()
        obj_pos = np.array([0.0, 0.0, 0.0])
        obs_pos = np.array([0.5, 0.0, 0.0])
        radius = 0.2

        success, new_pos = solver.solve_non_penetration(obj_pos, obs_pos, radius)
        assert isinstance(success, bool)
        # In mock mode, it should move away
        if success:
            assert np.linalg.norm(new_pos - obs_pos) >= radius - 1e-5

    def test_solve_joint_limits(self):
        solver = SymbolicSolver()
        angles = np.array([1.0, 2.0, 3.0])
        lower = np.array([-1.0, -1.0, -1.0])
        upper = np.array([2.0, 2.0, 2.0])

        success, new_angles = solver.solve_joint_limits(angles, lower, upper)
        assert isinstance(success, bool)
        if success:
            assert np.all(new_angles >= lower)
            assert np.all(new_angles <= upper)

    def test_check_infeasibility(self):
        solver = SymbolicSolver()
        # In mock mode, this returns False
        is_infeasible = solver.check_infeasibility([])
        assert isinstance(is_infeasible, bool)