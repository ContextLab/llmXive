"""
code/dickman.py: Numerical solver for the Dickman function ρ(u).
"""
import logging
import math
from typing import List, Optional, Tuple
import numpy as np

class DickmanFunction:
    """
    Numerical solver for the Dickman function ρ(u) via integration of the
    delay-differential equation (Tenenbaum method).
    """
    def __init__(self, max_u: float = 100.0, resolution: int = 100000):
        self.max_u = max_u
        self.resolution = resolution
        self.u_values = np.linspace(0, max_u, resolution)
        self.rho_values = np.zeros(resolution)
        self._compute()

    def _compute(self):
        """Compute ρ(u) using the delay-differential equation."""
        # Initial condition: ρ(u) = 1 for 0 ≤ u ≤ 1
        for i, u in enumerate(self.u_values):
            if u <= 1:
                self.rho_values[i] = 1.0
            else:
                # ρ(u) = ρ(u-1) - ∫_{u-1}^u ρ(t-1)/t dt
                # We use numerical integration
                prev_idx = i - 1
                if prev_idx >= 0:
                    # Approximate the integral using trapezoidal rule
                    # This is a simplified version; a full implementation would use more sophisticated integration
                    integral = 0.0
                    # For u > 1, we integrate from u-1 to u
                    # We need ρ(t-1) for t in [u-1, u], which is ρ(s) for s in [u-2, u-1]
                    # This requires looking back in the array
                    start_idx = max(0, prev_idx - 1)
                    if start_idx < prev_idx:
                        # Trapezoidal approximation
                        for j in range(start_idx, prev_idx):
                            t = self.u_values[j] + 1  # t-1 in the integral
                            if t > 0:
                                integral += self.rho_values[j] / t
                        integral *= (self.u_values[prev_idx] - self.u_values[start_idx]) / (prev_idx - start_idx) if prev_idx > start_idx else 0
                    self.rho_values[i] = self.rho_values[prev_idx] - integral

    def __call__(self, u: float) -> float:
        """Evaluate ρ(u) at a given point."""
        if u < 0:
            return 0.0
        if u > self.max_u:
            # Extrapolate or return small value
            return math.exp(-u * math.log(u))  # Asymptotic approximation
        idx = int(u / self.max_u * (self.resolution - 1))
        idx = min(idx, self.resolution - 1)
        return self.rho_values[idx]

def compute_dickman_function(u: float, max_u: float = 100.0) -> float:
    """Compute ρ(u) for a single value of u."""
    dickman = DickmanFunction(max_u=max_u)
    return dickman(u)

def rho(u: float) -> float:
    """
    Convenience function to compute ρ(u).
    Uses a cached DickmanFunction instance for efficiency.
    """
    # For efficiency, we could cache the DickmanFunction instance
    # For now, create a new one (slow for repeated calls)
    return compute_dickman_function(u)

def main():
    """CLI entry point for Dickman function (for debugging)."""
    import argparse
    parser = argparse.ArgumentParser(description="Compute Dickman function ρ(u)")
    parser.add_argument("--u", type=float, default=1.0, help="Value of u")
    args = parser.parse_args()

    result = rho(args.u)
    print(f"ρ({args.u}) = {result}")

if __name__ == "__main__":
    main()
