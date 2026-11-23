"""
Symbolic Solver Module for Geometric Action Model.

Implements constraint matrices and a symbolic solver using cvxpylayers/diffcp
for differentiable convex optimization.
"""
import logging
import signal
import sys
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch

# Import cvxpy and differentiable layers
try:
    import cvxpy as cp
    from cvxpylayers.torch import CvxpyLayer
    DIFFCP_AVAILABLE = True
except ImportError:
    DIFFCP_AVAILABLE = False
    cp = None
    CvxpyLayer = None

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    """Exception raised when a solver operation times out."""
    pass


class TimeoutHandler:
    """
    Context manager to enforce timeouts on solver operations.
    Uses threading to interrupt long-running processes.
    """
    def __init__(self, timeout_seconds: float):
        self.timeout_seconds = timeout_seconds
        self.timer: Optional[threading.Timer] = None
        self.timed_out = False

    def _timeout_handler(self):
        self.timed_out = True
        raise TimeoutError(f"Operation timed out after {self.timeout_seconds} seconds")

    def __enter__(self):
        self.timer = threading.Timer(self.timeout_seconds, self._timeout_handler)
        self.timer.daemon = True
        self.timer.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.timer:
            self.timer.cancel()
        # Do not suppress exceptions unless it's our specific TimeoutError
        return False


@dataclass
class ConstraintMatrix:
    """
    Represents a constraint matrix for the symbolic solver.

    Attributes:
        A: Constraint matrix (numpy array)
        b: Constraint vector (numpy array)
        G: Inequality constraint matrix (optional)
        h: Inequality constraint vector (optional)
    """
    A: np.ndarray
    b: np.ndarray
    G: Optional[np.ndarray] = None
    h: Optional[np.ndarray] = None

    def validate(self) -> bool:
        """Validate that matrices are well-formed."""
        if self.A is None or self.b is None:
            logger.error("Constraint matrix A or vector b is None")
            return False
        if not isinstance(self.A, np.ndarray) or not isinstance(self.b, np.ndarray):
            logger.error("Constraint matrix A or vector b must be numpy arrays")
            return False
        if self.A.shape[0] != self.b.shape[0]:
            logger.error(f"Mismatch in constraint dimensions: A.shape={self.A.shape}, b.shape={self.b.shape}")
            return False
        return True


class SymbolicSolver:
    """
    Differentiable Symbolic Solver using cvxpylayers.

    Solves convex optimization problems with constraints defined by ConstraintMatrix.
    Supports gradient flow for end-to-end differentiable training/inference.
    """
    def __init__(
        self,
        constraint_matrix: ConstraintMatrix,
        timeout_seconds: float = 300.0,
        use_gpu: bool = False
    ):
        """
        Initialize the symbolic solver.

        Args:
            constraint_matrix: The constraint matrix defining the optimization problem.
            timeout_seconds: Maximum time allowed for solving.
            use_gpu: Whether to attempt GPU acceleration (currently CPU-only enforced).
        """
        if not DIFFCP_AVAILABLE:
            raise ImportError(
                "cvxpylayers is required for differentiable solving. "
                "Install with: pip install cvxpylayers"
            )

        if not constraint_matrix.validate():
            raise ValueError("Invalid constraint matrix provided to SymbolicSolver")

        self.constraint_matrix = constraint_matrix
        self.timeout_seconds = timeout_seconds
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.device = torch.device("cuda" if self.use_gpu else "cpu")

        # Build the cvxpy problem
        self._build_problem()

    def _build_problem(self) -> None:
        """Construct the cvxpy optimization problem."""
        # Define variables
        n_vars = self.constraint_matrix.A.shape[1]
        x = cp.Variable(n_vars)

        # Objective: minimize ||x||^2 (simple regularization)
        objective = cp.Minimize(cp.sum_squares(x))

        # Constraints
        constraints = [
            self.constraint_matrix.A @ x == self.constraint_matrix.b
        ]

        if self.constraint_matrix.G is not None and self.constraint_matrix.h is not None:
            constraints.append(self.constraint_matrix.G @ x <= self.constraint_matrix.h)

        self.problem = cp.Problem(objective, constraints)

        # Convert to cvxpylayer for differentiability
        # Parameters for A, b, G, h to allow dynamic updates
        self.A_param = cp.Parameter(self.constraint_matrix.A.shape)
        self.b_param = cp.Parameter(self.constraint_matrix.b.shape)

        if self.constraint_matrix.G is not None:
            self.G_param = cp.Parameter(self.constraint_matrix.G.shape)
            self.h_param = cp.Parameter(self.constraint_matrix.h.shape)
            constraints = [
                self.A_param @ x == self.b_param,
                self.G_param @ x <= self.h_param
            ]
        else:
            self.G_param = None
            self.h_param = None
            constraints = [self.A_param @ x == self.b_param]

        objective = cp.Minimize(cp.sum_squares(x))
        prob = cp.Problem(objective, constraints)

        self.layer = CvxpyLayer(prob, parameters=[self.A_param, self.b_param] + 
                                ([self.G_param, self.h_param] if self.G_param is not None else []),
                                variables=[x])

    def solve(
        self,
        A: Optional[np.ndarray] = None,
        b: Optional[np.ndarray] = None,
        G: Optional[np.ndarray] = None,
        h: Optional[np.ndarray] = None,
        return_gradient: bool = False
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Solve the optimization problem with potentially updated constraints.

        Args:
            A: Override constraint matrix A.
            b: Override constraint vector b.
            G: Override inequality constraint matrix G.
            h: Override inequality constraint vector h.
            return_gradient: Whether to compute and return gradients.

        Returns:
            Tuple of (solution, gradient) where gradient is None if return_gradient=False.
        """
        # Use provided constraints or default
        A_eff = A if A is not None else self.constraint_matrix.A
        b_eff = b if b is not None else self.constraint_matrix.b
        G_eff = G if G is not None else self.constraint_matrix.G
        h_eff = h if h is not None else self.constraint_matrix.h

        # Validate
        if A_eff.shape[1] != self.constraint_matrix.A.shape[1]:
            raise ValueError(f"Dimension mismatch in A: expected {self.constraint_matrix.A.shape[1]}, got {A_eff.shape[1]}")

        # Prepare parameters
        params = [
            torch.tensor(A_eff, dtype=torch.float32),
            torch.tensor(b_eff, dtype=torch.float32)
        ]
        if G_eff is not None and h_eff is not None:
            params.append(torch.tensor(G_eff, dtype=torch.float32))
            params.append(torch.tensor(h_eff, dtype=torch.float32))

        # Solve with timeout
        try:
            with TimeoutHandler(self.timeout_seconds):
                if return_gradient:
                    # Enable gradients
                    for p in params:
                        p.requires_grad = True
                    solution, = self.layer(*params)
                    # Compute gradient w.r.t. constraints (example: w.r.t. b)
                    if solution.requires_grad:
                        grad = torch.autograd.grad(solution.sum(), params, retain_graph=True)[1].detach().numpy()
                        return solution.detach().cpu().numpy(), grad
                    else:
                        return solution.detach().cpu().numpy(), None
                else:
                    solution, = self.layer(*params)
                    return solution.detach().cpu().numpy(), None
        except TimeoutError as e:
            logger.error(f"Solve timeout: {e}")
            raise
        except Exception as e:
            logger.error(f"Solver error: {e}")
            raise

    def verify_differentiability(self) -> Dict[str, float]:
        """
        Verify that gradients flow correctly through the solver.

        Returns:
            Dictionary with gradient norms for verification.
        """
        try:
            # Create a small perturbation
            A_pert = self.constraint_matrix.A + 1e-4 * np.random.randn(*self.constraint_matrix.A.shape)
            b_pert = self.constraint_matrix.b + 1e-4 * np.random.randn(*self.constraint_matrix.b.shape)

            # Solve with gradients
            sol, grad = self.solve(A=A_pert, b=b_pert, return_gradient=True)

            grad_norm = float(np.linalg.norm(grad)) if grad is not None else 0.0

            return {
                "solution_norm": float(np.linalg.norm(sol)),
                "constraint_grad_norm": grad_norm,
                "is_differentiable": grad_norm > 1e-6
            }
        except Exception as e:
            logger.error(f"Differentiability check failed: {e}")
            return {
                "solution_norm": 0.0,
                "constraint_grad_norm": 0.0,
                "is_differentiable": False,
                "error": str(e)
            }


def main() -> None:
    """
    Main entry point for testing the symbolic solver.
    """
    logging.basicConfig(level=logging.INFO)

    # Create a simple test problem
    A = np.array([[1.0, 1.0], [1.0, -1.0]])
    b = np.array([2.0, 0.0])

    constraint_matrix = ConstraintMatrix(A=A, b=b)
    solver = SymbolicSolver(constraint_matrix, timeout_seconds=30.0)

    # Solve
    solution, _ = solver.solve()
    logger.info(f"Solution: {solution}")

    # Verify differentiability
    diff_check = solver.verify_differentiability()
    logger.info(f"Differentiability check: {diff_check}")


if __name__ == "__main__":
    main()
