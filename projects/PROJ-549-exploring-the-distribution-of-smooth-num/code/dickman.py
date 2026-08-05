"""
Numerical solver for the Dickman function ρ(u) via integration of the delay-differential equation.

Implements the Tenenbaum method for solving:
u * ρ'(u) + ρ(u-1) = 0  for u > 1
with initial condition ρ(u) = 1 for 0 <= u <= 1.

The solver uses a piecewise linear interpolation of ρ(u-1) on each interval [n, n+1]
and integrates the resulting ODE analytically.
"""

import logging
import math
from typing import List, Optional, Tuple

import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
DEFAULT_MAX_U = 100.0
DEFAULT_STEP = 1e-4
EPSILON = 1e-15  # Threshold for underflow


class DickmanFunction:
    """
    Numerical solver for the Dickman function ρ(u).
    
    The Dickman function ρ(u) is defined by the delay-differential equation:
    u * ρ'(u) + ρ(u-1) = 0 for u > 1
    with ρ(u) = 1 for 0 <= u <= 1.
    
    This class implements the Tenenbaum method which integrates the equation
    piecewise on intervals [n, n+1] using linear interpolation of ρ(u-1).
    """
    
    def __init__(self, max_u: float = DEFAULT_MAX_U, step: float = DEFAULT_STEP):
        """
        Initialize the Dickman function solver.
        
        Args:
            max_u: Maximum value of u to compute ρ(u) for.
            step: Step size for numerical integration.
        """
        if max_u <= 0:
            raise ValueError("max_u must be positive")
        if step <= 0:
            raise ValueError("step must be positive")
        if step > 1.0:
            raise ValueError("step must be <= 1.0 for accurate piecewise integration")
        
        self.max_u = max_u
        self.step = step
        self._rho_values: List[Tuple[float, float]] = []
        self._initialized = False
        
        logger.info(f"Initialized Dickman solver: max_u={max_u}, step={step}")
    
    def _initialize_base_case(self):
        """Initialize ρ(u) = 1 for 0 <= u <= 1."""
        self._rho_values = []
        n_steps = int(1.0 / self.step) + 1
        
        for i in range(n_steps):
            u = i * self.step
            self._rho_values.append((u, 1.0))
        
        self._initialized = True
        logger.debug("Initialized base case: ρ(u) = 1 for 0 <= u <= 1")
    
    def _get_rho_interpolated(self, u: float) -> float:
        """
        Get ρ(u) with linear interpolation.
        
        Args:
            u: The value at which to evaluate ρ.
            
        Returns:
            The interpolated value of ρ(u).
        """
        if u < 0:
            return 0.0
        if u <= self.max_u:
            # Find the two surrounding points
            idx = int(u / self.step)
            if idx >= len(self._rho_values) - 1:
                return self._rho_values[-1][1]
            
            u0, rho0 = self._rho_values[idx]
            u1, rho1 = self._rho_values[idx + 1]
            
            # Linear interpolation
            if u1 == u0:
                return rho0
            t = (u - u0) / (u1 - u0)
            return rho0 + t * (rho1 - rho0)
        else:
            # Extrapolate using the last known value (conservative)
            return self._rho_values[-1][1]
    
    def _integrate_interval(self, n: int) -> None:
        """
        Integrate the DDE on the interval [n, n+1].
        
        The equation is: u * ρ'(u) + ρ(u-1) = 0
        => ρ'(u) = -ρ(u-1) / u
        
        Using linear interpolation for ρ(u-1) on [n-1, n]:
        ρ(u-1) ≈ ρ(n-1) + (u - n) * (ρ(n) - ρ(n-1))
        
        This gives us an analytical solution for ρ on [n, n+1].
        """
        if not self._initialized:
            self._initialize_base_case()
        
        if n < 1:
            return
        
        # Get the values at the boundaries of the previous interval
        rho_n_minus_1 = self._get_rho_interpolated(float(n - 1))
        rho_n = self._get_rho_interpolated(float(n))
        
        # Number of steps in this interval
        n_steps = int(1.0 / self.step)
        
        # Starting value for this interval
        current_u = float(n)
        current_rho = rho_n
        
        # Store the starting point
        if current_u > self._rho_values[-1][0]:
            self._rho_values.append((current_u, current_rho))
        
        # Integrate step by step
        for i in range(1, n_steps + 1):
            current_u = n + i * self.step
            if current_u > self.max_u:
                break
            
            # Compute ρ(u-1) using linear interpolation
            u_minus_1 = current_u - 1.0
            rho_u_minus_1 = self._get_rho_interpolated(u_minus_1)
            
            # ρ'(u) = -ρ(u-1) / u
            # Using Euler's method: ρ(u + h) ≈ ρ(u) + h * ρ'(u)
            derivative = -rho_u_minus_1 / current_u
            current_rho += self.step * derivative
            
            # Handle underflow
            if current_rho < EPSILON:
                current_rho = 0.0
            
            self._rho_values.append((current_u, current_rho))
        
        logger.debug(f"Completed integration for interval [{n}, {min(n+1, self.max_u)}]")
    
    def compute(self) -> None:
        """
        Compute ρ(u) for u in [0, max_u].
        
        This method integrates the delay-differential equation piecewise
        on intervals [n, n+1] for n = 1, 2, ..., floor(max_u).
        """
        logger.info(f"Computing ρ(u) for u in [0, {self.max_u}]")
        
        if not self._initialized:
            self._initialize_base_case()
        
        # Integrate on each interval [n, n+1]
        n_max = int(math.ceil(self.max_u))
        
        for n in range(1, n_max + 1):
            if n * self.step > self.max_u:
                break
            self._integrate_interval(n)
        
        # Trim to max_u
        while self._rho_values and self._rho_values[-1][0] > self.max_u:
            self._rho_values.pop()
        
        logger.info(f"Completed computation: {len(self._rho_values)} points generated")
    
    def evaluate(self, u: float) -> float:
        """
        Evaluate ρ(u) at a specific point.
        
        Args:
            u: The point at which to evaluate.
            
        Returns:
            The value of ρ(u).
            
        Raises:
            RuntimeError: If compute() has not been called yet.
        """
        if not self._initialized:
            raise RuntimeError("Must call compute() before evaluate()")
        
        if u < 0:
            return 0.0
        if u > self.max_u:
            logger.warning(f"u={u} exceeds max_u={self.max_u}, returning last computed value")
            return self._rho_values[-1][1] if self._rho_values else 0.0
        
        return self._get_rho_interpolated(u)
    
    def get_table(self) -> List[Tuple[float, float]]:
        """
        Get the computed table of (u, ρ(u)) values.
        
        Returns:
            List of tuples (u, ρ(u)).
        """
        if not self._initialized:
            raise RuntimeError("Must call compute() before get_table()")
        return self._rho_values.copy()
    
    def save_to_file(self, filepath: str, precision: int = 10) -> None:
        """
        Save the computed ρ(u) values to a CSV file.
        
        Args:
            filepath: Path to the output CSV file.
            precision: Number of decimal places for floating point values.
        """
        if not self._initialized:
            raise RuntimeError("Must call compute() before saving")
        
        with open(filepath, 'w') as f:
            f.write("u,rho\n")
            for u, rho in self._rho_values:
                f.write(f"{u:.{precision}f},{rho:.{precision}e}\n")
        
        logger.info(f"Saved {len(self._rho_values)} points to {filepath}")


def compute_dickman_function(
    max_u: float = DEFAULT_MAX_U,
    step: float = DEFAULT_STEP,
    output_file: Optional[str] = None
) -> DickmanFunction:
    """
    Compute the Dickman function ρ(u) up to max_u.
    
    Args:
        max_u: Maximum value of u to compute.
        step: Step size for numerical integration.
        output_file: Optional path to save the results as CSV.
        
    Returns:
        A DickmanFunction instance containing the computed values.
    """
    solver = DickmanFunction(max_u=max_u, step=step)
    solver.compute()
    
    if output_file:
        solver.save_to_file(output_file)
    
    return solver


def rho(u: float, max_u: float = DEFAULT_MAX_U, step: float = DEFAULT_STEP) -> float:
    """
    Convenience function to evaluate ρ(u) at a single point.
    
    Args:
        u: The point at which to evaluate.
        max_u: Maximum value to compute up to (must be >= u).
        step: Step size for numerical integration.
        
    Returns:
        The value of ρ(u).
    """
    if u < 0:
        return 0.0
    if u <= 1.0:
        return 1.0
    
    solver = DickmanFunction(max_u=max(max_u, u), step=step)
    solver.compute()
    return solver.evaluate(u)


def main():
    """Main entry point for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Compute the Dickman function ρ(u) using the Tenenbaum method."
    )
    parser.add_argument(
        "--max-u",
        type=float,
        default=DEFAULT_MAX_U,
        help=f"Maximum value of u to compute (default: {DEFAULT_MAX_U})"
    )
    parser.add_argument(
        "--step",
        type=float,
        default=DEFAULT_STEP,
        help=f"Step size for numerical integration (default: {DEFAULT_STEP})"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output CSV file path (optional)"
    )
    parser.add_argument(
        "--evaluate",
        type=float,
        nargs='+',
        default=None,
        help="Specific u values to evaluate and print"
    )
    
    args = parser.parse_args()
    
    logger.info(f"Starting Dickman function computation: max_u={args.max_u}, step={args.step}")
    
    solver = compute_dickman_function(
        max_u=args.max_u,
        step=args.step,
        output_file=args.output
    )
    
    if args.evaluate:
        logger.info("Evaluating at specific points:")
        for u_val in args.evaluate:
            val = solver.evaluate(u_val)
            print(f"ρ({u_val}) = {val:.10e}")
    
    if args.output:
        logger.info(f"Results saved to {args.output}")
    
    return solver


if __name__ == "__main__":
    main()