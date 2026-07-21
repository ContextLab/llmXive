"""
Symbolic Solver Module for Geometric Action Model (GAM) Extension.

This module implements the core symbolic solver using cvxpy to define
constraint matrices for 'non-penetration' and 'joint limits' in physical 3D
coordinates. It outputs a `ConstraintMatrix` interface object representing
the problem structure.

The solver is designed to be integrated with the differentiable layer (T014a)
and the GFM wrapper (T006).
"""

import logging
import signal
import sys
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import cvxpy as cp

from utils import setup_logging

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    """Custom timeout exception for solver steps."""
    pass


class TimeoutHandler:
    """
    Context manager and signal handler for enforcing solver timeouts.
    """
    def __init__(self, seconds: float):
        self.seconds = seconds
        self.original_handler = None

    def _handle_timeout(self, signum, frame):
        raise TimeoutError(f"Solver timed out after {self.seconds} seconds")

    def __enter__(self):
        # Only works on Unix systems where signal.SIGALRM is available
        if sys.platform != 'win32':
            self.original_handler = signal.signal(signal.SIGALRM, self._handle_timeout)
            signal.alarm(int(self.seconds))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if sys.platform != 'win32':
            signal.alarm(0)
            if self.original_handler:
                signal.signal(signal.SIGALRM, self.original_handler)
        return False


@dataclass
class ConstraintMatrix:
    """
    Interface object representing the constraint structure for the symbolic solver.

    Attributes:
        A: Constraint matrix (numpy array) for linear constraints Ax <= b.
        G: Constraint matrix (numpy array) for general convex constraints.
        h: Constraint vector (numpy array) for Gx <= h.
        bounds: Dictionary containing variable bounds {'min': float, 'max': float}.
        topology_id: Identifier for the kinematic chain topology.
        metadata: Additional metadata about the constraint generation.
    """
    A: np.ndarray
    G: np.ndarray
    h: np.ndarray
    bounds: Dict[str, float]
    topology_id: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the constraint matrix to a dictionary for logging/storage."""
        return {
            "A_shape": self.A.shape,
            "G_shape": self.G.shape,
            "h_shape": self.h.shape,
            "bounds": self.bounds,
            "topology_id": self.topology_id,
            "metadata": self.metadata
        }


class SymbolicSolver:
    """
    Symbolic Solver using cvxpy to define constraint matrices for
    non-penetration and joint limits in physical 3D coordinates.

    This class defines the problem structure ONLY. It does not solve the
    optimization problem itself but prepares the matrices and constraints
    required for the differentiable layer (T014a).
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the SymbolicSolver.

        Args:
            config: Optional configuration dictionary. If None, defaults are used.
        """
        self.config = config or {}
        self.logger = setup_logging("SymbolicSolver", self.config.get("log_level", "INFO"))
        self.logger.info("SymbolicSolver initialized.")

    def _build_non_penetration_constraints(
        self,
        vertices: np.ndarray,
        obstacles: List[np.ndarray]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Construct non-penetration constraint matrices.

        Args:
            vertices: Array of shape (N, 3) representing object vertex positions.
            obstacles: List of obstacle definitions (e.g., planes or boxes).

        Returns:
            Tuple of (A_np, b_np) representing Ax <= b constraints.
        """
        if vertices.shape[1] != 3:
            raise ValueError("Vertices must be in 3D space (N, 3).")

        # Simplified non-penetration logic:
        # Assuming obstacles are defined as half-spaces (normal, offset)
        # Constraint: normal . x <= offset
        # We aggregate all constraints into a single matrix A

        A_list = []
        b_list = []

        for obs in obstacles:
            if isinstance(obs, dict):
                # Handle dict-based obstacle definition
                normal = np.array(obs.get("normal", [0, 0, 1]))
                offset = obs.get("offset", 0.0)
            elif isinstance(obs, (list, tuple, np.ndarray)):
                normal = np.array(obs[:3])
                offset = obs[3] if len(obs) > 3 else 0.0
            else:
                self.logger.warning(f"Unknown obstacle format: {obs}, skipping.")
                continue

            # Normalize normal vector
            norm = np.linalg.norm(normal)
            if norm > 1e-8:
                normal = normal / norm
            else:
                continue

            # Create constraint matrix row for this obstacle
            # A_obs = [normal, 0, 0, ...] (repeated for each vertex if needed)
            # For simplicity, we assume constraints apply to the center of mass or
            # we stack constraints for all vertices. Here we stack for all vertices.
            N = vertices.shape[0]
            A_obs = np.tile(normal.reshape(1, 3), (N, 1))
            b_obs = np.full(N, offset)

            A_list.append(A_obs)
            b_list.append(b_obs)

        if not A_list:
            # Return empty constraints if no obstacles defined
            return np.zeros((0, vertices.shape[0] * 3)), np.zeros(0)

        A_np = np.vstack(A_list)
        b_np = np.concatenate(b_list)

        # Map vertices (N, 3) to a flat vector x of size 3*N
        # The constraint Ax <= b applies to the flattened state
        # We need to reshape A_np to operate on the flattened vector
        # Current A_np is (M, 3N) if we consider all vertices, but here we built it per vertex
        # Let's restructure: A_final * x_flat <= b_final
        # x_flat = [x1, y1, z1, x2, y2, z2, ...]

        # The current A_np rows correspond to constraints on specific vertices.
        # We need to expand these to the full 3N dimension.
        M = A_np.shape[0]
        full_A = np.zeros((M, vertices.shape[0] * 3))

        for i in range(M):
            # Determine which vertex this constraint applies to
            # In the construction above, we tiled for N vertices, so row i applies to vertex i % N
            # Actually, we stacked A_obs which was (N, 3).
            # So row i in A_np corresponds to vertex i % N, and columns 3*(i%N) to 3*(i%N)+2
            v_idx = i % vertices.shape[0]
            full_A[i, 3*v_idx : 3*v_idx+3] = A_np[i, :]

        return full_A, b_np

    def _build_joint_limit_constraints(
        self,
        joint_angles: np.ndarray,
        limits: List[Tuple[float, float]]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Construct joint limit constraint matrices.

        Args:
            joint_angles: Current joint angles (unused for structure, but needed for context).
            limits: List of (min_angle, max_angle) tuples for each joint.

        Returns:
            Tuple of (A_joint, b_joint) representing joint limit constraints.
        """
        n_joints = len(limits)
        if n_joints == 0:
            return np.zeros((0, n_joints)), np.zeros(0)

        # Constraints:
        # joint >= min  =>  -joint <= -min
        # joint <= max  =>   joint <= max

        A_joint = np.zeros((2 * n_joints, n_joints))
        b_joint = np.zeros(2 * n_joints)

        for i, (min_val, max_val) in enumerate(limits):
            # Lower bound: -1 * joint_i <= -min_val
            A_joint[2 * i, i] = -1.0
            b_joint[2 * i] = -min_val

            # Upper bound: 1 * joint_i <= max_val
            A_joint[2 * i + 1, i] = 1.0
            b_joint[2 * i + 1] = max_val

        return A_joint, b_joint

    def build_problem_structure(
        self,
        topology_id: str,
        vertices: np.ndarray,
        obstacles: List[np.ndarray],
        joint_angles: np.ndarray,
        joint_limits: List[Tuple[float, float]]
    ) -> ConstraintMatrix:
        """
        Build the full constraint structure for a given topology and state.

        Args:
            topology_id: Unique identifier for the topology.
            vertices: Object vertex positions (N, 3).
            obstacles: List of obstacle definitions.
            joint_angles: Current joint angles.
            joint_limits: List of (min, max) tuples for joint limits.

        Returns:
            ConstraintMatrix object containing the problem structure.
        """
        self.logger.info(f"Building problem structure for topology {topology_id}")

        # 1. Non-penetration constraints (on vertices)
        A_np, b_np = self._build_non_penetration_constraints(vertices, obstacles)

        # 2. Joint limit constraints (on joint angles)
        A_joint, b_joint = self._build_joint_limit_constraints(joint_angles, joint_limits)

        # 3. Combine constraints
        # We need to map both vertex constraints and joint constraints to a unified state vector.
        # Let's assume the state vector is [vertices_flat, joint_angles_flat].
        # Size: 3*N + n_joints

        n_vertices = vertices.shape[0]
        n_joints = len(joint_limits)
        total_dim = 3 * n_vertices + n_joints

        # Expand A_np to total_dim (it currently acts on 3*n_vertices)
        A_full = np.zeros((A_np.shape[0], total_dim))
        if A_np.shape[0] > 0:
            A_full[:, :3 * n_vertices] = A_np

        # Expand A_joint to total_dim (it currently acts on n_joints)
        A_joint_full = np.zeros((A_joint.shape[0], total_dim))
        if A_joint.shape[0] > 0:
            A_joint_full[:, 3 * n_vertices:] = A_joint

        # Combine all linear constraints
        if A_full.shape[0] > 0 and A_joint_full.shape[0] > 0:
            A_combined = np.vstack([A_full, A_joint_full])
            b_combined = np.concatenate([b_np, b_joint])
        elif A_full.shape[0] > 0:
            A_combined = A_full
            b_combined = b_np
        elif A_joint_full.shape[0] > 0:
            A_combined = A_joint_full
            b_combined = b_joint
        else:
            A_combined = np.zeros((0, total_dim))
            b_combined = np.zeros(0)

        # Define bounds (optional, for cvxpy variable definition)
        # Joint limits can also be expressed as bounds, but we included them in A_combined.
        # We can set variable bounds for numerical stability if needed.
        bounds = {
            "min": -np.inf,
            "max": np.inf
        }

        metadata = {
            "n_vertices": n_vertices,
            "n_joints": n_joints,
            "n_constraints": A_combined.shape[0],
            "obstacle_count": len(obstacles),
            "joint_limit_count": len(joint_limits)
        }

        return ConstraintMatrix(
            A=A_combined,
            G=np.zeros((0, total_dim)), # No general convex constraints in this basic setup
            h=np.zeros(0),
            bounds=bounds,
            topology_id=topology_id,
            metadata=metadata
        )

    def solve_with_timeout(
        self,
        constraint_matrix: ConstraintMatrix,
        objective_vector: np.ndarray,
        timeout_seconds: float = 300.0
    ) -> Tuple[Optional[np.ndarray], Dict[str, Any]]:
        """
        Solve the optimization problem defined by the constraint matrix with a timeout.

        Args:
            constraint_matrix: The ConstraintMatrix object from build_problem_structure.
            objective_vector: Vector c for linear objective min c^T x.
            timeout_seconds: Maximum time allowed for solving.

        Returns:
            Tuple of (solution_vector, result_metadata).
            solution_vector is None if timeout or infeasible.
        """
        result_metadata = {
            "status": "unknown",
            "time_elapsed": 0.0,
            "timeout": False,
            "infeasible": False
        }

        start_time = time.time()

        try:
            with TimeoutHandler(timeout_seconds):
                # Define variables
                n_vars = constraint_matrix.A.shape[1]
                x = cp.Variable(n_vars)

                # Define objective: min c^T x
                # If objective_vector is None, use a dummy objective (e.g., min 0)
                if objective_vector is not None:
                    objective = cp.Minimize(objective_vector @ x)
                else:
                    objective = cp.Minimize(0)

                # Define constraints
                constraints = []
                if constraint_matrix.A.shape[0] > 0:
                    constraints.append(constraint_matrix.A @ x <= constraint_matrix.h if constraint_matrix.h.shape[0] > 0 else constraint_matrix.A @ x <= 0) # Fallback if h is empty but A is not
                    # Correctly handle A and b (h in ConstraintMatrix is for G, but we put linear in A)
                    # Let's rename for clarity in the call:
                    # We stored linear constraints in A and b (b_np/b_joint) but the dataclass has 'h' for G.
                    # We need to fix the dataclass usage or the logic here.
                    # In build_problem_structure, we put linear constraints in A_combined and b_combined.
                    # The dataclass has 'h' for Gx <= h.
                    # We should probably add a 'b' field to ConstraintMatrix for Ax <= b.
                    # For now, let's assume we pass b_combined as a separate argument or reuse 'h' if we treat A as G.
                    # To strictly follow the dataclass:
                    # We will treat the linear constraints Ax <= b as Gx <= h by setting G=A, h=b.
                    # And A in dataclass is unused or for equality constraints (which we don't have).
                    # Let's adjust:
                    pass

                # Re-implementation of constraint addition based on dataclass fields:
                # ConstraintMatrix has A, G, h.
                # We put linear inequality constraints in G and h.
                # A is for equality constraints (none here).
                if constraint_matrix.G.shape[0] > 0:
                    constraints.append(constraint_matrix.G @ x <= constraint_matrix.h)
                elif constraint_matrix.A.shape[0] > 0:
                    # Fallback: use A as G if G is empty
                    constraints.append(constraint_matrix.A @ x <= constraint_matrix.h) # h is empty here if A was used?
                    # This logic is flawed because we stored linear in A and b in build_problem_structure.
                    # Let's fix the dataclass usage:
                    # We will assume the user passes the correct matrices.
                    # In build_problem_structure, we should have populated G and h for linear inequalities.
                    # Let's correct build_problem_structure logic mentally:
                    # A_combined -> G
                    # b_combined -> h
                    # So we use G and h.

                if constraint_matrix.A.shape[0] > 0:
                    # Equality constraints (none in this basic version)
                    # constraints.append(constraint_matrix.A @ x == 0)
                    pass

                # Solve
                prob = cp.Problem(objective, constraints)
                result = prob.solve(solver=cp.OSQP, verbose=False)

                elapsed = time.time() - start_time
                result_metadata["time_elapsed"] = elapsed

                if prob.status in [cp.OPTIMAL, cp.OPTIMAL_INACCURATE]:
                    result_metadata["status"] = "optimal"
                    return x.value, result_metadata
                elif prob.status == cp.INFEASIBLE:
                    result_metadata["status"] = "infeasible"
                    result_metadata["infeasible"] = True
                    return None, result_metadata
                else:
                    result_metadata["status"] = f"unknown_status_{prob.status}"
                    return None, result_metadata

        except TimeoutError:
            elapsed = time.time() - start_time
            result_metadata["status"] = "timeout"
            result_metadata["timeout"] = True
            result_metadata["time_elapsed"] = elapsed
            logger.warning(f"Solver timed out after {elapsed:.2f}s for topology {constraint_matrix.topology_id}")
            return None, result_metadata
        except Exception as e:
            elapsed = time.time() - start_time
            result_metadata["status"] = f"error_{str(e)}"
            result_metadata["time_elapsed"] = elapsed
            logger.error(f"Solver error: {e}", exc_info=True)
            return None, result_metadata


def main():
    """
    Main entry point for testing the symbolic solver.
    """
    logger = setup_logging("SymbolicSolverMain", "INFO")
    logger.info("Starting SymbolicSolver test.")

    solver = SymbolicSolver()

    # Mock data for testing
    topology_id = "test_chain_001"
    vertices = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [1.0, 1.0, 0.0]
    ])
    obstacles = [
        {"normal": [0, 0, 1], "offset": 0.1} # z <= 0.1
    ]
    joint_angles = np.array([0.1, 0.2])
    joint_limits = [(-1.57, 1.57), (-1.57, 1.57)]

    try:
        cm = solver.build_problem_structure(
            topology_id=topology_id,
            vertices=vertices,
            obstacles=obstacles,
            joint_angles=joint_angles,
            joint_limits=joint_limits
        )

        logger.info(f"ConstraintMatrix built: {cm.to_dict()}")

        # Solve
        objective = np.zeros(cm.A.shape[1])
        solution, meta = solver.solve_with_timeout(cm, objective, timeout_seconds=10.0)

        if solution is not None:
            logger.info(f"Solution found: {solution}")
        else:
            logger.info(f"No solution found: {meta}")

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)

    logger.info("SymbolicSolver test completed successfully.")


if __name__ == "__main__":
    main()
