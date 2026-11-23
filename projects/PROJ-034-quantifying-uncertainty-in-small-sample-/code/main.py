import os
import sys
import json
import time
import argparse
import logging
from typing import List, Dict, Any, Optional

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from simulation.config import SimulationConfig
from simulation.engine import (
    generate_synthetic_data,
    calculate_vif,
    save_dataset_instance,
    DatasetInstance
)
from metrics.coverage import check_coverage, calculate_coverage_metrics
from models.ols import fit_ols_and_get_intervals
from models.bootstrap import fit_bootstrap_and_get_intervals
from models.bayesian import fit_bayesian_and_get_intervals

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(project_root, 'data', 'results', 'simulation.log'), mode='a')
    ]
)
logger = logging.getLogger(__name__)

def run_single_replication(
    config: SimulationConfig,
    seed: int,
    method: str = "ols"
) -> Dict[str, Any]:
    """
    Run a single replication of the simulation for a specific method.
    Returns a dictionary containing results and metadata.
    """
    logger.info(f"Starting replication {seed} with method {method}")
    start_time = time.time()

    try:
        # Generate synthetic data
        dataset: DatasetInstance = generate_synthetic_data(config, seed)
        
        # Check VIF
        max_vif = max(dataset.vif_scores.values()) if dataset.vif_scores else 0
        vif_fail = max_vif > 10
        
        if vif_fail:
            logger.warning(f"Replication {seed}: VIF check failed (max={max_vif})")
            return {
                "seed": seed,
                "method": method,
                "status": "invalid",
                "failure_reason": "vif_fail",
                "max_vif": max_vif,
                "duration": time.time() - start_time
            }

        # Fit model and get intervals
        if method == "ols":
            intervals, r_hat, status = fit_ols_and_get_intervals(dataset.X, dataset.y)
        elif method == "bootstrap":
            intervals, r_hat, status = fit_bootstrap_and_get_intervals(dataset.X, dataset.y)
        elif method == "bayesian":
            intervals, r_hat, status = fit_bayesian_and_get_intervals(dataset.X, dataset.y)
        else:
            raise ValueError(f"Unknown method: {method}")

        # Check convergence (for Bayesian)
        r_hat_fail = False
        if r_hat is not None and r_hat > 1.05:
            r_hat_fail = True
            logger.warning(f"Replication {seed}: R-hat check failed (r_hat={r_hat})")

        if r_hat_fail:
            return {
                "seed": seed,
                "method": method,
                "status": "invalid",
                "failure_reason": "r_hat_fail",
                "r_hat": r_hat,
                "duration": time.time() - start_time
            }

        # Calculate coverage for each parameter
        coverage_results = []
        for i, true_beta in enumerate(dataset.beta_true):
            lower, upper = intervals[i]
            covered = check_coverage(lower, upper, true_beta)
            coverage_results.append({
                "parameter_index": i,
                "true_beta": true_beta,
                "lower": lower,
                "upper": upper,
                "covered": covered
            })

        duration = time.time() - start_time
        logger.info(f"Replication {seed} completed in {duration:.2f}s")

        return {
            "seed": seed,
            "method": method,
            "status": "valid",
            "failure_reason": None,
            "intervals": intervals,
            "coverage_results": coverage_results,
            "max_vif": max_vif,
            "r_hat": r_hat,
            "duration": duration
        }

    except Exception as e:
        logger.error(f"Replication {seed} failed with exception: {e}", exc_info=True)
        return {
            "seed": seed,
            "method": method,
            "status": "invalid",
            "failure_reason": "other",
            "error_message": str(e),
            "duration": time.time() - start_time
        }

def run_full_simulation(
    config: SimulationConfig,
    n_replications: int = 200,
    methods: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Run the full Monte Carlo simulation.
    """
    if methods is None:
        methods = ["ols", "bootstrap", "bayesian"]
    
    all_results = []
    
    logger.info(f"Starting full simulation with {n_replications} replications and methods: {methods}")
    start_time = time.time()

    for rep_idx in range(n_replications):
        seed = rep_idx + 1  # Use 1-based seeds for reproducibility
        
        for method in methods:
            result = run_single_replication(config, seed, method)
            all_results.append(result)

    total_duration = time.time() - start_time
    logger.info(f"Full simulation completed in {total_duration:.2f}s")

    # Save raw results
    output_path = os.path.join(project_root, 'data', 'results', 'coverage_metrics.json')
    with open(output_path, 'w') as f:
        json.dump({
            "results": all_results,
            "config": config.__dict__,
            "n_replications": n_replications,
            "methods": methods,
            "total_duration": total_duration
        }, f, indent=2)
    
    logger.info(f"Raw results saved to {output_path}")
    
    return all_results

def filter_and_save_results(
    results: List[Dict[str, Any]],
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Filter results to exclude runs with R-hat > 1.05 or VIF > 10.
    Calculate coverage metrics only on valid runs.
    """
    if output_path is None:
        output_path = os.path.join(project_root, 'data', 'results', 'filtered_metrics.json')

    logger.info("Filtering results and calculating metrics...")

    # Separate valid and invalid runs
    valid_runs = []
    invalid_runs = []
    failure_reasons = {"r_hat_fail": 0, "vif_fail": 0, "other": 0}

    for result in results:
        if result["status"] == "valid":
            valid_runs.append(result)
        else:
            invalid_runs.append(result)
            reason = result.get("failure_reason", "other")
            if reason in failure_reasons:
                failure_reasons[reason] += 1
            else:
                failure_reasons["other"] += 1

    logger.info(f"Valid runs: {len(valid_runs)}, Invalid runs: {len(invalid_runs)}")

    # Calculate coverage metrics per method
    method_metrics = {}
    methods = list(set(r["method"] for r in valid_runs))

    for method in methods:
        method_valid_runs = [r for r in valid_runs if r["method"] == method]
        
        if not method_valid_runs:
            logger.warning(f"No valid runs for method {method}")
            continue

        # Aggregate coverage results
        all_covered = []
        all_widths = []
        
        for run in method_valid_runs:
          for cov in run.get("coverage_results", []):
              all_covered.append(cov["covered"])
              width = cov["upper"] - cov["lower"]
              all_widths.append(width)

        coverage_rate = sum(all_covered) / len(all_covered) if all_covered else 0.0
        avg_width = sum(all_widths) / len(all_widths) if all_widths else 0.0

        method_metrics[method] = {
            "coverage_rate": coverage_rate,
            "interval_width": avg_width,
            "valid_n": len(method_valid_runs),
            "total_runs": len([r for r in results if r["method"] == method])
        }

    filtered_output = {
        "summary": {
            "total_runs": len(results),
            "valid_runs": len(valid_runs),
            "invalid_runs": len(invalid_runs),
            "failure_reasons": failure_reasons
        },
        "method_metrics": method_metrics,
        "exclusion_criteria": {
            "r_hat_threshold": 1.05,
            "vif_threshold": 10
        }
    }

    with open(output_path, 'w') as f:
        json.dump(filtered_output, f, indent=2)

    logger.info(f"Filtered results saved to {output_path}")
    
    return filtered_output

def main():
    """
    Main entry point for the simulation pipeline.
    """
    parser = argparse.ArgumentParser(description="Run uncertainty quantification simulation")
    parser.add_argument('--n-replications', type=int, default=200, help='Number of Monte Carlo replications')
    parser.add_argument('--methods', type=str, nargs='+', default=['ols', 'bootstrap', 'bayesian'],
                      help='Methods to compare')
    parser.add_argument('--config', type=str, default=None, help='Path to simulation config JSON')
    args = parser.parse_args()

    # Default simulation config
    config = SimulationConfig(
        n_samples=30,
        n_predictors=3,
        correlation=0.5,
        noise_std=1.0,
        true_coefficients=[1.0, 2.0, 3.0]
    )

    if args.config:
        with open(args.config, 'r') as f:
            config_dict = json.load(f)
            config = SimulationConfig(**config_dict)

    # Run simulation
    results = run_full_simulation(
        config=config,
        n_replications=args.n_replications,
        methods=args.methods
    )

    # Filter and save results
    filtered_results = filter_and_save_results(results)

    # Print summary
    print("\n=== SIMULATION SUMMARY ===")
    print(f"Total runs: {filtered_results['summary']['total_runs']}")
    print(f"Valid runs: {filtered_results['summary']['valid_runs']}")
    print(f"Invalid runs: {filtered_results['summary']['invalid_runs']}")
    print(f"Failure reasons: {filtered_results['summary']['failure_reasons']}")
    print("\nMethod Metrics:")
    for method, metrics in filtered_results['method_metrics'].items():
        print(f"  {method}:")
        print(f"    Coverage Rate: {metrics['coverage_rate']:.4f}")
        print(f"    Avg Interval Width: {metrics['interval_width']:.4f}")
        print(f"    Valid N: {metrics['valid_n']}")

    return filtered_results

if __name__ == "__main__":
    main()