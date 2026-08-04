import argparse
import sys
import os
import json
from typing import Optional, List, Dict, Any
import numpy as np

def parse_args():
    parser = argparse.ArgumentParser(description="Causal Inference Simulation Pipeline")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--output", type=str, help="Path to output directory")
    return parser.parse_args()

def compute_run_seed(base_seed: int, run_index: int) -> int:
    """Compute a unique seed for a specific run."""
    return base_seed + run_index

def run_single_simulation(seed: int, beta: float, n: int = 1000):
    """
    Run a single simulation with given parameters.
    
    This function orchestrates the full pipeline:
    1. Regenerate ground truth parameters
    2. Generate synthetic SCM
    3. Inject MNAR missingness
    4. Run imputation and estimation
    5. Calculate bias metrics
    
    Args:
        seed: Random seed for this run
        beta: MNAR mechanism parameter
        n: Sample size
        
    Returns:
        Dictionary containing simulation results
    """
    from simulation.scm_generator import regenerate_ground_truth, generate_scm
    from simulation.missingness import inject_mnar, tune_alpha
    from analysis.pipeline import run_imputation_and_estimation
    from analysis.metrics import calculate_bias_metrics
    
    # Step 1: Regenerate ground truth
    tau_true, beta_value = regenerate_ground_truth(seed, beta)
    
    # Step 2: Generate synthetic SCM
    dataset = generate_scm(seed, n, tau_true)
    
    # Step 3: Inject MNAR missingness
    # First, tune alpha to achieve target missingness rate
    target_rate = 0.3  # 30% missingness
    alpha = tune_alpha(beta_value, target_rate)
    
    # Inject missingness
    incomplete_data = inject_mnar(dataset, beta_value, target_rate)
    
    # Step 4: Run imputation and estimation
    results = run_imputation_and_estimation(incomplete_data)
    
    # Step 5: Calculate bias metrics
    bias_results = {}
    for method, estimates in results.items():
        for estimator, estimate in estimates.items():
            bias_metrics = calculate_bias_metrics([estimate.ate], tau_true)
            bias_results[f"{method}_{estimator}"] = {
                "ate": estimate.ate,
                "se": estimate.se,
                "ci_lower": estimate.ci_lower,
                "ci_upper": estimate.ci_upper,
                "bias": bias_metrics["absolute_bias"],
                "rmse": bias_metrics["rmse"]
            }
    
    return {
        "seed": seed,
        "beta": beta_value,
        "tau_true": tau_true,
        "alpha": alpha,
        "results": bias_results
    }

def main():
    args = parse_args()
    
    # Load configuration if provided
    config = {}
    if args.config:
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    # Set output directory
    output_dir = args.output or "data/results"
    os.makedirs(output_dir, exist_ok=True)
    
    # Get simulation parameters from config or defaults
    betas = config.get("betas", [0.0, 0.2, 0.5, 0.8, 1.0])
    n_runs = config.get("n_runs", 200)
    base_seed = config.get("base_seed", 42)
    n = config.get("sample_size", 1000)
    
    all_results = []
    
    # Run simulations for each beta value
    for beta in betas:
        for i in range(n_runs):
            run_seed = compute_run_seed(base_seed, i)
            result = run_single_simulation(run_seed, beta, n)
            result["run_id"] = f"{beta}_{i}"
            all_results.append(result)
            
            # Progress indicator
            if (i + 1) % 50 == 0:
                print(f"Completed {i + 1}/{n_runs} runs for beta={beta}")
    
    # Save aggregated results
    output_file = os.path.join(output_dir, "simulation_results.json")
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"Simulation complete. Results saved to {output_file}")

if __name__ == "__main__":
    main()