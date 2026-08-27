"""
Script to run simulation replications with comprehensive logging.

This script orchestrates the simulation process, running multiple replications
and logging detailed information about each run to a JSON file.
"""
import os
import sys
import time
import argparse
import json
from typing import List, Dict, Any
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from simulation.config import SimulationConfig
from simulation.engine import generate_dataset, calculate_vif
from simulation.logging_utils import ensure_log_directory, log_simulation_run
from metrics.coverage import check_coverage, calculate_coverage_metrics
from models.ols import fit_ols_and_get_intervals
from models.bootstrap import fit_bootstrap_and_get_intervals
from models.bayesian import fit_bayesian_and_get_intervals


def run_single_replication_with_logging(
    config: SimulationConfig,
    seed: int,
    methods: List[str] = ["ols", "bootstrap", "bayesian"]
) -> Dict[str, Any]:
    """
    Run a single simulation replication with detailed logging.
    
    Args:
        config: Simulation configuration parameters
        seed: Random seed for reproducibility
        methods: List of methods to run (ols, bootstrap, bayesian)
        
    Returns:
        Dictionary containing run results and metrics
    """
    start_time = time.time()
    
    try:
        # Generate synthetic data
        dataset = generate_dataset(config, seed)
        X, y, beta_true = dataset.X, dataset.y, dataset.beta_true
        
        # Calculate VIF scores
        vif_scores = calculate_vif(X)
        vif_max = max(vif_scores.values()) if vif_scores else 0.0
        
        # Check for rank deficiency
        n_samples, n_features = X.shape
        if n_samples <= n_features:
            return {
                "seed": seed,
                "status": "failed",
                "reason": "rank_deficient",
                "n_samples": n_samples,
                "n_features": n_features,
                "duration": time.time() - start_time
            }
        
        # Initialize results dictionary
        results = {
            "seed": seed,
            "N": n_samples,
            "rho": config.rho,
            "methods": {},
            "vif_max": vif_max,
            "beta_true": beta_true.tolist(),
            "status": "success"
        }
        
        # Run OLS if requested
        if "ols" in methods:
            try:
                coef_est, ci_lower, ci_upper = fit_ols_and_get_intervals(X, y)
                covered = check_coverage(beta_true, ci_lower, ci_upper)
                results["methods"]["ols"] = {
                    "coef_est": coef_est.tolist(),
                    "ci_lower": ci_lower.tolist(),
                    "ci_upper": ci_upper.tolist(),
                    "covered": covered.tolist()
                }
            except Exception as e:
                results["methods"]["ols"] = {"error": str(e), "status": "failed"}
        
        # Run Bootstrap if requested
        if "bootstrap" in methods:
            try:
                coef_est, ci_lower, ci_upper = fit_bootstrap_and_get_intervals(X, y)
                covered = check_coverage(beta_true, ci_lower, ci_upper)
                results["methods"]["bootstrap"] = {
                    "coef_est": coef_est.tolist(),
                    "ci_lower": ci_lower.tolist(),
                    "ci_upper": ci_upper.tolist(),
                    "covered": covered.tolist()
                }
            except Exception as e:
                results["methods"]["bootstrap"] = {"error": str(e), "status": "failed"}
        
        # Run Bayesian if requested
        if "bayesian" in methods:
            try:
                coef_est, ci_lower, ci_upper = fit_bayesian_and_get_intervals(X, y)
                covered = check_coverage(beta_true, ci_lower, ci_upper)
                results["methods"]["bayesian"] = {
                    "coef_est": coef_est.tolist(),
                    "ci_lower": ci_lower.tolist(),
                    "ci_upper": ci_upper.tolist(),
                    "covered": covered.tolist()
                }
            except Exception as e:
                results["methods"]["bayesian"] = {"error": str(e), "status": "failed"}
                
    except Exception as e:
        results = {
            "seed": seed,
            "status": "failed",
            "reason": str(e),
            "duration": time.time() - start_time
        }
    
    # Calculate duration
    duration = time.time() - start_time
    results["duration"] = duration
    
    return results


def main():
    """Main entry point for the simulation with logging script."""
    parser = argparse.ArgumentParser(description="Run simulation with comprehensive logging")
    parser.add_argument("--n_replications", type=int, default=200, help="Number of replications")
    parser.add_argument("--n_samples", type=int, default=30, help="Number of samples per replication")
    parser.add_argument("--n_features", type=int, default=3, help="Number of features")
    parser.add_argument("--rho", type=float, default=0.5, help="Correlation coefficient")
    parser.add_argument("--noise_std", type=float, default=1.0, help="Noise standard deviation")
    parser.add_argument("--seed", type=int, default=42, help="Base random seed")
    parser.add_argument("--output_dir", type=str, default="data/results", help="Output directory")
    parser.add_argument("--methods", nargs="+", default=["ols", "bootstrap", "bayesian"],
                      help="Methods to run")
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Ensure log directory exists
    log_dir = ensure_log_directory()
    
    # Create simulation configuration
    config = SimulationConfig(
        N=args.n_samples,
        n_predictors=args.n_features,
        rho=args.rho,
        noise_std=args.noise_std,
        true_coefficients=None  # Will be generated internally
    )
    
    # Run replications
    all_results = []
    start_total = time.time()
    
    print(f"Starting {args.n_replications} replications with N={args.n_samples}, rho={args.rho}")
    
    for i in range(args.n_replications):
        seed = args.seed + i
        print(f"Running replication {i+1}/{args.n_replications} (seed={seed})")
        
        result = run_single_replication_with_logging(config, seed, args.methods)
        all_results.append(result)
        
        # Log each run to the JSON log file
        log_entry = {
            "timestamp": time.time(),
            "seed": seed,
            "N": config.N,
            "rho": config.rho,
            "duration": result.get("duration", 0),
            "vif_max": result.get("vif_max", 0),
            "status": result.get("status", "unknown"),
            "methods_run": args.methods
        }
        log_simulation_run(log_entry)
    
    total_duration = time.time() - start_total
    print(f"Completed {args.n_replications} replications in {total_duration:.2f}s")
    
    # Save aggregated results
    results_file = output_dir / "simulation_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            "config": {
                "N": args.n_samples,
                "rho": args.rho,
                "n_features": args.n_features,
                "noise_std": args.noise_std
            },
            "total_replications": args.n_replications,
            "total_duration": total_duration,
            "results": all_results
        }, f, indent=2)
    
    print(f"Results saved to {results_file}")
    
    # Log final summary
    summary_entry = {
        "timestamp": time.time(),
        "event": "simulation_complete",
        "total_replications": args.n_replications,
        "total_duration": total_duration,
        "config": {
            "N": args.n_samples,
            "rho": args.rho
        }
    }
    log_simulation_run(summary_entry)


if __name__ == "__main__":
    main()
