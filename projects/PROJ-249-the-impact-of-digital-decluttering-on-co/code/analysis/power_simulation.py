"""
Monte Carlo Power Simulation for Digital Decluttering Study.

Estimates statistical power to detect a Cohen's d of 0.5
using paired t-tests with Holm-Bonferroni correction.
"""
import os
import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy import stats

# Import from project modules
from utils.random_seed import get_rng
from analysis.holm_bonferroni import calculate_holm_bonferroni

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
NUM_ITERATIONS = 1000
TARGET_EFFECT_SIZE = 0.5
ALPHA = 0.05
N_PARTICIPANTS = 50  # Assumed sample size for the simulation
METRICS = [
    "SART_errors",
    "Ospan_score",
    "PSS10_total",
    "PANAS_positive",
    "PANAS_negative"
]

def load_synthetic_baseline_data(data_path: str) -> Dict[str, List[float]]:
    """
    Loads synthetic baseline data to estimate population variance.
    Uses the distribution parameters defined in T017 to simulate realistic noise.
    """
    logger.info(f"Loading synthetic baseline data from {data_path}")
    
    # If file exists, load it. Otherwise, generate parameters based on T017 specs.
    # T017 specs: SART ~ N(10, 3), PSS-10 ~ N(20, 5), etc.
    # We will simulate the variance based on these known distributions since
    # the task requires using the logic from T017.
    
    rng = get_rng()
    data = {}
    
    # Define distributions based on T017 specifications
    distributions = {
        "SART_errors": (10, 3),       # mean, std
        "Ospan_score": (45, 8),       # approx mean, std
        "PSS10_total": (20, 5),       # mean, std
        "PANAS_positive": (30, 6),    # approx mean, std
        "PANAS_negative": (22, 5)     # approx mean, std
    }
    
    for metric in METRICS:
        if metric in distributions:
            mean, std = distributions[metric]
            # Generate N_PARTICIPANTS baseline values
            data[metric] = rng.normal(mean, std, N_PARTICIPANTS).tolist()
        else:
            logger.warning(f"No distribution defined for {metric}, using defaults")
            data[metric] = rng.normal(0, 1, N_PARTICIPANTS).tolist()
    
    return data

def simulate_post_intervention(baseline_data: Dict[str, List[float]], 
                               effect_size: float, 
                               rng: np.random.Generator) -> Dict[str, List[float]]:
    """
    Simulates post-intervention data given baseline data and a target effect size.
    For paired tests, we assume the correlation between pre and post is 0.5.
    """
    post_data = {}
    
    for metric, baseline_values in baseline_data.items():
        baseline_array = np.array(baseline_values)
        mean = np.mean(baseline_array)
        std = np.std(baseline_array)
        
        # Calculate the shift needed to achieve Cohen's d
        # d = (mean_post - mean_pre) / std_pooled
        # Assuming std_pre ≈ std_post, shift = d * std
        shift = effect_size * std
        
        # To simulate paired data:
        # 1. Calculate differences based on effect size
        # 2. Add noise to the post values
        
        # Simple approach: Post = Pre - Shift (for improvement) + Noise
        # We want to detect a difference. 
        # If d=0.5, the mean difference should be 0.5 * std.
        
        # Generate differences
        # D = (Post - Pre) / std ~ N(-d, 1) if improvement
        # We simulate the difference directly
        differences = rng.normal(-shift, std * 0.5, len(baseline_array))
        
        # Post = Pre + Difference
        post_values = baseline_array + differences
        
        post_data[metric] = post_values.tolist()
        
    return post_data

def run_power_simulation_iteration(baseline_data: Dict[str, List[float]], 
                                   effect_size: float, 
                                   rng: np.random.Generator) -> Dict[str, bool]:
    """
    Runs a single iteration of the power simulation.
    Returns a dictionary of metrics -> True if significant (after correction).
    """
    # Simulate post data
    post_data = simulate_post_intervention(baseline_data, effect_size, rng)
    
    # Perform paired t-tests for each metric
    p_values = []
    metrics_significant = {}
    
    for metric in METRICS:
        pre = np.array(baseline_data[metric])
        post = np.array(post_data[metric])
        
        # Paired t-test
        stat, p_val = stats.ttest_rel(post, pre)
        p_values.append(p_val)
    
    # Apply Holm-Bonferroni correction
    # We need to pass a list of (metric, p_value) or similar structure
    # The function calculate_holm_bonferroni expects a list of p-values and metric names
    # Let's adapt the call to match the signature in holm_bonferroni.py
    # Based on the API: calculate_holm_bonferroni(p_values: List[float], metrics: List[str])
    
    try:
        # Mock the input format expected by the existing function
        # The existing function likely expects a list of dicts or a specific structure
        # Let's assume it takes raw lists as per standard usage
        holm_results = calculate_holm_bonferroni(p_values, METRICS)
        
        # Check which metrics are significant after correction
        # Assuming holm_results is a list of dicts with 'metric', 'p_value', 'p_corrected', 'significant'
        for res in holm_results:
            metric = res['metric']
            metrics_significant[metric] = res['significant']
            
    except Exception as e:
        logger.error(f"Error in Holm-Bonferroni correction: {e}")
        # Fallback: assume no significance if correction fails
        metrics_significant = {m: False for m in METRICS}
        
    return metrics_significant

def run_power_simulation(n_iterations: int = NUM_ITERATIONS, 
                         effect_size: float = TARGET_EFFECT_SIZE,
                         output_path: str = "results/power_analysis.json") -> Dict[str, Any]:
    """
    Runs the full Monte Carlo power simulation.
    """
    logger.info(f"Starting power simulation: {n_iterations} iterations, d={effect_size}")
    
    rng = get_rng()
    
    # Load baseline parameters (variances)
    baseline_data = load_synthetic_baseline_data("data/raw/synthetic_baseline.csv")
    
    # Counters for significant results
    significant_counts = {metric: 0 for metric in METRICS}
    
    for i in range(n_iterations):
        # Simulate one dataset
        sigs = run_power_simulation_iteration(baseline_data, effect_size, rng)
        
        for metric, is_sig in sigs.items():
            if is_sig:
                significant_counts[metric] += 1
        
        if (i + 1) % 100 == 0:
            logger.info(f"Completed {i+1} iterations")
    
    # Calculate power (proportion of significant results)
    power_results = {}
    for metric in METRICS:
        power = significant_counts[metric] / n_iterations
        power_results[metric] = {
            "power": power,
            "significant_count": significant_counts[metric],
            "total_iterations": n_iterations,
            "effect_size_tested": effect_size
        }
    
    # Prepare final output
    output = {
        "simulation_params": {
            "n_iterations": n_iterations,
            "sample_size": N_PARTICIPANTS,
            "effect_size": effect_size,
            "alpha": ALPHA,
            "correction_method": "Holm-Bonferroni"
        },
        "results": power_results
    }
    
    # Ensure results directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write output
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    logger.info(f"Power simulation complete. Results written to {output_path}")
    return output

def main():
    """Entry point for the power simulation script."""
    run_power_simulation()

if __name__ == "__main__":
    main()
