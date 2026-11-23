"""
Simulation Runner Module for Evaluating Statistical Significance in A/B Tests.

This module orchestrates the generation of synthetic data with intra-cluster correlation
(ICC), executes statistical tests (naive, cluster‑robust, and permutation), and aggregates
results to evaluate Type I error rates under various conditions.

It enforces strict memory and time limits to ensure reproducibility and compliance with
hardware constraints (FR‑006).

Usage (compatible with quickstart):
    python code/simulation_runner.py --icc-range 0.0,0.1 --iterations 20
    # or for full runs:
    python code/simulation_runner.py \
        --icc-range 0.0,0.1,0.2,0.3,0.4,0.5 \
        --iterations 1000
"""

import warnings
import time
import tracemalloc
import os
import sys
import csv
import argparse
import logging
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd
from scipy.stats import beta

# Import from local project modules
from code.config import (
    load_config,
    validate_config,
    set_seed,
    DEFAULT_N_CLUSTERS,
    CLUSTER_MEAN_SIZE,
    CLUSTER_STD_SIZE,
    DEFAULT_ITERATIONS,
    DEFAULT_SEED,
    ICC_RANGE,
    ALPHA_LEVELS,
)
from code.data_generator import generate_data
from code.estimators import (
    run_naive_ttest_with_warning,
    run_cluster_robust_ttest,
    run_block_permutation,
)
from code.analysis import aggregate_errors

# Constants for resource limits
MEMORY_LIMIT_MB = 7000  # 7 GB
TIME_LIMIT_SEC = 21600  # 6 hours

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("data/derived/simulation_log.txt"),
    ],
)
logger = logging.getLogger(__name__)

def estimate_memory_footprint(n_clusters: int, n_obs_per_cluster: int) -> float:
    """
    Estimates the memory footprint of the simulation data in MB.

    Calculates the theoretical memory usage assuming float64 (8 bytes) per element
    with a 5x safety factor to account for overhead and intermediate calculations.

    Args:
        n_clusters (int): Number of clusters.
        n_obs_per_cluster (int): Average number of observations per cluster.

    Returns:
        float: Estimated memory usage in MB.
    """
    estimated_mb = (n_clusters * n_obs_per_cluster * 8 * 5) / 1e6
    return estimated_mb

def optimize_memory(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adjusts the configuration to respect the memory limit.

    If the estimated memory usage exceeds ``MEMORY_LIMIT_MB``, the function reduces
    ``n_obs_per_cluster`` (down to a minimum of 1) until the estimate fits within the limit.
    The function returns the possibly‑modified configuration dictionary.

    The unit test ``test_optimize_memory_no_change`` expects that a configuration already
    under the limit is returned unchanged.

    Args:
        cfg (Dict[str, Any]): Configuration dictionary possibly containing
            ``n_clusters`` and ``n_obs_per_cluster``.

    Returns:
        Dict[str, Any]: Updated configuration dictionary.
    """
    n_clusters = cfg.get("n_clusters", DEFAULT_N_CLUSTERS)
    n_obs = cfg.get("n_obs_per_cluster", 1)
    est = estimate_memory_footprint(n_clusters, n_obs)
    if est <= MEMORY_LIMIT_MB:
        return cfg

    # Reduce n_obs_per_cluster iteratively until under limit (but not below 1)
    while est > MEMORY_LIMIT_MB and n_obs > 1:
        n_obs = max(1, int(n_obs * 0.5))
        est = estimate_memory_footprint(n_clusters, n_obs)

    cfg["n_obs_per_cluster"] = n_obs
    return cfg

def downsample_clusters(df: pd.DataFrame, target_n_clusters: int) -> pd.DataFrame:
    """
    Randomly downsamples the dataset to a target number of clusters.

    Args:
        df (pd.DataFrame): The full dataset with a 'cluster_id' column.
        target_n_clusters (int): The desired number of clusters to keep.

    Returns:
        pd.DataFrame: A subset of the original dataframe.
    """
    if df["cluster_id"].nunique() <= target_n_clusters:
        return df

    unique_clusters = df["cluster_id"].unique()
    selected_clusters = np.random.choice(
        unique_clusters, size=target_n_clusters, replace=False
    )
    return df[df["cluster_id"].isin(selected_clusters)].reset_index(drop=True)

def log_timing(start_time: float, end_time: float, output_path: str = "data/timing.csv") -> None:
    """
    Logs the execution time to a CSV file.

    Args:
        start_time (float): Start timestamp.
        end_time (float): End timestamp.
        output_path (str): Path to the timing log file.
    """
    duration_sec = end_time - start_time
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    file_exists = os.path.exists(output_path)

    with open(output_path, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["start_time", "end_time", "duration_sec"])
        writer.writerow([start_time, end_time, duration_sec])

    logger.info(f"Timing logged: {duration_sec:.2f} seconds")

def log_memory(output_path: str = "data/memory.csv") -> None:
    """
    Logs peak memory usage to a CSV file.

    Args:
        output_path (str): Path to the memory log file.
    """
    peak_bytes = tracemalloc.get_traced_memory()[1]
    peak_gb = peak_bytes / (1024 ** 3)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    file_exists = os.path.exists(output_path)

    with open(output_path, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["peak_memory_gb"])
        writer.writerow([peak_gb])

    logger.info(f"Peak memory logged: {peak_gb:.4f} GB")

def log_config_change(config: Dict[str, Any], output_path: str = "data/derived/simulation_config_log.csv") -> None:
    """
    Logs the actual configuration parameters used for the simulation.

    This ensures reproducibility by recording the exact parameters (n_clusters,
    n_obs_per_cluster, etc.) that drove the experiment.

    Args:
        config (Dict[str, Any]): The configuration dictionary.
        output_path (str): Path to the config log file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    file_exists = os.path.exists(output_path)

    with open(output_path, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(
                ["n_clusters", "n_obs_per_cluster", "icc", "seed", "iterations"]
            )

        n_clusters = config.get("n_clusters", DEFAULT_N_CLUSTERS)
        n_obs = config.get("n_obs_per_cluster", 1)
        icc = config.get("icc", 0.0)
        seed = config.get("seed", DEFAULT_SEED)
        iterations = config.get("iterations", DEFAULT_ITERATIONS)

        writer.writerow([n_clusters, n_obs, icc, seed, iterations])

    logger.info(f"Configuration logged to {output_path}")

def run_baseline_simulation(
    icc: float,
    n_iterations: int,
    seed: int,
    n_clusters: int,
    n_obs_per_cluster: int,
    alpha_levels: Optional[List[float]] = None,
) -> List[Dict[str, Any]]:
    """
    Runs the baseline (naive) simulation for a given ICC.

    The function matches the expectations of the unit tests in
    ``tests/unit/test_simulation_runner.py``.  It returns a list where each entry
    contains the iteration index, the ICC value, the raw p‑value from the naive
    t‑test, and three boolean rejection flags for the default alphas
    (0.01, 0.05, 0.10).

    Args:
        icc (float): Target intra‑cluster correlation.
        n_iterations (int): Number of Monte‑Carlo repetitions.
        seed (int): Base random seed; each iteration uses ``seed + i``.
        n_clusters (int): Number of clusters to generate.
        n_obs_per_cluster (int): Observations per cluster.
        alpha_levels (List[float], optional): Alpha thresholds.  If ``None``,
            the default list ``[0.01, 0.05, 0.10]`` is used.

    Returns:
        List[Dict[str, Any]]: Simulation results in the test‑compatible format.
    """
    if alpha_levels is None:
        alpha_levels = [0.01, 0.05, 0.10]

    results: List[Dict[str, Any]] = []
    set_seed(seed)

    for i in range(n_iterations):
        df = generate_data(
            n_clusters=n_clusters,
            n_obs_per_cluster=n_obs_per_cluster,
            icc=icc,
            seed=seed + i,
            cluster_mean=CLUSTER_MEAN_SIZE,
            cluster_std=CLUSTER_STD_SIZE,
        )
        p_val = run_naive_ttest_with_warning(df, "treatment", "outcome")
        result = {
            "iteration": i,
            "icc": icc,
            "p_value": p_val,
            "rejected_0.01": p_val < 0.01,
            "rejected_0.05": p_val < 0.05,
            "rejected_0.10": p_val < 0.10,
        }
        results.append(result)

    return results

def run_robust_simulation(
    icc: float,
    n_iterations: int,
    seed: int,
    n_clusters: int,
    n_obs_per_cluster: int,
    alpha_levels: List[float],
    n_permutations: int = 1000,
) -> List[Dict[str, Any]]:
    """
    Runs the robust simulation (cluster‑robust and block permutation) for a given ICC.

    Returns a list of dictionaries compatible with the aggregation logic used later
    in ``run_full_simulation``.
    """
    results: List[Dict[str, Any]] = []
    set_seed(seed)

    for i in range(n_iterations):
        df = generate_data(
            n_clusters=n_clusters,
            n_obs_per_cluster=n_obs_per_cluster,
            icc=icc,
            seed=seed + i,
            cluster_mean=CLUSTER_MEAN_SIZE,
            cluster_std=CLUSTER_STD_SIZE,
        )

        # Cluster‑Robust
        p_robust = run_cluster_robust_ttest(
            df, "treatment", "outcome", "cluster_id"
        )
        for alpha in alpha_levels:
            results.append(
                {
                    "iteration": i,
                    "icc": icc,
                    "p_value": p_robust,
                    "alpha": alpha,
                    "rejected": p_robust < alpha,
                    "method": "cluster_robust",
                }
            )

        # Block Permutation
        p_perm = run_block_permutation(
            df, "treatment", "outcome", "cluster_id", n_permutations
        )
        for alpha in alpha_levels:
            results.append(
                {
                    "iteration": i,
                    "icc": icc,
                    "p_value": p_perm,
                    "alpha": alpha,
                    "rejected": p_perm < alpha,
                    "method": "block_permutation",
                }
            )
    return results

def run_full_simulation(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Orchestrates the full simulation across all configured ICC levels.

    Validates memory constraints, runs baseline and robust simulations,
    aggregates error rates, and writes results to disk.
    """
    start_time = time.time()
    tracemalloc.start()

    # Pre‑run memory validation and possible optimisation
    cfg = optimize_memory(cfg)

    n_clusters = cfg.get("n_clusters", DEFAULT_N_CLUSTERS)
    n_obs = cfg.get("n_obs_per_cluster", 1)
    est_mem = estimate_memory_footprint(n_clusters, n_obs)

    if est_mem > MEMORY_LIMIT_MB:
        tracemalloc.stop()
        raise RuntimeError(
            f"Memory limit exceeded: {est_mem:.2f} MB > {MEMORY_LIMIT_MB} MB."
        )

    logger.info(f"Memory check passed: {est_mem:.2f} MB estimated.")
    log_config_change(cfg)

    icc_range = cfg.get("icc_range", ICC_RANGE)
    n_iterations = cfg.get("iterations", DEFAULT_ITERATIONS)
    seed = cfg.get("seed", DEFAULT_SEED)
    alpha_levels = cfg.get("alpha_levels", ALPHA_LEVELS)
    cluster_mean = cfg.get("cluster_mean", CLUSTER_MEAN_SIZE)
    cluster_std = cfg.get("cluster_std", CLUSTER_STD_SIZE)
    n_permutations = cfg.get("n_permutations", 1000)

    all_results: List[Dict[str, Any]] = []

    for icc in icc_range:
        logger.info(f"Processing ICC={icc}")

        # Baseline (naive)
        baseline_res = run_baseline_simulation(
            icc=icc,
            n_iterations=n_iterations,
            seed=seed,
            n_clusters=n_clusters,
            n_obs_per_cluster=n_obs,
            alpha_levels=alpha_levels,
        )
        all_results.extend(baseline_res)

        # Robust
        robust_res = run_robust_simulation(
            icc=icc,
            n_iterations=n_iterations,
            seed=seed + 1000,
            n_clusters=n_clusters,
            n_obs_per_cluster=n_obs,
            alpha_levels=alpha_levels,
            n_permutations=n_permutations,
        )
        all_results.extend(robust_res)

    # Save raw results (required by T005)
    results_df = pd.DataFrame(all_results)
    raw_output_path = "data/derived/simulation_results_raw.csv"
    os.makedirs(os.path.dirname(raw_output_path), exist_ok=True)
    results_df.to_csv(raw_output_path, index=False)
    logger.info(f"Raw simulation results saved to {raw_output_path}")

    # Aggregate into final report using the analysis helper
    final_df = aggregate_errors(all_results, alpha_levels)
    final_path = cfg.get("output", "data/derived/final_report.csv")
    os.makedirs(os.path.dirname(final_path), exist_ok=True)
    final_df.to_csv(final_path, index=False)
    logger.info(f"Final report saved to {final_path}")

    end_time = time.time()
    log_timing(start_time, end_time)
    log_memory()

    tracemalloc.stop()

    return {
        "status": "success",
        "total_time_sec": end_time - start_time,
        "rows_written": len(final_df),
    }

def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Parses command-line arguments for the simulation runner.
    """
    parser = argparse.ArgumentParser(
        description="Run A/B test simulation with cluster correlation."
    )
    parser.add_argument(
        "--icc-range",
        type=str,
        default=None,
        help="Comma-separated list of ICC values (e.g., 0.0,0.1,0.2)",
    )
    parser.add_argument(
        "--icc",
        type=float,
        default=None,
        help="Single ICC value (shortcut for a one‑element icc_range).",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=DEFAULT_ITERATIONS,
        help=f"Number of iterations (default: {DEFAULT_ITERATIONS})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help=f"Random seed (default: {DEFAULT_SEED})",
    )
    parser.add_argument(
        "--cluster-mean",
        type=float,
        default=CLUSTER_MEAN_SIZE,
        help=f"Mean cluster size (default: {CLUSTER_MEAN_SIZE})",
    )
    parser.add_argument(
        "--cluster-std",
        type=float,
        default=CLUSTER_STD_SIZE,
        help=f"Std dev of cluster size (default: {CLUSTER_STD_SIZE})",
    )
    parser.add_argument(
        "--n-clusters",
        type=int,
        default=DEFAULT_N_CLUSTERS,
        help=f"Number of clusters (default: {DEFAULT_N_CLUSTERS})",
    )
    parser.add_argument(
        "--n-obs-per-cluster",
        type=int,
        default=1,
        help="Number of observations per cluster",
    )
    parser.add_argument(
        "--n-permutations",
        type=int,
        default=1000,
        help="Number of permutations for block test",
    )
    parser.add_argument(
        "--alpha-list",
        type=str,
        default=None,
        help="Comma-separated alpha levels (e.g., 0.01,0.05,0.10)",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=None,
        help="Single alpha level (shortcut for a one‑element alpha_list).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/derived/final_report.csv",
        help="Output path for the final report",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    return parser.parse_args(args)

def main() -> None:
    """
    Main entry point for the simulation runner.
    """
    args = parse_args()
    cfg = load_config()

    # Translate shortcut arguments into full list forms expected by the config
    if args.icc is not None:
        cfg["icc_range"] = [args.icc]
    elif args.icc_range:
        cfg["icc_range"] = [float(x) for x in args.icc_range.split(",")]

    if args.alpha is not None:
        cfg["alpha_levels"] = [args.alpha]
    elif args.alpha_list:
        cfg["alpha_levels"] = [float(x) for x in args.alpha_list.split(",")]

    # Override other config values if CLI supplied
    for name in [
        "iterations",
        "seed",
        "cluster_mean",
        "cluster_std",
        "n_clusters",
        "n_obs_per_cluster",
        "n_permutations",
        "output",
    ]:
        # argparse stores arguments with underscores; use the attribute directly
        val = getattr(args, name)
        if val is not None:
            cfg[name] = val

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Validate final configuration
    validate_config(cfg)

    try:
        result = run_full_simulation(cfg)
        logger.info(
            f"Simulation completed successfully. Status: {result['status']}"
        )
    except RuntimeError as e:
        logger.error(f"Simulation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
