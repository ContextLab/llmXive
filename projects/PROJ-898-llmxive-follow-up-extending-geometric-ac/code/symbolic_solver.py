"""
Symbolic Solver Module for Geometric Action Model.

Implements a differentiable constraint satisfaction solver using CVXPY/diffcp
for enforcing geometric constraints in 3D space (rigid/soft body).
Includes timeout handling and infeasibility detection.
"""

import logging
import signal
import sys
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

import cvxpy as cp
import numpy as np

from utils import setup_logging

logger = setup_logging(__name__)


class TimeoutError(Exception):
    """Custom exception for solver timeout."""
    pass


class TimeoutHandler:
    """Context manager for enforcing solver timeouts."""

    def __init__(self, timeout_seconds: float):
        self.timeout_seconds = timeout_seconds
        self.timer = None

    def _timeout_handler(self, signum, frame):
        raise TimeoutError(f"Solver timed out after {self.timeout_seconds} seconds")

    def __enter__(self):
        # Use signal only on Unix-like systems
        if hasattr(signal, 'SIGALRM'):
            self.old_handler = signal.signal(signal.SIGALRM, self._timeout_handler)
            signal.alarm(int(self.timeout_seconds) + 1)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)
            signal.signal(signal.SIGALRM, self.old_handler)
        return False


class SymbolicSolver:
    """
    Differentiable symbolic solver for geometric constraints.

    Uses CVXPY with diffcp to solve optimization problems subject to
    physical constraints (non-penetration, joint limits, etc.).
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the solver with configuration.

        Args:
            config: Solver configuration dictionary. Expected keys:
                    - 'timeout_seconds': Maximum time allowed per solve
                    - 'joint_limits': Dict of joint constraints
                    - 'penetration_threshold': Minimum distance allowed between bodies
        """
        self.config = config or {}
        self.timeout_seconds = self.config.get('timeout_seconds', 30.0)
        self.joint_limits = self.config.get('joint_limits', {})
        self.penetration_threshold = self.config.get('penetration_threshold', 0.01)

        logger.info(f"SymbolicSolver initialized with timeout={self.timeout_seconds}s")

    def _build_problem(self, latent_state: np.ndarray, target_pose: np.ndarray,
                     constraints_config: Dict[str, Any]) -> Tuple[cp.Variable, cp.Problem, Dict[str, Any]]:
        """
        Build the CVXPY optimization problem.

        Args:
            latent_state: Encoded latent representation of current state
            target_pose: Desired target pose in 3D space
            constraints_config: Additional constraint parameters

        Returns:
            Tuple of (decision variable, problem object, metadata dict)
        """
        # Decision variable: action vector in 3D space
        n_dims = 6  # 3D position + 3D rotation
        action = cp.Variable(n_dims)

        # Objective: minimize distance to target while respecting constraints
        position_error = cp.sum_squares(action[:3] - target_pose[:3])
        rotation_error = cp.sum_squares(action[3:] - target_pose[3:])

        # Weighted objective
        objective = cp.Minimize(0.5 * position_error + 0.5 * rotation_error)

        constraints = []

        # Joint limits constraint
        if self.joint_limits:
            for i, (min_val, max_val) in enumerate(self.joint_limits.items()):
                if i < n_dims:
                    constraints.append(action[i] >= min_val)
                    constraints.append(action[i] <= max_val)

        # Non-penetration constraint (simplified distance constraint)
        if 'obstacles' in constraints_config:
            for obstacle in constraints_config['obstacles']:
                obstacle_pos = np.array(obstacle['position'])
                min_dist = obstacle.get('min_distance', self.penetration_threshold)
                # Simple distance constraint: ||action - obstacle|| >= min_dist
                dist_sq = cp.sum_squares(action[:3] - obstacle_pos)
                constraints.append(dist_sq >= min_dist ** 2)

        # Soft body deformation constraints (if applicable)
        if constraints_config.get('soft_body', False):
            # Add elasticity constraints
            deformation_energy = cp.sum_squares(action)
            constraints.append(deformation_energy <= constraints_config.get('max_deformation', 1.0))

        problem = cp.Problem(objective, constraints)

        metadata = {
            'n_vars': n_dims,
            'n_constraints': len(constraints),
            'has_soft_body': constraints_config.get('soft_body', False)
        }

        return action, problem, metadata

    def solve(self, latent_state: np.ndarray, target_pose: np.ndarray,
             constraints_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Solve the constrained optimization problem.

        Args:
            latent_state: Encoded latent representation
            target_pose: Target 3D pose
            constraints_config: Optional additional constraints

        Returns:
            Dictionary containing:
              - 'action': Optimized action vector (np.ndarray) or None
              - 'success': Boolean indicating if a valid solution was found
              - 'infeasible': Boolean indicating if constraints were unsatisfiable
              - 'status': Solver status string
              - 'value': Objective value if successful
              - 'metadata': Additional solving metadata
        """
        if constraints_config is None:
            constraints_config = {}

        logger.debug(f"Solving for latent_state shape {latent_state.shape}, "
                    f"target_pose {target_pose}")

        action_var, problem, metadata = self._build_problem(
            latent_state, target_pose, constraints_config
        )

        result = {
            'action': None,
            'success': False,
            'infeasible': False,
            'status': 'unknown',
            'value': None,
            'metadata': metadata,
            'solve_time': None
        }

        try:
            with TimeoutHandler(self.timeout_seconds):
                start_time = time.time()
                problem.solve(solver=cp.ECOS, verbose=False)
                solve_time = time.time() - start_time
                result['solve_time'] = solve_time

            result['status'] = problem.status

            # Check for infeasibility
            if problem.status in [cp.INFEASIBLE, cp.INFEASIBLE_INACCURATE]:
                logger.warning(f"Constraints infeasible for target {target_pose}")
                result['infeasible'] = True
                result['success'] = False
                return result

            # Check for unbounded or numerical issues
            if problem.status in [cp.UNBOUNDED, cp.UNBOUNDED_INACCURATE, cp.NUMERICAL]:
                logger.warning(f"Solve failed with status {problem.status}")
                result['success'] = False
                return result

            # Successful solve
            if problem.status in [cp.OPTIMAL, cp.OPTIMAL_INACCURATE]:
                result['action'] = action_var.value
                result['success'] = True
                result['value'] = problem.value
                logger.debug(f"Solver succeeded in {solve_time:.3f}s, "
                           f"action={result['action']}")
            else:
                logger.warning(f"Unexpected solver status: {problem.status}")
                result['success'] = False

        except TimeoutError as e:
            logger.error(f"Solver timeout: {e}")
            result['status'] = 'timeout'
            result['success'] = False
            result['infeasible'] = False  # Timeout is not infeasibility

        except Exception as e:
            logger.error(f"Solver error: {e}", exc_info=True)
            result['status'] = f'error: {str(e)}'
            result['success'] = False

        return result

    def verify_constraints(self, action: np.ndarray, constraints_config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Verify that a given action satisfies all constraints.

        Args:
            action: Action vector to verify
            constraints_config: Constraint configuration

        Returns:
            Tuple of (is_valid, list_of_violated_constraints)
        """
        violations = []

        # Check joint limits
        if self.joint_limits:
            for i, (min_val, max_val) in enumerate(self.joint_limits.items()):
                if i < len(action):
                    if action[i] < min_val:
                        violations.append(f"joint_{i}_min")
                    if action[i] > max_val:
                        violations.append(f"joint_{i}_max")

        # Check non-penetration
        if 'obstacles' in constraints_config:
            for idx, obstacle in enumerate(constraints_config['obstacles']):
                obstacle_pos = np.array(obstacle['position'])
                min_dist = obstacle.get('min_distance', self.penetration_threshold)
                actual_dist = np.linalg.norm(action[:3] - obstacle_pos)
                if actual_dist < min_dist:
                    violations.append(f"obstacle_{idx}_penetration")

        return len(violations) == 0, violations


def main():
    """
    Main entry point for standalone testing of the symbolic solver.
    """
    logger.info("Starting SymbolicSolver standalone test")

    # Create solver instance
    config = {
        'timeout_seconds': 5.0,
        'joint_limits': {
            0: (-1.0, 1.0),
            1: (-1.0, 1.0),
            2: (-1.0, 1.0)
        },
        'penetration_threshold': 0.05
    }
    solver = SymbolicSolver(config)

    # Test case 1: Feasible problem
    logger.info("Test 1: Feasible problem")
    latent = np.random.randn(32)
    target = np.array([0.5, 0.5, 0.5, 0.0, 0.0, 0.0])
    constraints = {'soft_body': False}

    result = solver.solve(latent, target, constraints)
    logger.info(f"Result: success={result['success']}, "
               f"infeasible={result['infeasible']}, "
               f"status={result['status']}")

    # Test case 2: Infeasible problem (tight constraints)
    logger.info("Test 2: Infeasible problem")
    tight_config = {
        'timeout_seconds': 5.0,
        'joint_limits': {
            0: (0.1, 0.2),  # Very narrow range
            1: (0.1, 0.2),
            2: (0.1, 0.2)
        },
        'penetration_threshold': 0.05
    }
    tight_solver = SymbolicSolver(tight_config)
    result2 = tight_solver.solve(latent, target, constraints)
    logger.info(f"Result: success={result2['success']}, "
               f"infeasible={result2['infeasible']}, "
               f"status={result2['status']}")

    # Test case 3: Timeout
    logger.info("Test 3: Timeout simulation")
    slow_config = {'timeout_seconds': 0.001}
    slow_solver = SymbolicSolver(slow_config)
    result3 = slow_solver.solve(latent, target, constraints)
    logger.info(f"Result: success={result3['success']}, "
               f"status={result3['status']}")

    logger.info("Standalone test completed")


if __name__ == '__main__':
    main()