"""
Heuristic variance estimation for multi-objective reinforcement learning.

Implements the Moving-Window Heuristic for variance estimation using the last k steps.
This module provides the core logic for the Dynamic Variance-adaptive Advantage
Optimization (DVAO) pipeline.
"""
import numpy as np
from typing import List, Tuple, Optional, Dict
from collections import deque
import json
import os
import sys
import argparse
from datetime import datetime

class MovingWindowVarianceHeuristic:
    """
    Maintains a sliding window of the last k variance estimates and computes
    the current variance estimate based on the windowed data.
    
    Attributes:
        window_size (int): Number of steps to look back (k).
        window (deque): Rolling buffer of recent values.
        values (deque): Rolling buffer of recent squared values for variance calc.
    """
    def __init__(self, window_size: int):
        if window_size < 1:
            raise ValueError("Window size must be at least 1")
        self.window_size = window_size
        self.window = deque(maxlen=window_size)
        self.squared_window = deque(maxlen=window_size)
        self._initialized = False

    def update(self, value: float) -> float:
        """
        Update the heuristic with a new value and return the current variance estimate.
        
        Args:
            value: The new observed value (e.g., advantage, reward).
        
        Returns:
            float: The estimated variance based on the last k values.
        """
        self.window.append(value)
        self.squared_window.append(value ** 2)
        
        if len(self.window) < self.window_size:
            # Not enough data yet, return NaN or 0 depending on policy
            # For this implementation, we return 0 if not enough data to avoid division by zero
            # but in a real training loop, this might be handled by skipping updates
            return 0.0
        
        mean = np.mean(self.window)
        variance = np.mean(self.squared_window) - (mean ** 2)
        
        # Ensure non-negative variance due to floating point errors
        return max(0.0, variance)

    def get_current_variance(self) -> float:
        """
        Get the current variance estimate without updating.
        
        Returns:
            float: The estimated variance based on the current window.
        """
        if len(self.window) < self.window_size:
            return 0.0
        
        mean = np.mean(self.window)
        variance = np.mean(self.squared_window) - (mean ** 2)
        return max(0.0, variance)

    def reset(self):
        """Reset the heuristic state."""
        self.window.clear()
        self.squared_window.clear()
        self._initialized = False


def calculate_windowed_variance(values: List[float], k: int) -> float:
    """
    Calculate the variance of the last k values in the list.
    
    This is a stateless utility function for one-off calculations.
    
    Args:
        values: List of observed values.
        k: Window size (number of last steps to consider).
    
    Returns:
        float: The variance of the last k values.
    
    Raises:
        ValueError: If k is less than 1 or greater than the length of values.
    """
    if k < 1:
        raise ValueError("Window size k must be at least 1")
    if len(values) == 0:
        raise ValueError("Values list cannot be empty")
    
    effective_k = min(k, len(values))
    window_values = values[-effective_k:]
    
    if effective_k == 1:
        return 0.0
    
    mean = np.mean(window_values)
    variance = np.var(window_values, ddof=0)  # Population variance for heuristic
    return variance


def compare_heuristic_to_fullbatch(
    values: List[float], 
    k: int, 
    threshold: float = 0.1
) -> Dict[str, any]:
    """
    Compare the moving-window heuristic variance estimate against the full-batch
    empirical variance.
    
    This function is used for validation and debugging to ensure the heuristic
    is providing reasonable estimates.
    
    Args:
        values: List of all observed values.
        k: Window size for the heuristic.
        threshold: Maximum allowed relative error for the heuristic to be considered
                  "close enough" to the full-batch variance.
    
    Returns:
        dict: A dictionary containing:
            - 'heuristic_variance': Variance from the last k values.
            - 'fullbatch_variance': Variance from all values.
            - 'relative_error': Absolute relative error between the two.
            - 'is_acceptable': Boolean indicating if relative_error <= threshold.
    """
    if len(values) == 0:
        raise ValueError("Values list cannot be empty")
    
    heuristic_var = calculate_windowed_variance(values, k)
    fullbatch_var = np.var(values, ddof=0)
    
    if fullbatch_var == 0:
        relative_error = 0.0 if heuristic_var == 0 else float('inf')
    else:
        relative_error = abs(heuristic_var - fullbatch_var) / fullbatch_var
    
    return {
        'heuristic_variance': float(heuristic_var),
        'fullbatch_variance': float(fullbatch_var),
        'relative_error': float(relative_error),
        'is_acceptable': relative_error <= threshold
    }


def main():
    """
    Main function to demonstrate and verify the Moving-Window Heuristic.
    
    This script:
    1. Generates synthetic test data (simulating a rollout).
    2. Runs the MovingWindowVarianceHeuristic step-by-step.
    3. Compares the heuristic's final output against a full-batch calculation.
    4. Outputs the results to the console and a JSON file.
    """
    print("Starting Moving-Window Heuristic Verification...")
    
    # 1. Generate synthetic test data
    # Simulating a rollout with N=100 steps of advantage estimates
    np.random.seed(42)
    n_steps = 100
    k_window = 20
    
    # Generate data with some noise and a slight trend to simulate real RL behavior
    base_values = np.random.normal(loc=0.0, scale=1.0, size=n_steps)
    # Add a slight trend
    trend = np.linspace(0, 0.5, n_steps)
    test_values = base_values + trend
    
    print(f"Generated {n_steps} synthetic advantage values.")
    print(f"Window size (k): {k_window}")
    
    # 2. Run the heuristic step-by-step
    heuristic = MovingWindowVarianceHeuristic(window_size=k_window)
    variance_history = []
    
    for i, val in enumerate(test_values):
        var_est = heuristic.update(val)
        variance_history.append(var_est)
        
        # Log progress every 20 steps
        if (i + 1) % 20 == 0:
            print(f"Step {i+1}: Current variance estimate = {var_est:.4f}")
    
    final_heuristic_var = heuristic.get_current_variance()
    print(f"Final Heuristic Variance (last {k_window} steps): {final_heuristic_var:.4f}")
    
    # 3. Compare with full-batch
    comparison = compare_heuristic_to_fullbatch(test_values, k_window)
    print(f"Full-batch Variance (all {n_steps} steps): {comparison['fullbatch_variance']:.4f}")
    print(f"Relative Error: {comparison['relative_error']:.4f}")
    print(f"Acceptable (error <= 0.1): {comparison['is_acceptable']}")
    
    # 4. Save results
    output_dir = "data/processed"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "heuristic_verification.json")
    
    result = {
        "timestamp": datetime.now().isoformat(),
        "parameters": {
            "n_steps": n_steps,
            "k_window": k_window,
            "seed": 42
        },
        "results": {
            "final_heuristic_variance": float(final_heuristic_var),
            "fullbatch_variance": float(comparison['fullbatch_variance']),
            "relative_error": float(comparison['relative_error']),
            "is_acceptable": comparison['is_acceptable']
        },
        "variance_history": [float(v) for v in variance_history]
    }
    
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"Results saved to {output_file}")
    
    # Verification check
    if not comparison['is_acceptable']:
        print("Warning: Heuristic variance deviates significantly from full-batch.")
        # In a real run, this might trigger a warning or adjustment, but for
        # verification purposes, we just log it.
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
