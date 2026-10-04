"""
Simulation runner with memory and time constraints.

Implements baseline and robust simulation loops with dynamic down-sampling
and performance monitoring.
"""
import warnings
import time
import tracemalloc
import os
import sys
import csv
import logging
import argparse
from typing import List, Dict, Any, Optional, Tuple

# Add project root to path if running as script
if __name__ == "__main__" and "code" not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd

from code.config import validate_config, load_config, set_seed, parse_cli_args
from code.data_generator import generate_data
from code.estimators import run_naive_ttest_with_warning, run_cluster_robust_ttest, run_block_permutation
from code.analysis import aggregate_errors

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

MEMORY_LIMIT_GB = 7.0
TIME_LIMIT_SEC = 21600  # 6 hours
MIN_CLUSTERS = 50

def estimate_memory_footprint(n_clusters: int, n_obs_per_cluster: int, factor: float = 5.0) -> float:
    """
    Estimate memory footprint in MB.

    Formula: n_clusters * n_obs_per_cluster * 8 bytes * factor / (1024 * 1024)
    """
    bytes_per_obs = 8  # float64
    total_bytes = n_clusters * n_obs_per_cluster * bytes_per_obs * factor
    return total_bytes / (1024 * 1024)

def downsample_clusters(n_clusters: int, n_obs_per_cluster: int, max_mb: float = 7000.0) -> Tuple[int, int]:
    """
    Down-sample clusters and observations if memory limit is exceeded.

    Returns (new_n_clusters, new_n_obs_per_cluster).
    Raises RuntimeError if down-sampling violates statistical validity.
    """
    estimated_mb = estimate_memory_footprint(n_clusters, n_obs_per_cluster)

    if estimated_mb <= max_mb:
        return n_clusters, n_obs_per_cluster

    # Retry 1: Halve n_obs_per_cluster
    new_n_obs = n_obs_per_cluster // 2
    if new_n_obs < 1:
        new_n_obs = 1
    estimated_mb = estimate_memory_footprint(n_clusters, new_n_obs)
    if estimated_mb <= max_mb:
        return n_clusters, new_n_obs

    # Retry 2: Halve n_clusters
    new_n_clusters = n_clusters // 2
    if new_n_clusters < MIN_CLUSTERS:
        raise RuntimeError(
            f"Memory limit exceeded: 7GB. Down-sampling would violate statistical validity (n_clusters < {MIN_CLUSTERS})."
        )
    estimated_mb = estimate_memory_footprint(new_n_clusters, new_n_obs)
    if estimated_mb <= max_mb:
        return new_n_clusters, new_n_obs

    # Retry 3: Halve n_obs_per_cluster again (if not already 1)
    if new_n_obs > 1:
        new_n_obs = new_n_obs // 2
        estimated_mb = estimate_memory_footprint(new_n_clusters, new_n_obs)
        if estimated_mb <= max_mb:
            return new_n_clusters, new_n_obs

    raise RuntimeError(
        f"Memory limit exceeded: 7GB. Down-sampling failed. "
        f"Estimated MB: {estimated_mb:.2f} with n_clusters={new_n_clusters}, n_obs={new_n_obs}."
    )

def log_timing(start_time: float, output_path: str = "data/timing.csv") -> None:
    """Log wall-clock time to CSV."""
    duration = time.time() - start_time
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    file_exists = os.path.exists(output_path)

    with open(output_path, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "duration_sec"])
        writer.writerow([timestamp, duration])

    logger.info(f"Timing logged: {duration:.2f} seconds")

def log_memory(output_path: str = "data/memory.csv") -> None:
    """Log peak memory usage to CSV."""
    current, peak = tracemalloc.get_traced_memory()
    peak_gb = peak / (1024 * 1024 * 1024)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    file_exists = os.path.exists(output_path)

    with open(output_path, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "peak_memory_gb"])
        writer.writerow([timestamp, peak_gb])

    logger.info(f"Memory logged: {peak_gb:.4f} GB")

def log_config_change(cfg: Dict[str, Any], output_path: str = "data/derived/simulation_config_log.csv") -> None:
    """Log actual configuration parameters used for reproducibility."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    file_exists = os.path.exists(output_path)

    with open(output_path, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "n_clusters", "n_obs_per_cluster", "icc", "seed"])
        writer.writerow([
            time.strftime("%Y-%m-%d %H:%M:%S"),
            cfg.get("n_clusters", cfg.get("n_clusters", 100)),
            cfg.get("n_obs_per_cluster", cfg.get("n_obs_per_cluster", 12)),
            cfg.get("icc"),
            cfg.get("seed")
        ])

def run_baseline_simulation(
    icc: float,
    n_iterations: int,
    seed: int,
    cluster_mean: float = 12.5,
    cluster_std: float = 8.2,
    n_clusters: Optional[int] = None,
    n_obs_per_cluster: Optional[int] = None
) -> List[Dict]:
    """
    Run baseline simulation for a single ICC level.

    Returns a list of result dictionaries.
    """
    if n_clusters is None:
        n_clusters = 100
    if n_obs_per_cluster is None:
        n_obs_per_cluster = 12

    # Check memory and down-sample if necessary
    try:
        n_clusters, n_obs_per_cluster = downsample_clusters(n_clusters, n_obs_per_cluster)
    except RuntimeError as e:
        logger.error(str(e))
        raise

    # Log config change if down-sampling occurred
    log_config_change({
        "n_clusters": n_clusters,
        "n_obs_per_cluster": n_obs_per_cluster,
        "icc": icc,
        "seed": seed
    })

    results = []
    start_time = time.time()

    for i in range(n_iterations):
        # Time limit check
        if time.time() - start_time > TIME_LIMIT_SEC:
            raise RuntimeError("Time limit exceeded: 6 hours.")

        # Memory check
        current, peak = tracemalloc.get_traced_memory()
        if peak > MEMORY_LIMIT_GB * 1024 * 1024 * 1024:
            raise RuntimeError("Memory limit exceeded: 7GB. Down-sampling failed.")

        try:
            data = generate_data(
                n_clusters=n_clusters,
                n_obs_per_cluster=n_obs_per_cluster,
                icc=icc,
                seed=seed + i,
                cluster_mean=cluster_mean,
                cluster_std=cluster_std
            )
            p_value = run_naive_ttest_with_warning(data, "treatment", "outcome")
            results.append({
                "iteration": i,
                "icc": icc,
                "p_value": p_value,
                "rejected": p_value < 0.05
            })
        except Exception as e:
            logger.warning(f"Iteration {i} failed: {e}. Skipping.")
            continue

    return results

def run_robust_simulation(
    icc: float,
    n_iterations: int,
    seed: int,
    cluster_mean: float = 12.5,
    cluster_std: float = 8.2,
    n_clusters: Optional[int] = None,
    n_obs_per_cluster: Optional[int] = None,
    n_permutations: int = 1000
) -> List[Dict]:
    """
    Run robust simulation for a single ICC level.

    Returns a list of result dictionaries for naive, cluster-robust, and block permutation.
    """
    if n_clusters is None:
        n_clusters = 100
    if n_obs_per_cluster is None:
        n_obs_per_cluster = 12

    try:
        n_clusters, n_obs_per_cluster = downsample_clusters(n_clusters, n_obs_per_cluster)
    except RuntimeError as e:
        logger.error(str(e))
        raise

    log_config_change({
        "n_clusters": n_clusters,
        "n_obs_per_cluster": n_obs_per_cluster,
        "icc": icc,
        "seed": seed
    })

    results = []
    start_time = time.time()

    for i in range(n_iterations):
        if time.time() - start_time > TIME_LIMIT_SEC:
            raise RuntimeError("Time limit exceeded: 6 hours.")

        current, peak = tracemalloc.get_traced_memory()
        if peak > MEMORY_LIMIT_GB * 1024 * 1024 * 1024:
            raise RuntimeError("Memory limit exceeded: 7GB. Down-sampling failed.")

        try:
            data = generate_data(
                n_clusters=n_clusters,
                n_obs_per_cluster=n_obs_per_cluster,
                icc=icc,
                seed=seed + i,
                cluster_mean=cluster_mean,
                cluster_std=cluster_std
            )

            # Naive
            p_naive = run_naive_ttest_with_warning(data, "treatment", "outcome")
            results.append({
                "iteration": i,
                "icc": icc,
                "method": "naive",
                "p_value": p_naive,
                "rejected": p_naive < 0.05
            })

            # Cluster-robust
            p_robust = run_cluster_robust_ttest(data, "treatment", "outcome", "cluster_id")
            results.append({
                "iteration": i,
                "icc": icc,
                "method": "cluster_robust",
                "p_value": p_robust,
                "rejected": p_robust < 0.05
            })

            # Block permutation
            p_perm = run_block_permutation(data, "treatment", "outcome", "cluster_id", n_permutations)
            results.append({
                "iteration": i,
                "icc": icc,
                "method": "block_permutation",
                "p_value": p_perm,
                "rejected": p_perm < 0.05
            })

        except Exception as e:
            logger.warning(f"Iteration {i} failed: {e}. Skipping.")
            continue

    return results

def run_full_simulation(
    icc_range: List[float],
    n_iterations: int,
    seed: int,
    cluster_mean: float = 12.5,
    cluster_std: float = 8.2,
    n_clusters: Optional[int] = None,
    n_obs_per_cluster: Optional[int] = None,
    n_permutations: int = 1000
) -> List[Dict]:
    """
    Run full simulation across ICC range.

    Returns a list of result dictionaries.
    """
    all_results = []
    start_time = time.time()

    for icc in icc_range:
        logger.info(f"Starting simulation for ICC={icc}")
        try:
            results = run_robust_simulation(
                icc=icc,
                n_iterations=n_iterations,
                seed=seed,
                cluster_mean=cluster_mean,
                cluster_std=cluster_std,
                n_clusters=n_clusters,
                n_obs_per_cluster=n_obs_per_cluster,
                n_permutations=n_permutations
            )
            all_results.extend(results)
        except Exception as e:
            logger.error(f"Simulation failed for ICC={icc}: {e}")
            continue

        log_timing(start_time)
        log_memory()

    return all_results

def parse_args(cli_args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run simulation with robust methods.")
    parser.add_argument("--icc-range", type=str, default="0.0,0.1,0.2,0.3,0.4,0.5")
    parser.add_argument("--iterations", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--cluster-mean", type=float, default=12.5)
    parser.add_argument("--cluster-std", type=float, default=8.2)
    parser.add_argument("--n-clusters", type=int, default=100)
    parser.add_argument("--n-obs-per-cluster", type=int, default=12)
    parser.add_argument("--n-permutations", type=int, default=1000)
    parser.add_argument("--output", type=str, default="data/derived/robust_results.csv")
    return parser.parse_args(cli_args)

def main():
    """Main entry point."""
    args = parse_args()
    cfg = load_config()
    cfg = parse_cli_args(args, cfg)
    validate_config(cfg)
    set_seed(cfg.get("seed", 42))

    icc_range = [float(x) for x in args.icc_range.split(",")]

    results = run_full_simulation(
        icc_range=icc_range,
        n_iterations=args.iterations,
        seed=args.seed,
        cluster_mean=args.cluster_mean,
        cluster_std=args.cluster_std,
        n_clusters=args.n_clusters,
        n_obs_per_cluster=args.n_obs_per_cluster,
        n_permutations=args.n_permutations
    )

    if results:
        df = pd.DataFrame(results)
        df.to_csv(args.output, index=False)
        logger.info(f"Results written to {args.output}")
    else:
        logger.warning("No results to write.")

if __name__ == "__main__":
    main()