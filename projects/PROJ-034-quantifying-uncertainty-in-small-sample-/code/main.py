import os
import sys
import json
import time
import argparse
from typing import List, Dict, Any, Tuple

from simulation.config import SimulationConfig
from simulation.engine import generate_dataset, calculate_vif, save_dataset_instance, DatasetInstance
from models.ols import OLSModel, fit_ols_and_get_intervals
from models.bootstrap import BootstrapModel, fit_bootstrap_and_get_intervals
from models.bayesian import BayesianModel, fit_bayesian_and_get_intervals
from metrics.coverage import check_coverage, calculate_coverage_metrics, aggregate_coverage_by_method
from simulation.logging_utils import ensure_log_directory, log_simulation_run

def run_single_replication(config: SimulationConfig, seed: int) -> Dict[str, Any]:
    """
    Run a single Monte Carlo replication.
    Returns a dictionary containing results for OLS, Bootstrap, and Bayesian methods.
    """
    np.random.seed(seed)
    start_time = time.time()

    # Generate dataset
    try:
        dataset: DatasetInstance = generate_dataset(config)
    except Exception as e:
        return {
            "seed": seed,
            "status": "failed_generation",
            "error": str(e),
            "duration": time.time() - start_time
        }

    # Calculate VIF
    vif_values = calculate_vif(dataset.X)
    vif_max = max(vif_values) if vif_values else 0.0
    dataset.metadata["vif_max"] = vif_max

    # Check VIF threshold
    vif_exceeded = vif_max > 10.0
    dataset.metadata["vif_exceeded"] = vif_exceeded

    results = {
        "seed": seed,
        "N": config.N,
        "rho": config.rho,
        "vif_max": vif_max,
        "vif_exceeded": vif_exceeded,
        "true_beta": dataset.beta_true.tolist() if hasattr(dataset.beta_true, 'tolist') else dataset.beta_true,
        "methods": {}
    }

    # OLS
    ols_model = OLSModel()
    try:
        ols_intervals, ols_stats = fit_ols_and_get_intervals(ols_model, dataset.X, dataset.y)
        results["methods"]["ols"] = {
            "intervals": [
                {"beta_idx": i, "lower": float(l), "upper": float(u)}
                for i, (l, u) in enumerate(ols_intervals)
            ],
            "stats": ols_stats
        }
    except Exception as e:
        results["methods"]["ols"] = {"error": str(e)}

    # Bootstrap
    boot_model = BootstrapModel(n_bootstrap=1000)
    try:
        boot_intervals, boot_stats = fit_bootstrap_and_get_intervals(boot_model, dataset.X, dataset.y)
        results["methods"]["bootstrap"] = {
            "intervals": [
                {"beta_idx": i, "lower": float(l), "upper": float(u)}
                for i, (l, u) in enumerate(boot_intervals)
            ],
            "stats": boot_stats
        }
    except Exception as e:
        results["methods"]["bootstrap"] = {"error": str(e)}

    # Bayesian
    bayes_model = BayesianModel()
    try:
        bayes_intervals, bayes_stats = fit_bayesian_and_get_intervals(bayes_model, dataset.X, dataset.y)
        results["methods"]["bayesian"] = {
            "intervals": [
                {"beta_idx": i, "lower": float(l), "upper": float(u)}
                for i, (l, u) in enumerate(bayes_intervals)
            ],
            "stats": bayes_stats
        }
    except Exception as e:
        results["methods"]["bayesian"] = {"error": str(e)}

    results["duration"] = time.time() - start_time
    return results

def run_full_simulation(config: SimulationConfig, n_replications: int = 200, output_dir: str = "data/results") -> List[Dict[str, Any]]:
    """
    Run the full Monte Carlo simulation.
    """
    ensure_log_directory(output_dir)
    all_results = []
    start_total = time.time()

    for i in range(n_replications):
        seed = config.base_seed + i
        print(f"Running replication {i+1}/{n_replications} (seed={seed})...")
        result = run_single_replication(config, seed)
        all_results.append(result)

        # Log individual run
        log_simulation_run(result, output_dir)

    print(f"Total simulation time: {time.time() - start_total:.2f}s")
    return all_results

def filter_and_save_results(results: List[Dict[str, Any]], output_path: str = "data/results/filtered_metrics.json"):
    """
    Filter results to exclude runs with R-hat > 1.05 or VIF > 10.
    Calculate coverage metrics on the filtered set and save to JSON.
    """
    filtered_runs = []
    excluded_runs = []

    for run in results:
        if run.get("status") == "failed_generation":
            excluded_runs.append({"seed": run.get("seed"), "reason": "generation_failed"})
            continue

        vif_exceeded = run.get("vif_exceeded", False)
        r_hat_exceeded = False

        # Check Bayesian R-hat if available
        if "bayesian" in run.get("methods", {}) and "stats" in run["methods"]["bayesian"]:
            r_hat = run["methods"]["bayesian"]["stats"].get("r_hat")
            if r_hat is not None and r_hat > 1.05:
                r_hat_exceeded = True

        if vif_exceeded or r_hat_exceeded:
            excluded_runs.append({
                "seed": run.get("seed"),
                "reason": "vif_exceeded" if vif_exceeded else "r_hat_exceeded",
                "vif_max": run.get("vif_max"),
                "r_hat": run.get("methods", {}).get("bayesian", {}).get("stats", {}).get("r_hat")
            })
        else:
            filtered_runs.append(run)

    print(f"Total runs: {len(results)}")
    print(f"Excluded runs: {len(excluded_runs)}")
    print(f"Filtered runs (valid): {len(filtered_runs)}")

    if len(filtered_runs) == 0:
        print("WARNING: No valid runs remaining after filtering.")
        filtered_metrics = {
            "total_attempts": len(results),
            "valid_n": 0,
            "excluded_count": len(excluded_runs),
            "excluded_details": excluded_runs,
            "coverage_by_method": {},
            "interval_widths_by_method": {}
        }
    else:
        # Calculate coverage metrics
        coverage_by_method = {}
        width_by_method = {}

        methods = ["ols", "bootstrap", "bayesian"]
        for method in methods:
            covered_counts = []
            widths = []

            for run in filtered_runs:
                if method not in run.get("methods", {}) or "error" in run["methods"][method]:
                    continue

                intervals = run["methods"][method].get("intervals", [])
                true_beta = run.get("true_beta", [])

                if not intervals or not true_beta:
                    continue

                # Check coverage for each coefficient
                for i, interval in enumerate(intervals):
                    lower = interval["lower"]
                    upper = interval["upper"]
                    beta_true = true_beta[i] if i < len(true_beta) else None

                    if beta_true is not None:
                        covered = check_coverage(lower, upper, beta_true)
                        covered_counts.append(covered)
                        widths.append(upper - lower)

            if covered_counts:
                coverage_rate = sum(covered_counts) / len(covered_counts)
                avg_width = sum(widths) / len(widths)
                coverage_by_method[method] = {
                    "coverage_rate": float(coverage_rate),
                    "valid_samples": len(covered_counts),
                    "avg_interval_width": float(avg_width)
                }
            else:
                coverage_by_method[method] = {
                    "coverage_rate": None,
                    "valid_samples": 0,
                    "avg_interval_width": None,
                    "error": "No valid intervals to compute coverage"
                }

        filtered_metrics = {
            "total_attempts": len(results),
            "valid_n": len(filtered_runs),
            "excluded_count": len(excluded_runs),
            "excluded_details": excluded_runs,
            "coverage_by_method": coverage_by_method,
            "interval_widths_by_method": width_by_method
        }

    # Save to JSON
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(filtered_metrics, f, indent=2)

    print(f"Filtered metrics saved to {output_path}")
    return filtered_metrics

def main():
    parser = argparse.ArgumentParser(description="Run uncertainty quantification simulation")
    parser.add_argument("--n-replications", type=int, default=200, help="Number of Monte Carlo replications")
    parser.add_argument("--output-dir", type=str, default="data/results", help="Output directory for results")
    parser.add_argument("--config", type=str, default="data/config/simulation_config.json", help="Path to simulation config")
    args = parser.parse_args()

    # Load config
    if os.path.exists(args.config):
        with open(args.config, "r") as f:
            config_dict = json.load(f)
        config = SimulationConfig(**config_dict)
    else:
        # Default config for testing
        config = SimulationConfig(
            N=30,
            n_predictors=3,
            rho=0.5,
            noise_std=1.0,
            true_beta=[1.0, 2.0, 3.0],
            base_seed=42
        )

    print(f"Starting simulation with N={config.N}, rho={config.rho}, n_replications={args.n_replications}")

    # Run simulation
    results = run_full_simulation(config, args.n_replications, args.output_dir)

    # Filter and save results
    filter_and_save_results(results, os.path.join(args.output_dir, "filtered_metrics.json"))

    # Also save raw results for debugging
    raw_output = os.path.join(args.output_dir, "raw_results.json")
    with open(raw_output, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Raw results saved to {raw_output}")

if __name__ == "__main__":
    main()