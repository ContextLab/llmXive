"""
Script to run the full simulation pipeline with detailed logging.
Executes multiple replications and logs parameters/results to data/results/simulation.log
"""
import os
import sys
import time
import argparse
import json
from typing import List, Dict, Any

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from simulation.config import SimulationConfig
from simulation.engine import generate_synthetic_data, save_dataset_instance, calculate_vif
from simulation.logging_utils import ensure_log_directory, log_simulation_run
from models.ols import OLSModel, fit_ols_and_get_intervals
from models.bootstrap import BootstrapModel, fit_bootstrap_and_get_intervals
from models.bayesian import BayesianModel, fit_bayesian_and_get_intervals
from metrics.coverage import check_coverage, calculate_coverage_metrics

def run_single_replication_with_logging(
    config: SimulationConfig,
    seed: int,
    output_dir: str,
    log_entries: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Run a single simulation replication and log parameters.
    
    Args:
        config: Simulation configuration
        seed: Random seed for reproducibility
        output_dir: Directory to save dataset instance
        log_entries: List to append log entries to
    
    Returns:
        Dictionary with replication results and metrics
    """
    start_time = time.time()
    
    try:
        # Generate synthetic data
        dataset = generate_synthetic_data(config, seed)
        
        # Save dataset instance
        dataset_path = save_dataset_instance(dataset, output_dir, seed)
        
        # Calculate VIF scores
        vif_scores = dataset.vif_scores
        vif_max = max(vif_scores.values()) if vif_scores else 0.0
        
        # Check for high collinearity
        is_valid_run = vif_max <= 10.0
        
        # Run OLS model
        ols_model = OLSModel()
        ols_intervals = fit_ols_and_get_intervals(ols_model, dataset.X, dataset.y)
        
        # Check coverage for OLS
        ols_covered = check_coverage(ols_intervals, dataset.beta_true)
        
        # Run Bootstrap model
        bootstrap_model = BootstrapModel(n_bootstraps=1000)
        bootstrap_intervals = fit_bootstrap_and_get_intervals(bootstrap_model, dataset.X, dataset.y)
        
        # Check coverage for Bootstrap
        bootstrap_covered = check_coverage(bootstrap_intervals, dataset.beta_true)
        
        # Run Bayesian model
        bayesian_model = BayesianModel()
        bayesian_intervals, r_hat = fit_bayesian_and_get_intervals(bayesian_model, dataset.X, dataset.y)
        
        # Check coverage for Bayesian
        bayesian_covered = check_coverage(bayesian_intervals, dataset.beta_true)
        
        # Check convergence
        is_converged = r_hat <= 1.05
        
        duration = time.time() - start_time
        
        # Create log entry
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "N": config.N,
            "rho": config.rho,
            "seed": seed,
            "duration": duration,
            "vif_max": vif_max,
            "is_valid_run": is_valid_run,
            "is_converged": is_converged,
            "ols_covered": ols_covered,
            "bootstrap_covered": bootstrap_covered,
            "bayesian_covered": bayesian_covered,
            "dataset_path": dataset_path
        }
        
        log_entries.append(log_entry)
        
        # Log to file immediately
        ensure_log_directory("data/results")
        log_simulation_run(log_entry, "data/results/simulation.log")
        
        return {
            "seed": seed,
            "success": True,
            "is_valid_run": is_valid_run,
            "is_converged": is_converged,
            "ols_covered": ols_covered,
            "bootstrap_covered": bootstrap_covered,
            "bayesian_covered": bayesian_covered,
            "duration": duration,
            "vif_max": vif_max
        }
        
    except Exception as e:
        duration = time.time() - start_time
        error_entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "N": config.N,
            "rho": config.rho,
            "seed": seed,
            "duration": duration,
            "vif_max": 0.0,
            "is_valid_run": False,
            "is_converged": False,
            "ols_covered": False,
            "bootstrap_covered": False,
            "bayesian_covered": False,
            "error": str(e)
        }
        log_entries.append(error_entry)
        ensure_log_directory("data/results")
        log_simulation_run(error_entry, "data/results/simulation.log")
        
        return {
            "seed": seed,
            "success": False,
            "error": str(e)
        }

def main():
    parser = argparse.ArgumentParser(description="Run simulation with logging")
    parser.add_argument("--n-replications", type=int, default=200, help="Number of Monte Carlo replications")
    parser.add_argument("--n", type=int, default=30, help="Sample size per replication")
    parser.add_argument("--rho", type=float, default=0.5, help="Target correlation coefficient")
    parser.add_argument("--predictors", type=int, default=3, help="Number of predictors")
    parser.add_argument("--output-dir", type=str, default="data/simulated", help="Output directory for datasets")
    parser.add_argument("--log-file", type=str, default="data/results/simulation.log", help="Log file path")
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    ensure_log_directory(os.path.dirname(args.log_file))
    
    # Create simulation config
    config = SimulationConfig(
        N=args.n,
        predictors=args.predictors,
        rho=args.rho,
        noise_std=1.0,
        true_coefficients=[1.0, 2.0, 3.0][:args.predictors]
    )
    
    log_entries = []
    results = []
    
    print(f"Starting simulation with {args.n_replications} replications...")
    print(f"Config: N={config.N}, rho={config.rho}, predictors={config.predictors}")
    
    for i in range(args.n_replications):
        seed = i * 42  # Deterministic seed sequence
        print(f"Running replication {i+1}/{args.n_replications} (seed={seed})...")
        
        result = run_single_replication_with_logging(
            config, 
            seed, 
            args.output_dir,
            log_entries
        )
        results.append(result)
        
        if result["success"]:
            status = "OK"
            if not result["is_valid_run"]:
                status = "VIF_FAIL"
            elif not result["is_converged"]:
                status = "CONV_FAIL"
            print(f"  -> {status} (duration: {result['duration']:.2f}s, vif_max: {result['vif_max']:.2f})")
        else:
            print(f"  -> ERROR: {result['error']}")
    
    # Summary
    successful_runs = sum(1 for r in results if r["success"])
    valid_runs = sum(1 for r in results if r.get("is_valid_run", False))
    converged_runs = sum(1 for r in results if r.get("is_converged", False))
    
    print(f"\nSimulation complete.")
    print(f"Successful runs: {successful_runs}/{args.n_replications}")
    print(f"Valid runs (VIF <= 10): {valid_runs}/{successful_runs}")
    print(f"Converged runs (R-hat <= 1.05): {converged_runs}/{valid_runs}")
    print(f"Log file: {args.log_file}")

if __name__ == "__main__":
    main()