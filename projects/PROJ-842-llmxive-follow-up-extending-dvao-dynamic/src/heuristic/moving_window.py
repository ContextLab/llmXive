"""
Moving-Window Heuristic for Variance Estimation.

Implements variance estimation using the last k steps of a trajectory,
where k is configurable and must be less than the rollout group size.
"""
import numpy as np
from typing import List, Tuple, Optional, Deque, Generator
from collections import deque
import json
import os
import sys

class MovingWindowVarianceHeuristic:
    """
    Heuristic estimator for variance using a sliding window of size k.
    
    Attributes:
        k (int): Window size (number of steps to consider).
        window (deque): Circular buffer storing the last k values.
        sum_sq (float): Running sum of squared values in the window.
        sum_val (float): Running sum of values in the window.
        count (int): Current number of elements in the window (up to k).
    """
    def __init__(self, k: int):
        if k <= 0:
            raise ValueError("Window size k must be positive.")
        self.k = k
        self.window: Deque[float] = deque(maxlen=k)
        self.sum_sq: float = 0.0
        self.sum_val: float = 0.0
        self.count: int = 0

    def update(self, value: float) -> float:
        """
        Update the window with a new value and return the current variance estimate.
        
        Args:
            value: The new observation value.
        
        Returns:
            float: The unbiased variance estimate of the current window.
                   Returns NaN if fewer than 2 values are in the window.
        """
        # If window is full, remove the oldest value's contribution
        if len(self.window) == self.k:
            old_val = self.window[0]
            self.sum_sq -= old_val ** 2
            self.sum_val -= old_val
            self.count -= 1

        # Add new value
        self.window.append(value)
        self.sum_sq += value ** 2
        self.sum_val += value
        self.count += 1

        # Calculate variance
        if self.count < 2:
            return float('nan')
        
        mean = self.sum_val / self.count
        variance = (self.sum_sq / self.count) - (mean ** 2)
        
        # Unbiased estimator correction (Bessel's correction)
        if self.count > 1:
            variance *= (self.count / (self.count - 1))
        
        return max(0.0, variance)  # Ensure non-negative due to floating point errors

    def get_variance(self) -> float:
        """
        Get the current variance estimate without updating.
        
        Returns:
            float: The current variance estimate or NaN if insufficient data.
        """
        if self.count < 2:
            return float('nan')
        
        mean = self.sum_val / self.count
        variance = (self.sum_sq / self.count) - (mean ** 2)
        
        if self.count > 1:
            variance *= (self.count / (self.count - 1))
        
        return max(0.0, variance)

    def reset(self):
        """Reset the heuristic state."""
        self.window.clear()
        self.sum_sq = 0.0
        self.sum_val = 0.0
        self.count = 0

def calculate_windowed_variance(values: List[float], k: int) -> List[float]:
    """
    Calculate the moving window variance for a list of values.
    
    Args:
        values: List of observations.
        k: Window size.
    
    Returns:
        List of variance estimates at each step.
    """
    heuristic = MovingWindowVarianceHeuristic(k)
    results = []
    for val in values:
        var_est = heuristic.update(val)
        results.append(var_est)
    return results

def compare_heuristic_to_fullbatch(values: List[float], k: int) -> Tuple[float, float, float]:
    """
    Compare the moving window heuristic variance to the full-batch variance.
    
    Args:
        values: List of observations.
        k: Window size for the heuristic.
    
    Returns:
        Tuple containing:
            - heuristic_variance: The final variance from the moving window.
            - fullbatch_variance: The variance of the entire list.
            - ratio: heuristic_variance / fullbatch_variance (or NaN if fullbatch is 0).
    """
    if len(values) < 2:
        raise ValueError("Need at least 2 values to calculate variance.")
    
    # Calculate full-batch variance
    fullbatch_variance = np.var(values, ddof=1)
    
    # Calculate heuristic variance
    heuristic = MovingWindowVarianceHeuristic(k)
    for val in values:
        heuristic.update(val)
    heuristic_variance = heuristic.get_variance()
    
    if fullbatch_variance == 0:
        ratio = float('inf') if heuristic_variance > 0 else float('nan')
    else:
        ratio = heuristic_variance / fullbatch_variance
    
    return heuristic_variance, fullbatch_variance, ratio

def main():
    """
    Main function to demonstrate the Moving Window Heuristic.
    Reads configuration, runs the heuristic, and outputs results.
    """
    # Default parameters if not provided via CLI
    k = 10
    n_samples = 100
    seed = 42
    
    # Parse arguments
    if len(sys.argv) > 1:
        k = int(sys.argv[1])
    if len(sys.argv) > 2:
        n_samples = int(sys.argv[2])
    if len(sys.argv) > 3:
        seed = int(sys.argv[3])

    np.random.seed(seed)
    values = np.random.randn(n_samples).tolist()
    
    # Calculate moving window variance
    var_estimates = calculate_windowed_variance(values, k)
    
    # Compare to full batch
    h_var, fb_var, ratio = compare_heuristic_to_fullbatch(values, k)
    
    # Prepare output
    result = {
        "k": k,
        "n_samples": n_samples,
        "seed": seed,
        "heuristic_variance": h_var,
        "fullbatch_variance": fb_var,
        "ratio": ratio,
        "variance_estimates": var_estimates
    }
    
    # Ensure output directory exists
    output_dir = "data/processed"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "moving_window_variance.json")
    
    # Write results
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"Moving window variance calculation complete.")
    print(f"Results saved to: {output_path}")
    print(f"Heuristic Variance: {h_var:.6f}")
    print(f"Full-batch Variance: {fb_var:.6f}")
    print(f"Ratio: {ratio:.6f}")

if __name__ == "__main__":
    main()
