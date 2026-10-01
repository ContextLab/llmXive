"""
Null Model Baseline Implementation for Feature Importance Drift Analysis.

This module implements FR-007:
1. Shuffle chronological order of time windows.
2. Re-calculate importance rankings (using the existing importance_profiles.csv).
3. Calculate mean rho of multiple shuffled runs.
4. Generate outputs/null_baseline.json.

Note: Implementation follows Spec FR-007 (window shuffling).
"""
import os
import sys
import json
import logging
import random
import csv
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logger import get_logger

# Configuration
NUM_SHUFFLES = 1000  # Number of Monte Carlo permutations
OUTPUT_DIR = Path("outputs")
PROFILES_PATH = OUTPUT_DIR / "importance_profiles.csv"
NULL_BASELINE_PATH = OUTPUT_DIR / "null_baseline.json"

logger = get_logger(__name__)

def load_importance_profiles(profile_path: Path) -> Dict[int, List[Tuple[str, float]]]:
    """
    Load importance profiles from CSV.
    Returns a dict: { window_id: [(feature_name, importance_score), ...] }
    """
    profiles = {}
    if not profile_path.exists():
        raise FileNotFoundError(f"Importance profiles not found at {profile_path}")

    with open(profile_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            window_id = int(row['window_id'])
            feature_name = row['feature_name']
            importance_score = float(row['importance_score'])

            if window_id not in profiles:
                profiles[window_id] = []
            profiles[window_id].append((feature_name, importance_score))

    if not profiles:
        raise ValueError("Importance profiles file is empty or invalid.")

    return profiles

def extract_window_rankings(profiles: Dict[int, List[Tuple[str, float]]]) -> Dict[int, List[str]]:
    """
    Extract ordered list of feature names (rankings) for each window.
    Sorted by importance score descending.
    """
    rankings = {}
    for window_id, features in profiles.items():
        # Sort by importance score descending
        sorted_features = sorted(features, key=lambda x: x[1], reverse=True)
        rankings[window_id] = [f[0] for f in sorted_features]
    return rankings

def calculate_rank_correlation(rankings_t1: List[str], rankings_t2: List[str]) -> Tuple[float, float]:
    """
    Calculate Spearman rank correlation between two lists of feature names.
    Returns (rho, p_value).
    Uses a simple implementation since we only have rankings.
    Note: For true Spearman, we need ranks. Here we assume the list order IS the rank.
    """
    if len(rankings_t1) != len(rankings_t2):
        raise ValueError("Rankings must be of equal length")

    n = len(rankings_t1)
    if n == 0:
        return 0.0, 1.0

    # Create rank maps (feature -> rank index)
    # Rank 0 is most important (index 0 in list)
    rank_map_1 = {feat: i for i, feat in enumerate(rankings_t1)}
    rank_map_2 = {feat: i for i, feat in enumerate(rankings_t2)}

    # Calculate d^2
    d_squared_sum = 0
    common_features = set(rankings_t1) & set(rankings_t2)
    if len(common_features) < n:
        # If features differ, we can't compute standard Spearman directly.
        # For this null baseline, we assume the set of features is constant across windows.
        # If not, we compute correlation only on common features or return NaN.
        # Given the context of drift analysis on a fixed feature set, we expect equality.
        # We will raise an error if mismatched to catch data issues.
        raise ValueError(f"Feature set mismatch in windows. Expected {n}, found {len(common_features)} common.")

    for feat in common_features:
        d = rank_map_1[feat] - rank_map_2[feat]
        d_squared_sum += d * d

    # Spearman rho formula: 1 - (6 * sum(d^2)) / (n * (n^2 - 1))
    denominator = n * (n * n - 1)
    if denominator == 0:
        return 1.0, 0.0 # Perfect correlation if n=1 or 0

    rho = 1 - (6 * d_squared_sum) / denominator

    # Approximate p-value calculation for Spearman (t-distribution approximation)
    # t = rho * sqrt((n-2) / (1 - rho^2))
    # This is an approximation for n > 10. For small n, exact tables are better.
    # We will use a simplified approach: return rho and a placeholder p-value logic
    # or use scipy if available. Since we want to avoid heavy deps, we'll implement
    # a basic permutation p-value logic inside the main loop if needed,
    # but for the baseline mean, we just need the rho values.
    # However, the function signature asks for p_value. We'll return a dummy 0.0
    # as the p-value is not the primary metric for the baseline mean calculation.
    p_value = 0.0 

    return rho, p_value

def shuffle_windows_and_compute_rho(rankings: Dict[int, List[str]], rng: random.Random) -> float:
    """
    Shuffle the chronological order of window rankings and compute the 
    mean Spearman rho between consecutive shuffled windows.
    
    Returns the mean rho for this specific shuffle.
    """
    # Get sorted list of window IDs (chronological)
    window_ids = sorted(rankings.keys())
    if len(window_ids) < 2:
        return 0.0

    # Shuffle the window IDs
    shuffled_ids = window_ids.copy()
    rng.shuffle(shuffled_ids)

    # Compute pairwise rho for the shuffled sequence
    rhos = []
    for i in range(len(shuffled_ids) - 1):
        w_t = shuffled_ids[i]
        w_t1 = shuffled_ids[i+1]
        rho, _ = calculate_rank_correlation(rankings[w_t], rankings[w_t1])
        rhos.append(rho)

    if not rhos:
        return 0.0

    return sum(rhos) / len(rhos)

def run_null_baseline(profiles_path: Path = PROFILES_PATH, 
                      num_shuffles: int = NUM_SHUFFLES,
                      seed: int = 42) -> Dict[str, Any]:
    """
    Run the null model baseline procedure.
    1. Load profiles.
    2. Extract rankings.
    3. Perform `num_shuffles` random permutations of window order.
    4. Compute mean rho for each permutation.
    5. Return statistics (mean, std, min, max of the null distribution).
    """
    logger.info(f"Loading importance profiles from {profiles_path}")
    profiles = load_importance_profiles(profiles_path)
    
    logger.info("Extracting window rankings")
    rankings = extract_window_rankings(profiles)
    
    logger.info(f"Running {num_shuffles} null model permutations")
    rng = random.Random(seed)
    null_distributions = []

    for i in range(num_shuffles):
        mean_rho = shuffle_windows_and_compute_rho(rankings, rng)
        null_distributions.append(mean_rho)
        if (i + 1) % 100 == 0:
            logger.debug(f"Completed {i+1}/{num_shuffles} shuffles")

    # Calculate statistics
    mean_rho = sum(null_distributions) / len(null_distributions)
    variance = sum((x - mean_rho) ** 2 for x in null_distributions) / len(null_distributions)
    std_rho = variance ** 0.5
    min_rho = min(null_distributions)
    max_rho = max(null_distributions)

    result = {
        "num_shuffles": num_shuffles,
        "seed": seed,
        "null_distribution_stats": {
            "mean_rho": mean_rho,
            "std_rho": std_rho,
            "min_rho": min_rho,
            "max_rho": max_rho
        },
        "description": "Null model baseline generated by shuffling window chronology and computing mean Spearman rho of consecutive pairs."
    }

    return result

def save_null_baseline(result: Dict[str, Any], output_path: Path = NULL_BASELINE_PATH):
    """
    Save the null baseline results to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    logger.info(f"Null baseline saved to {output_path}")

def main():
    """
    Entry point for the null baseline script.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting Null Model Baseline Calculation")
    
    try:
        result = run_null_baseline()
        save_null_baseline(result)
        logger.info("Null Model Baseline completed successfully.")
        print(f"Null baseline mean rho: {result['null_distribution_stats']['mean_rho']:.4f}")
    except FileNotFoundError as e:
        logger.error(f"Data error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()