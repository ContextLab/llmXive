"""
Null Model Baseline Implementation (T020)

Implements FR-007: Shuffle chronological order of time windows, re-calculate
importance rankings, calculate mean rho of multiple shuffled runs, and generate
outputs/null_baseline.json.
"""
import os
import sys
import json
import logging
import random
import csv
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import get_logger

logger = get_logger(__name__)

# Constants
DEFAULT_NUM_SHUFFLES = 1000
DEFAULT_RANDOM_SEED = 42
OUTPUT_DIR = Path("outputs")
OUTPUT_FILE = OUTPUT_DIR / "null_baseline.json"
IMPORTANCE_PROFILES_FILE = Path("outputs") / "importance_profiles.csv"


def load_importance_profiles(filepath: Path = IMPORTANCE_PROFILES_FILE) -> List[Dict[str, Any]]:
    """
    Load importance profiles from CSV file.
    
    Args:
        filepath: Path to the importance_profiles.csv file
        
    Returns:
        List of dictionaries containing window_id, feature, importance_score
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Importance profiles file not found: {filepath}")
    
    profiles = []
    with open(filepath, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            profiles.append({
                'window_id': row['window_id'],
                'feature': row['feature'],
                'importance_score': float(row['importance_score'])
            })
    
    logger.info(f"Loaded {len(profiles)} importance records from {filepath}")
    return profiles


def extract_window_rankings(profiles: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """
    Extract importance rankings per window.
    
    Args:
        profiles: List of importance profile records
        
    Returns:
        Dictionary mapping window_id to feature->importance_score mapping
    """
    window_data = {}
    for record in profiles:
        window_id = record['window_id']
        if window_id not in window_data:
            window_data[window_id] = {}
        window_data[window_id][record['feature']] = record['importance_score']
    
    logger.info(f"Extracted rankings for {len(window_data)} windows")
    return window_data


def calculate_rank_correlation(rankings_t: Dict[str, float], rankings_t1: Dict[str, float]) -> Tuple[float, float]:
    """
    Calculate Spearman rank correlation between two importance rankings.
    
    Args:
        rankings_t: Importance scores for time T
        rankings_t1: Importance scores for time T+1
        
    Returns:
        Tuple of (rho, p_value)
    """
    common_features = set(rankings_t.keys()) & set(rankings_t1.keys())
    if len(common_features) < 2:
        logger.warning("Insufficient common features for correlation calculation")
        return 0.0, 1.0
    
    # Get ranks
    features = sorted(common_features)
    ranks_t = {f: i for i, f in enumerate(features)}
    ranks_t1 = {f: i for i, f in enumerate(features)}
    
    # Reorder ranks based on importance scores
    sorted_t = sorted(features, key=lambda f: rankings_t[f], reverse=True)
    sorted_t1 = sorted(features, key=lambda f: rankings_t1[f], reverse=True)
    
    rank_map_t = {f: i for i, f in enumerate(sorted_t)}
    rank_map_t1 = {f: i for i, f in enumerate(sorted_t1)}
    
    # Calculate Spearman correlation
    n = len(features)
    d_squared_sum = sum((rank_map_t[f] - rank_map_t1[f]) ** 2 for f in features)
    
    # Spearman's rho formula
    rho = 1 - (6 * d_squared_sum) / (n * (n ** 2 - 1))
    
    # Approximate p-value using t-distribution approximation
    # t = rho * sqrt((n-2) / (1-rho^2))
    if abs(rho) >= 1.0:
        p_value = 0.0
    else:
        t_stat = rho * ((n - 2) ** 0.5) / ((1 - rho ** 2) ** 0.5)
        # Approximate p-value (two-tailed) using simple approximation
        # For small n, this is rough but sufficient for null baseline
        p_value = 2 * (1 - min(1.0, 0.5 + 0.5 * (t_stat / (t_stat ** 2 + n - 2)) ** 0.5))
    
    return rho, p_value


def shuffle_windows_and_compute_rho(window_data: Dict[str, Dict[str, float]], seed: int) -> float:
    """
    Shuffle window order and compute correlation sequence mean rho.
    
    Args:
        window_data: Dictionary of window_id -> feature->importance mapping
        seed: Random seed for reproducibility
        
    Returns:
        Mean rho value from the shuffled sequence
    """
    random.seed(seed)
    window_ids = list(window_data.keys())
    shuffled_ids = window_ids.copy()
    random.shuffle(shuffled_ids)
    
    if len(shuffled_ids) < 2:
        return 0.0
    
    rhos = []
    for i in range(len(shuffled_ids) - 1):
        window_t = shuffled_ids[i]
        window_t1 = shuffled_ids[i + 1]
        
        rho, _ = calculate_rank_correlation(
            window_data[window_t], 
            window_data[window_t1]
        )
        rhos.append(rho)
    
    return sum(rhos) / len(rhos) if rhos else 0.0


def run_null_baseline(
    num_shuffles: int = DEFAULT_NUM_SHUFFLES,
    random_seed: int = DEFAULT_RANDOM_SEED
) -> Dict[str, Any]:
    """
    Run the null model baseline analysis.
    
    Args:
        num_shuffles: Number of shuffled runs to perform
        random_seed: Base random seed for reproducibility
        
    Returns:
        Dictionary containing null baseline statistics
    """
    logger.info(f"Starting null baseline calculation with {num_shuffles} shuffles")
    
    # Load data
    profiles = load_importance_profiles()
    window_data = extract_window_rankings(profiles)
    
    if len(window_data) < 2:
        logger.error("Insufficient windows for null baseline calculation")
        return {
            "status": "failed",
            "reason": "Insufficient windows",
            "num_windows": len(window_data)
        }
    
    # Calculate original sequence rho (for comparison)
    window_ids = sorted(window_data.keys())
    original_rhos = []
    for i in range(len(window_ids) - 1):
        rho, _ = calculate_rank_correlation(
            window_data[window_ids[i]],
            window_data[window_ids[i + 1]]
        )
        original_rhos.append(rho)
    
    original_mean_rho = sum(original_rhos) / len(original_rhos) if original_rhos else 0.0
    
    # Perform shuffled runs
    shuffled_rhos = []
    for i in range(num_shuffles):
        seed_i = random_seed + i
        rho = shuffle_windows_and_compute_rho(window_data, seed_i)
        shuffled_rhos.append(rho)
    
    # Calculate statistics
    mean_rho = sum(shuffled_rhos) / len(shuffled_rhos)
    variance = sum((r - mean_rho) ** 2 for r in shuffled_rhos) / len(shuffled_rhos)
    std_dev = variance ** 0.5
    
    # Calculate p-value: proportion of shuffled runs with |rho| >= |original_mean_rho|
    extreme_count = sum(1 for r in shuffled_rhos if abs(r) >= abs(original_mean_rho))
    p_value = extreme_count / num_shuffles
    
    result = {
        "status": "success",
        "num_windows": len(window_data),
        "num_shuffles": num_shuffles,
        "original_mean_rho": original_mean_rho,
        "null_mean_rho": mean_rho,
        "null_std_dev": std_dev,
        "null_variance": variance,
        "p_value": p_value,
        "interpretation": "Drift is significant if p_value < 0.05" if p_value < 0.05 else "Drift not statistically significant"
    }
    
    logger.info(f"Null baseline complete: mean_rho={mean_rho:.4f}, p_value={p_value:.4f}")
    return result


def save_null_baseline(result: Dict[str, Any], filepath: Path = OUTPUT_FILE) -> None:
    """
    Save null baseline results to JSON file.
    
    Args:
        result: Dictionary containing null baseline statistics
        filepath: Output file path
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Saved null baseline results to {filepath}")


def main():
    """Main entry point for null baseline calculation."""
    try:
        # Ensure output directory exists
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        # Run analysis
        result = run_null_baseline(
            num_shuffles=DEFAULT_NUM_SHUFFLES,
            random_seed=DEFAULT_RANDOM_SEED
        )
        
        # Save results
        save_null_baseline(result)
        
        # Print summary
        print(json.dumps(result, indent=2))
        
        return 0
        
    except Exception as e:
        logger.error(f"Null baseline calculation failed: {e}")
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
