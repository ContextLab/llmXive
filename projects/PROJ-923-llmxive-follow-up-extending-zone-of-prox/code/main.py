"""
Batch Runner Script for ZPPO Comparative Analysis.

This script executes multiple independent simulation runs (both Static Baseline
and CAP-ZPPO) across different random seeds. It aggregates the resulting AUCC
values and prepares the data for the paired t-test analysis required by FR-008.

Workflow:
1. Loads configuration for the number of runs/seeds.
2. Iterates through seeds, running the Baseline simulation and saving to `data/metrics/baseline_results.csv`.
3. Iterates through seeds, running the CAP simulation and saving to `data/metrics/cap_results.csv`.
4. Aggregates all AUCC values into `data/metrics/aggregated_batch_results.csv`.
5. Prints a summary of the aggregated AUCC distributions.

Output:
    data/metrics/baseline_results.csv: Individual baseline run results.
    data/metrics/cap_results.csv: Individual CAP run results.
    data/metrics/aggregated_batch_results.csv: Combined dataset for statistical testing.
"""
import os
import sys
import argparse
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import load_config, get_config
from data.generators import generate_synthetic_rollout_log, set_seed
from data.loaders import load_mmlu_held_out_set
from loops.base_zppo import run_baseline_simulation
from loops.cap_zppo import run_cap_simulation
from analysis.metrics import calculate_metrics, save_metrics_to_csv
from utils.logging import get_logger, configure_logging
from utils.seeds import initialize_project_seed

logger = get_logger(__name__)


def run_single_baseline(seed: int, config: Any, output_dir: Path) -> Dict[str, Any]:
    """
    Executes a single Baseline ZPPO simulation run.

    Args:
        seed: Random seed for reproducibility.
        config: Loaded configuration object.
        output_dir: Directory to save the specific run's metrics.

    Returns:
        Dictionary containing the metrics for this run.
    """
    logger.info(f"--- Starting Baseline Run with Seed: {seed} ---")
    initialize_project_seed(seed)

    # 1. Generate Synthetic Rollout Log
    rollout_data = generate_synthetic_rollout_log(
        num_samples=config.simulation.initial_buffer_size,
        seed=seed
    )

    # 2. Load Held-Out Data
    held_out_data = load_mmlu_held_out_set(
        subset_size=config.simulation.held_out_size,
        seed=seed
    )

    # 3. Run Baseline Simulation
    try:
        results = run_baseline_simulation(
            initial_rollout=rollout_data,
            held_out_data=held_out_data,
            config=config,
            seed=seed
        )
    except Exception as e:
        logger.error(f"Baseline simulation failed for seed {seed}: {e}")
        raise

    # 4. Calculate Metrics
    metrics = calculate_metrics(
        trajectory=results["trajectory"],
        final_accuracy=results["final_accuracy"],
        prompt_lengths=results.get("prompt_lengths", [])
    )

    # Add metadata
    metrics["seed"] = seed
    metrics["num_cycles"] = config.simulation.num_cycles
    metrics["algorithm"] = "Static-Baseline"
    metrics["run_type"] = "baseline"

    # 5. Save Individual Run
    run_output_path = output_dir / f"baseline_seed_{seed}.csv"
    save_metrics_to_csv(metrics, run_output_path)
    logger.info(f"Baseline run {seed} completed. AUCC: {metrics['aucc']:.4f}")

    return metrics


def run_single_cap(seed: int, config: Any, output_dir: Path) -> Dict[str, Any]:
    """
    Executes a single CAP-ZPPO simulation run.

    Args:
        seed: Random seed for reproducibility.
        config: Loaded configuration object.
        output_dir: Directory to save the specific run's metrics.

    Returns:
        Dictionary containing the metrics for this run.
    """
    logger.info(f"--- Starting CAP Run with Seed: {seed} ---")
    initialize_project_seed(seed)

    # 1. Generate Synthetic Rollout Log
    rollout_data = generate_synthetic_rollout_log(
        num_samples=config.simulation.initial_buffer_size,
        seed=seed
    )

    # 2. Load Held-Out Data
    held_out_data = load_mmlu_held_out_set(
        subset_size=config.simulation.held_out_size,
        seed=seed
    )

    # 3. Run CAP Simulation
    try:
        results = run_cap_simulation(
            initial_rollout=rollout_data,
            held_out_data=held_out_data,
            config=config,
            seed=seed
        )
    except Exception as e:
        logger.error(f"CAP simulation failed for seed {seed}: {e}")
        raise

    # 4. Calculate Metrics
    metrics = calculate_metrics(
        trajectory=results["trajectory"],
        final_accuracy=results["final_accuracy"],
        prompt_lengths=results.get("prompt_lengths", [])
    )

    # Add metadata
    metrics["seed"] = seed
    metrics["num_cycles"] = config.simulation.num_cycles
    metrics["algorithm"] = "CAP-ZPPO"
    metrics["run_type"] = "cap"

    # 5. Save Individual Run
    run_output_path = output_dir / f"cap_seed_{seed}.csv"
    save_metrics_to_csv(metrics, run_output_path)
    logger.info(f"CAP run {seed} completed. AUCC: {metrics['aucc']:.4f}")

    return metrics


def aggregate_results(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Aggregates all individual run results into a single CSV file.

    Args:
        results: List of metric dictionaries from all runs.
        output_path: Path to the aggregated CSV file.
    """
    logger.info(f"Aggregating {len(results)} results into {output_path}...")
    if not results:
        logger.warning("No results to aggregate.")
        return

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to CSV
    fieldnames = list(results[0].keys())
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    logger.info("Aggregation complete.")


def main():
    """
    Main entry point for the Batch Runner.
    Executes multiple simulations and aggregates results for statistical analysis.
    """
    # Parse arguments
    parser = argparse.ArgumentParser(description="Batch Runner for ZPPO Comparative Analysis")
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to the configuration file"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/metrics",
        help="Directory to store all output CSV files"
    )
    parser.add_argument(
        "--num-runs",
        type=int,
        default=None,
        help="Override the number of runs (seeds) from config"
    )
    parser.add_argument(
        "--seeds",
        type=str,
        default=None,
        help="Comma-separated list of specific seeds to run (e.g., 42,43,44). Overrides --num-runs."
    )
    args = parser.parse_args()

    # Initialize logging
    configure_logging(level="INFO")
    logger.info("Starting Batch Runner for ZPPO Analysis")

    # Load configuration
    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)

    config = load_config(config_path)
    logger.info(f"Loaded configuration from {config_path}")

    # Determine seeds to run
    if args.seeds:
        seeds_to_run = [int(s.strip()) for s in args.seeds.split(',')]
        logger.info(f"Running specific seeds: {seeds_to_run}")
    else:
        num_runs = args.num_runs if args.num_runs is not None else config.simulation.num_runs
        # Generate sequential seeds starting from config seed + offset or just 0..N
        base_seed = config.simulation.seed
        seeds_to_run = [base_seed + i for i in range(num_runs)]
        logger.info(f"Running {num_runs} sequential runs starting from seed {base_seed}")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_results = []

    # --- Run Baseline Simulations ---
    logger.info("=== Starting Baseline Simulations ===")
    for seed in seeds_to_run:
        try:
            metrics = run_single_baseline(seed, config, output_dir)
            all_results.append(metrics)
        except Exception as e:
            logger.error(f"Skipping baseline seed {seed} due to error: {e}")
            # Continue with other seeds even if one fails

    # --- Run CAP Simulations ---
    logger.info("=== Starting CAP Simulations ===")
    for seed in seeds_to_run:
        try:
            metrics = run_single_cap(seed, config, output_dir)
            all_results.append(metrics)
        except Exception as e:
            logger.error(f"Skipping CAP seed {seed} due to error: {e}")
            # Continue with other seeds even if one fails

    # --- Aggregate Results ---
    aggregated_path = output_dir / "aggregated_batch_results.csv"
    aggregate_results(all_results, aggregated_path)

    # --- Summary ---
    logger.info("=== Batch Run Summary ===")
    baseline_auc = [r['aucc'] for r in all_results if r.get('algorithm') == 'Static-Baseline']
    cap_auc = [r['aucc'] for r in all_results if r.get('algorithm') == 'CAP-ZPPO']

    if baseline_auc:
        logger.info(f"Baseline Runs: {len(baseline_auc)}, Avg AUCC: {sum(baseline_auc)/len(baseline_auc):.4f}")
    if cap_auc:
        logger.info(f"CAP Runs: {len(cap_auc)}, Avg AUCC: {sum(cap_auc)/len(cap_auc):.4f}")

    logger.info(f"All results saved to: {aggregated_path}")
    logger.info("Batch runner completed successfully.")

    return 0


if __name__ == "__main__":
    sys.exit(main())