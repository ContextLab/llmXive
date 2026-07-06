import os
import sys
import json
import time
import argparse
from typing import List, Dict, Any, Tuple

from simulation.config import SimulationConfig
from simulation.engine import generate_dataset, save_dataset_instance, calculate_vif, load_dataset_instance
from models.ols import fit_ols_and_get_intervals
from models.bootstrap import fit_bootstrap_and_get_intervals
from models.bayesian import fit_bayesian_and_get_intervals
from metrics.coverage import check_coverage, calculate_coverage_metrics

def run_single_replication(config: SimulationConfig, seed: int, method: str = "all") -> Dict[str, Any]:
    """
    Run a single replication of the simulation for a given config and seed.
    
    Returns a dictionary containing:
    - seed: The random seed used
    - method: The method used ('ols', 'bootstrap', 'bayesian', or 'all')
    - coverage: Binary coverage flags for each parameter
    - interval_widths: Width of confidence/credible intervals
    - vif_max: Maximum VIF value for the dataset
    - r_hat: R-hat value for Bayesian method (None for others)
    - valid: Boolean indicating if the run should be included in final metrics
    - reason_invalid: Reason for invalidity if valid is False
    """
    start_time = time.time()
    
    try:
        # Generate dataset
        dataset = generate_dataset(config, seed)
        X, y, beta_true = dataset.X, dataset.y, dataset.beta_true
        
        # Calculate VIF
        vif_values = calculate_vif(X)
        vif_max = max(vif_values) if vif_values else 0.0
        
        # Check VIF threshold
        if vif_max > 10:
            return {
                "seed": seed,
                "method": method,
                "coverage": [],
                "interval_widths": [],
                "vif_max": vif_max,
                "r_hat": None,
                "valid": False,
                "reason_invalid": f"VIF too high: {vif_max:.2f} > 10",
                "duration": time.time() - start_time
            }
        
        # Store results based on method
        results = {
            "seed": seed,
            "method": method,
            "vif_max": vif_max,
            "valid": True,
            "reason_invalid": None,
            "duration": time.time() - start_time
        }
        
        if method == "ols" or method == "all":
            intervals, cov_flags, widths = fit_ols_and_get_intervals(X, y, beta_true)
            results["method"] = "ols"
            results["coverage"] = cov_flags
            results["interval_widths"] = widths
            results["r_hat"] = None
            
        elif method == "bootstrap" or method == "all":
            intervals, cov_flags, widths = fit_bootstrap_and_get_intervals(X, y, beta_true)
            results["method"] = "bootstrap"
            results["coverage"] = cov_flags
            results["interval_widths"] = widths
            results["r_hat"] = None
            
        elif method == "bayesian" or method == "all":
            intervals, cov_flags, widths, r_hat = fit_bayesian_and_get_intervals(X, y, beta_true)
            results["method"] = "bayesian"
            results["coverage"] = cov_flags
            results["interval_widths"] = widths
            results["r_hat"] = r_hat
            
            # Check R-hat threshold
            if r_hat is not None and r_hat > 1.05:
                results["valid"] = False
                results["reason_invalid"] = f"R-hat too high: {r_hat:.4f} > 1.05"
        
        return results
        
    except Exception as e:
        return {
            "seed": seed,
            "method": method,
            "coverage": [],
            "interval_widths": [],
            "vif_max": 0.0,
            "r_hat": None,
            "valid": False,
            "reason_invalid": f"Exception: {str(e)}",
            "duration": time.time() - start_time
        }

def run_full_simulation(config: SimulationConfig, n_replications: int = 200, 
                        output_path: str = "data/results/coverage_metrics.json",
                        filtered_output_path: str = "data/results/filtered_metrics.json") -> Dict[str, Any]:
    """
    Run the full simulation with multiple replications.
    
    Args:
        config: Simulation configuration
        n_replications: Number of Monte Carlo replications
        output_path: Path to save all results
        filtered_output_path: Path to save filtered results (excluding invalid runs)
        
    Returns:
        Dictionary with aggregated metrics
    """
    print(f"Starting simulation with {n_replications} replications...")
    start_time = time.time()
    
    all_results = []
    
    for i in range(n_replications):
        seed = config.seed + i
        print(f"Replication {i+1}/{n_replications} (seed={seed})")
        
        # Run all methods for this replication
        methods = ["ols", "bootstrap", "bayesian"]
        for method in methods:
            result = run_single_replication(config, seed, method)
            result["replication_id"] = i
            all_results.append(result)
            
    total_duration = time.time() - start_time
    print(f"Simulation completed in {total_duration:.2f} seconds")
    
    # Save all results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"Saved all results to {output_path}")
    
    # Filter results: exclude runs with R-hat > 1.05 or VIF > 10
    filtered_results = [r for r in all_results if r["valid"]]
    invalid_count = len(all_results) - len(filtered_results)
    
    # Calculate coverage metrics for filtered results
    coverage_metrics = calculate_coverage_metrics(filtered_results)
    
    # Add metadata to filtered results
    for method in ["ols", "bootstrap", "bayesian"]:
        method_results = [r for r in filtered_results if r["method"] == method]
        if method in coverage_metrics:
            coverage_metrics[method]["total_attempts"] = len([r for r in all_results if r["method"] == method])
            coverage_metrics[method]["invalid_count"] = invalid_count
    
    # Save filtered results
    filtered_output = {
        "metadata": {
            "total_replications": n_replications,
            "total_attempts": len(all_results),
            "valid_runs": len(filtered_results),
            "invalid_runs": invalid_count,
            "total_duration": total_duration,
            "config": {
                "N": config.N,
                "predictors": config.predictors,
                "rho": config.rho,
                "noise_std": config.noise_std,
                "seed": config.seed
            }
        },
        "coverage_metrics": coverage_metrics,
        "individual_results": filtered_results
    }
    
    os.makedirs(os.path.dirname(filtered_output_path), exist_ok=True)
    with open(filtered_output_path, 'w') as f:
        json.dump(filtered_output, f, indent=2)
    print(f"Saved filtered results to {filtered_output_path}")
    print(f"Filtered out {invalid_count} invalid runs")
    
    return filtered_output

def main():
    """Main entry point for the simulation."""
    parser = argparse.ArgumentParser(description="Run uncertainty quantification simulation")
    parser.add_argument("--config", type=str, default="data/results/simulation_config.json",
                      help="Path to simulation configuration file")
    parser.add_argument("--replications", type=int, default=200,
                      help="Number of Monte Carlo replications")
    parser.add_argument("--output", type=str, default="data/results/coverage_metrics.json",
                      help="Output path for all results")
    parser.add_argument("--filtered-output", type=str, default="data/results/filtered_metrics.json",
                      help="Output path for filtered results")
    
    args = parser.parse_args()
    
    # Load configuration
    if os.path.exists(args.config):
        with open(args.config, 'r') as f:
            config_dict = json.load(f)
        config = SimulationConfig(**config_dict)
    else:
        # Default configuration
        config = SimulationConfig(
            N=30,
            predictors=3,
            rho=0.5,
            noise_std=1.0,
            seed=42
        )
    
    # Run simulation
    results = run_full_simulation(
        config=config,
        n_replications=args.replications,
        output_path=args.output,
        filtered_output_path=args.filtered_output
    )
    
    print("\nSummary:")
    print(f"Total attempts: {results['metadata']['total_attempts']}")
    print(f"Valid runs: {results['metadata']['valid_runs']}")
    print(f"Invalid runs: {results['metadata']['invalid_runs']}")
    
    for method, metrics in results['coverage_metrics'].items():
        print(f"\n{method.upper()}:")
        print(f"  Coverage rate: {metrics['coverage_rate']:.4f}")
        print(f"  Avg interval width: {metrics['avg_interval_width']:.4f}")
        print(f"  Valid samples: {metrics['valid_n']}")

if __name__ == "__main__":
    main()