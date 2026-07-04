import os
import sys
import json
import logging
import random
import csv
from pathlib import Path
from typing import List, Dict, Tuple, Any

import numpy as np

# Add project root to path if running directly
if "code" not in sys.path:
    project_root = Path(__file__).resolve().parent
    if (project_root / "code").exists():
        sys.path.insert(0, str(project_root))

from code.utils.logger import get_logger

logger = get_logger(__name__)

def load_importance_profiles(profiles_path: Path) -> List[Dict[str, Any]]:
    """
    Load importance profiles from CSV.
    Expected columns: window_id, feature_name, importance_score, rank
    Returns a list of dicts per row.
    """
    if not profiles_path.exists():
        raise FileNotFoundError(f"Importance profiles not found at {profiles_path}")

    profiles = []
    with open(profiles_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            row["window_id"] = int(row["window_id"])
            row["importance_score"] = float(row["importance_score"])
            row["rank"] = int(row["rank"])
            profiles.append(row)

    return profiles

def extract_window_rankings(profiles: List[Dict[str, Any]]) -> Dict[int, List[Tuple[str, float]]]:
    """
    Group profiles by window_id and return a dict:
    { window_id: [(feature_name, importance_score), ...] }
    Sorted by importance_score descending.
    """
    windows = {}
    for row in profiles:
        wid = row["window_id"]
        if wid not in windows:
            windows[wid] = []
        windows[wid].append((row["feature_name"], row["importance_score"]))

    # Sort each window's features by importance descending
    for wid in windows:
        windows[wid].sort(key=lambda x: x[1], reverse=True)

    return windows

def calculate_rank_correlation(ranks_a: List[str], ranks_b: List[str]) -> Tuple[float, float]:
    """
    Calculate Spearman rank correlation between two lists of feature names (ordered by importance).
    Returns (rho, p_value).
    Uses scipy.stats.spearmanr.
    """
    try:
        from scipy.stats import spearmanr
    except ImportError:
        raise ImportError("scipy is required for rank correlation. Install with: pip install scipy")

    # Create rank arrays (1-indexed rank for each feature in the list)
    # We assume both lists contain the same set of features
    feature_to_rank_a = {feat: i + 1 for i, feat in enumerate(ranks_a)}
    feature_to_rank_b = {feat: i + 1 for i, feat in enumerate(ranks_b)}

    all_features = list(ranks_a)  # Assuming same features
    ranks_a_array = [feature_to_rank_a[f] for f in all_features]
    ranks_b_array = [feature_to_rank_b[f] for f in all_features]

    rho, p_value = spearmanr(ranks_a_array, ranks_b_array)
    return float(rho), float(p_value)

def shuffle_windows_and_compute_rho(
    window_rankings: Dict[int, List[Tuple[str, float]]],
    rng_seed: int
) -> float:
    """
    Shuffle the chronological order of windows, re-calculate importance rankings
    (which remain the same per window, but the sequence of windows is permuted),
    then compute the Spearman correlation between consecutive shuffled windows.
    Returns the mean rho of the shuffled sequence.

    Note: Since importance rankings are intrinsic to each window's data,
    shuffling windows just changes the order of comparison. We calculate
    rho between window[i] and window[i+1] in the shuffled order.
    """
    rng = random.Random(rng_seed)

    # Extract window IDs and sort them chronologically first
    sorted_window_ids = sorted(window_rankings.keys())

    # Shuffle the window IDs
    shuffled_ids = sorted_window_ids.copy()
    rng.shuffle(shuffled_ids)

    # Calculate correlations between consecutive windows in shuffled order
    rhos = []
    for i in range(len(shuffled_ids) - 1):
        wid_current = shuffled_ids[i]
        wid_next = shuffled_ids[i + 1]

        ranks_current = [feat for feat, _ in window_rankings[wid_current]]
        ranks_next = [feat for feat, _ in window_rankings[wid_next]]

        # Ensure both windows have the same features
        if set(ranks_current) != set(ranks_next):
            logger.warning(f"Feature mismatch between window {wid_current} and {wid_next}. Skipping pair.")
            continue

        rho, _ = calculate_rank_correlation(ranks_current, ranks_next)
        rhos.append(rho)

    if not rhos:
        return 0.0

    return float(np.mean(rhos))

def run_null_baseline(
    profiles_path: Path,
    output_path: Path,
    n_runs: int = 100,
    base_seed: int = 42
) -> Dict[str, Any]:
    """
    Run the null model baseline:
    1. Load importance profiles.
    2. Extract window rankings.
    3. Shuffle window order multiple times.
    4. Calculate mean rho for each run.
    5. Return the distribution of mean rhos and the overall mean.

    Args:
        profiles_path: Path to importance_profiles.csv
        output_path: Path to save null_baseline.json
        n_runs: Number of shuffled runs
        base_seed: Base random seed

    Returns:
        Dict with 'mean_rho', 'std_rho', 'min_rho', 'max_rho', 'n_runs'
    """
    logger.info(f"Loading importance profiles from {profiles_path}")
    profiles = load_importance_profiles(profiles_path)

    logger.info("Extracting window rankings")
    window_rankings = extract_window_rankings(profiles)

    if len(window_rankings) < 2:
        logger.error("Not enough windows to calculate drift. Need at least 2 windows.")
        raise ValueError("Need at least 2 windows to calculate drift.")

    logger.info(f"Running {n_runs} shuffled null model runs")
    mean_rhos = []

    for i in range(n_runs):
        seed = base_seed + i
        mean_rho = shuffle_windows_and_compute_rho(window_rankings, seed)
        mean_rhos.append(mean_rho)
        if (i + 1) % 20 == 0:
            logger.info(f"  Run {i+1}/{n_runs}: mean_rho = {mean_rho:.4f}")

    mean_rho = float(np.mean(mean_rhos))
    std_rho = float(np.std(mean_rhos))
    min_rho = float(np.min(mean_rhos))
    max_rho = float(np.max(mean_rhos))

    result = {
        "n_runs": n_runs,
        "mean_rho": mean_rho,
        "std_rho": std_rho,
        "min_rho": min_rho,
        "max_rho": max_rho,
        "description": "Null model baseline: Mean Spearman rho of shuffled window sequences. "
                       "Observed drift should be compared against this distribution."
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    logger.info(f"Null baseline saved to {output_path}")
    logger.info(f"  Mean rho: {mean_rho:.4f} (+/- {std_rho:.4f})")

    return result

def main():
    """Main entry point for null baseline calculation."""
    # Default paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    profiles_path = project_root / "outputs" / "importance_profiles.csv"
    output_path = project_root / "outputs" / "null_baseline.json"

    # Allow override via environment variables
    if os.getenv("PROFILES_PATH"):
        profiles_path = Path(os.getenv("PROFILES_PATH"))
    if os.getenv("OUTPUT_PATH"):
        output_path = Path(os.getenv("OUTPUT_PATH"))

    n_runs = int(os.getenv("NULL_BASELINE_RUNS", "100"))

    logger.info(f"Starting Null Model Baseline calculation")
    logger.info(f"  Profiles: {profiles_path}")
    logger.info(f"  Output: {output_path}")
    logger.info(f"  Runs: {n_runs}")

    try:
        result = run_null_baseline(profiles_path, output_path, n_runs=n_runs)
        print(json.dumps(result, indent=2))
    except Exception as e:
        logger.error(f"Failed to compute null baseline: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
