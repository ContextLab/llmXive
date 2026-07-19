"""
Symbolic Solver Module for llmXive
Implements convex optimization constraints for non-penetration and joint limits.
"""

import logging
import signal
import sys
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

import cvxpy as cp
import numpy as np
from scipy import sparse

# Configure logging
logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    """Custom timeout exception for solver operations."""
    pass


class TimeoutHandler:
    """Context manager for enforcing solver timeouts."""

    def __init__(self, seconds: int):
        self.seconds = seconds
        self.original_handler = None

    def _handle_timeout(self, signum, frame):
        raise TimeoutError(f"Solver operation timed out after {self.seconds} seconds")

    def __enter__(self):
        # Set the signal handler
        self.original_handler = signal.signal(signal.SIGALRM, self._handle_timeout)
        signal.alarm(self.seconds)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cancel the alarm and restore the original handler
        signal.alarm(0)
        if self.original_handler:
            signal.signal(signal.SIGALRM, self.original_handler)
        return False


class SymbolicSolver:
    """
    Symbolic Solver using cvxpy for defining constraint matrices.
    
    This class defines the problem structure for:
    1. Non-penetration constraints (linearized collision avoidance)
    2. Joint limits constraints (position and velocity bounds)
    
    NOTE: This class defines the problem structure ONLY. It is intended to be
    wrapped by T014a (differentiable layer) to enable gradient flow.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the symbolic solver.
        
        Args:
            config: Optional configuration dictionary. If None, uses defaults.
        """
        self.config = config or {}
        self.timeout = self.config.get('timeout', 300)  # Default 300s timeout
        self.log_path = self.config.get('log_path', 'data/results/solver_debug.log')
        
        # Setup solver-specific logging
        self.solver_logger = logging.getLogger('symbolic_solver')
        handler = logging.FileHandler(self.log_path)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.solver_logger.addHandler(handler)
        self.solver_logger.setLevel(logging.INFO)

    def _build_non_penetration_constraints(
        self, 
        position: cp.Variable, 
        velocity: cp.Variable,
        obstacle_params: Dict[str, np.ndarray]
    ) -> List[cp.Constraint]:
        """
        Build non-penetration constraints based on linearized collision geometry.
        
        Args:
            position: Position variable (n_dims,)
            velocity: Velocity variable (n_dims,)
            obstacle_params: Dictionary containing obstacle geometry data:
                - 'planes': (n_planes, n_dims + 1) coefficients for a*x + b*y + c*z + d <= 0
                - 'safety_margin': float safety buffer
        
        Returns:
            List of cvxpy Constraint objects
        """
        constraints = []
        
        if 'planes' not in obstacle_params:
            self.solver_logger.warning("No obstacle planes provided, skipping non-penetration")
            return constraints

        planes = obstacle_params['planes']
        safety_margin = obstacle_params.get('safety_margin', 0.01)
        
        # Linearized constraint: A * position + b <= 0
        # planes shape: (n_constraints, n_dims + 1)
        # Last column is the constant term 'b'
        
        A = planes[:, :-1]  # Coefficients for position
        b = planes[:, -1] + safety_margin  # Constant term + safety margin
        
        # Constraint: A @ position + b <= 0
        non_penetration = A @ position + b <= 0
        constraints.append(non_penetration)
        
        # Optional: Velocity damping near obstacles to prevent penetration
        if 'velocity_damping' in obstacle_params:
            damping_factor = obstacle_params['velocity_damping']
            # Limit velocity magnitude in direction of obstacle normal
            normals = A
            vel_constraint = cp.norm(cp.multiply(normals, velocity), 2) <= damping_factor
            constraints.append(vel_constraint)
        
        self.solver_logger.info(f"Added {len(A)} non-penetration constraints")
        return constraints

    def _build_joint_limit_constraints(
        self, 
        position: cp.Variable, 
        velocity: cp.Variable,
        joint_params: Dict[str, np.ndarray]
    ) -> List[cp.Constraint]:
        """
        Build joint limit constraints (position and velocity bounds).
        
        Args:
            position: Position variable (n_joints,)
            velocity: Velocity variable (n_joints,)
            joint_params: Dictionary containing joint limit data:
                - 'lower': (n_joints,) lower position bounds
                - 'upper': (n_joints,) upper position bounds
                - 'max_velocity': (n_joints,) maximum velocity magnitudes
        
        Returns:
            List of cvxpy Constraint objects
        """
        constraints = []
        
        if 'lower' not in joint_params or 'upper' not in joint_params:
            self.solver_logger.warning("Missing joint limits, skipping joint constraints")
            return constraints

        lower = joint_params['lower']
        upper = joint_params['upper']
        max_vel = joint_params.get('max_velocity', np.full_like(lower, np.inf))
        
        # Position bounds: lower <= position <= upper
        pos_constraints = [
            position >= lower,
            position <= upper
        ]
        constraints.extend(pos_constraints)
        
        # Velocity bounds: -max_vel <= velocity <= max_vel
        vel_constraints = [
            velocity >= -max_vel,
            velocity <= max_vel
        ]
        constraints.extend(vel_constraints)
        
        self.solver_logger.info(f"Added joint limits: {len(lower)} joints")
        return constraints

    def solve(
        self, 
        objective: cp.Expression, 
        variables: List[cp.Variable],
        additional_constraints: Optional[List[cp.Constraint]] = None,
        solver_name: str = 'ECOS',
        problem_params: Optional[Dict[str, Any]] = None
    ) -> Tuple[Optional[np.ndarray], Optional[float], bool]:
        """
        Solve the defined convex optimization problem.
        
        Args:
            objective: The objective function expression to minimize.
            variables: List of variables in the problem.
            additional_constraints: Optional list of extra constraints.
            solver_name: CVXPY solver name (ECOS, SCS, OSQP).
            problem_params: Additional parameters for the problem definition.
        
        Returns:
            Tuple of (solution_dict, optimal_value, success_flag)
            solution_dict: Dict mapping variable names to their solved values.
            optimal_value: The optimal objective value.
            success_flag: True if solver converged successfully.
        """
        constraints = []
        
        if additional_constraints:
            constraints.extend(additional_constraints)
        
        problem = cp.Problem(cp.Minimize(objective), constraints)
        
        start_time = time.time()
        success = False
        optimal_value = None
        solution_dict = None
        
        try:
            with TimeoutHandler(self.timeout):
                problem.solve(
                    solver=solver_name,
                    verbose=False,
                    **problem_params or {}
                )
            
            if problem.status in [cp.OPTIMAL, cp.OPTIMAL_INACCURATE]:
                success = True
                optimal_value = problem.value
                
                # Extract solution values
                solution_dict = {}
                for var in variables:
                    solution_dict[var.name] = var.value
                    
                elapsed = time.time() - start_time
                self.solver_logger.info(
                    f"Solved successfully in {elapsed:.3f}s. Status: {problem.status}, "
                    f"Value: {optimal_value}"
                )
            else:
                self.solver_logger.warning(f"Solver failed with status: {problem.status}")
                
        except TimeoutError as e:
            self.solver_logger.error(str(e))
            success = False
        except Exception as e:
            self.solver_logger.error(f"Solver exception: {type(e).__name__}: {str(e)}")
            success = False
        
        return solution_dict, optimal_value, success

    def create_problem_structure(
        self,
        latent_input: np.ndarray,
        geometry_data: Dict[str, Any]
    ) -> Tuple[cp.Variable, cp.Variable, cp.Expression, List[cp.Constraint]]:
        """
        Create the full problem structure (variables, objective, constraints).
        This is the primary entry point for T014a to wrap.
        
        Args:
            latent_input: Latent representation from GFM encoder (n_dims,)
            geometry_data: Dictionary containing:
                - 'obstacles': Obstacle parameters for non-penetration
                - 'joints': Joint parameters for limits
                - 'target': Target position for objective (optional)
        
        Returns:
            Tuple of (position_var, velocity_var, objective_expr, constraints_list)
        """
        n_dims = latent_input.shape[0]
        
        # Define variables
        position = cp.Variable(n_dims)
        velocity = cp.Variable(n_dims)
        
        # Build constraints
        constraints = []
        
        # 1. Non-penetration constraints
        if 'obstacles' in geometry_data:
            constraints.extend(
                self._build_non_penetration_constraints(
                    position, velocity, geometry_data['obstacles']
                )
            )
        
        # 2. Joint limit constraints
        if 'joints' in geometry_data:
            constraints.extend(
                self._build_joint_limit_constraints(
                    position, velocity, geometry_data['joints']
                )
            )
        
        # 3. Additional kinematic constraints (e.g., smoothness)
        # Minimize acceleration: ||velocity - prev_velocity||^2
        # For now, assume prev_velocity is zero or provided in geometry_data
        prev_vel = geometry_data.get('prev_velocity', np.zeros(n_dims))
        smoothness = cp.sum_squares(velocity - prev_vel)
        
        # Objective: Minimize distance to target + smoothness
        target = geometry_data.get('target', latent_input)
        tracking_error = cp.sum_squares(position - target)
        
        # Weighted objective
        alpha = geometry_data.get('tracking_weight', 1.0)
        beta = geometry_data.get('smoothness_weight', 0.1)
        
        objective = alpha * tracking_error + beta * smoothness
        
        return position, velocity, objective, constraints


def main():
    """
    Main entry point for testing the symbolic solver structure.
    This function demonstrates the problem definition but does not execute a full
    differentiable pass (that is the responsibility of T014a).
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting SymbolicSolver structure test...")
    
    # Initialize solver
    solver = SymbolicSolver({'timeout': 30})
    
    # Create dummy geometry data
    n_joints = 6
    geometry_data = {
        'obstacles': {
            'planes': np.random.randn(4, 4),  # 4 planes in 3D + constant
            'safety_margin': 0.05,
            'velocity_damping': 0.1
        },
        'joints': {
            'lower': np.full(n_joints, -1.0),
            'upper': np.full(n_joints, 1.0),
            'max_velocity': np.full(n_joints, 2.0)
        },
        'target': np.zeros(n_joints),
        'tracking_weight': 1.0,
        'smoothness_weight': 0.1
    }
    
    latent_input = np.random.randn(n_joints)
    
    # Create problem structure
    position, velocity, objective, constraints = solver.create_problem_structure(
        latent_input, geometry_data
    )
    
    logger.info(f"Created problem with {len(constraints)} constraints")
    logger.info(f"Variables: {position.name}, {velocity.name}")
    logger.info(f"Objective type: {type(objective)}")
    
    # Attempt to solve (without differentiability)
    solution, value, success = solver.solve(
        objective, 
        [position, velocity], 
        constraints
    )
    
    if success:
        logger.info(f"Solution found: position={solution[position.name][:3]}...")
    else:
        logger.warning("Solving failed (expected if no real data or constraints conflict)")
    
    logger.info("SymbolicSolver structure test completed.")


if __name__ == "__main__":
    main()