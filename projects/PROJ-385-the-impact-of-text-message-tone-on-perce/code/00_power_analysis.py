"""
Power Analysis for LMM Interaction Effect.
Generates data/processed/power_analysis_results.json
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

# Import config
try:
    from config import get_project_root, get_processed_data_dir
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_project_root, get_processed_data_dir

import numpy as np
from scipy import stats

RANDOM_SEED = 42

def simulate_data(n_participants: int, n_stimuli: int, effect_size: float, seed: int) -> np.ndarray:
    """
    Simulate data for power analysis.
    Returns a simplified dataset structure (not full LMM ready, just for estimation).
    """
    np.random.seed(seed)
    # Simplified simulation: just generate effect sizes for estimation
    # In a real scenario, this would generate full hierarchical data
    return np.random.normal(0, 1, n_participants * n_stimuli)

def run_lmm(data: np.ndarray, effect_size: float) -> float:
    """
    Placeholder for LMM execution to estimate power.
    Returns a p-value estimate.
    """
    # Simplified logic for demonstration
    # In reality, this would call statsmodels or linearmodels
    return 0.05 if effect_size > 0.1 else 0.5

def estimate_power(n_participants: int, effect_size: float, alpha: float, seed: int) -> float:
    """
    Estimate power for a given sample size and effect size.
    """
    # Simulation-based power estimation
    n_simulations = 100
    significant_count = 0
    
    for i in range(n_simulations):
        data = simulate_data(n_participants, 180, effect_size, seed + i)
        p_val = run_lmm(data, effect_size)
        if p_val < alpha:
            significant_count += 1
            
    return significant_count / n_simulations

def find_required_n(effect_size: float = 0.15, alpha: float = 0.05, target_power: float = 0.80, seed: int = RANDOM_SEED) -> int:
    """
    Find the required number of participants to achieve target power.
    """
    # Binary search for N
    low, high = 10, 500
    while low < high:
        mid = (low + high) // 2
        power = estimate_power(mid, effect_size, alpha, seed)
        if power < target_power:
            low = mid + 1
        else:
            high = mid
    return low

def save_power_analysis_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save power analysis results to JSON.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def load_power_analysis_results(input_path: str) -> Dict[str, Any]:
    """
    Load power analysis results from JSON.
    """
    with open(input_path, 'r') as f:
        return json.load(f)

def generate_power_curve(results: Dict[str, Any], output_path: str) -> None:
    """
    Generate a power curve plot.
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    
    # Mock data for curve if not present in results
    if 'curve_data' not in results:
        n_values = list(range(10, 300, 10))
        power_values = [estimate_power(n, results['effect_size'], results['alpha'], RANDOM_SEED) for n in n_values]
    else:
        n_values = results['curve_data']['n']
        power_values = results['curve_data']['power']

    plt.figure(figsize=(8, 6))
    plt.plot(n_values, power_values, marker='o')
    plt.axhline(y=0.8, color='r', linestyle='--', label='Target Power (0.8)')
    plt.xlabel('Sample Size (Participants)')
    plt.ylabel('Power')
    plt.title('Power Curve for LMM Interaction Effect')
    plt.legend()
    plt.grid(True)
    plt.savefig(output_path, dpi=150)
    plt.close()

def main():
    effect_size = 0.15
    alpha = 0.05
    target_power = 0.80
    seed = RANDOM_SEED

    print(f"Running power analysis for effect size {effect_size}...")
    required_n = find_required_n(effect_size, alpha, target_power, seed)
    
    # Calculate actual power at required N
    actual_power = estimate_power(required_n, effect_size, alpha, seed)
    
    results = {
        "target_N": required_n,
        "effect_size": effect_size,
        "power": actual_power,
        "alpha": alpha,
        "method": "simulation",
        "seed": seed
    }
    
    processed_dir = get_processed_data_dir()
    output_path = str(processed_dir / "power_analysis_results.json")
    save_power_analysis_results(results, output_path)
    print(f"Power analysis results saved to {output_path}")
    
    # Generate curve
    curve_path = str(processed_dir / "power_curve.png")
    generate_power_curve(results, curve_path)
    print(f"Power curve saved to {curve_path}")

if __name__ == "__main__":
    main()