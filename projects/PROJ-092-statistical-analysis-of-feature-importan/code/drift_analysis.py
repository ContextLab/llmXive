import os
import sys
import logging
import csv
import json
import math
import random
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any

# Import from sibling modules based on API surface
from utils.logger import setup_logger, get_logger
from utils.config import get_config

# Constants
OUTPUT_DIR = Path("data/outputs")
PROFILES_PATH = OUTPUT_DIR / "importance_profiles.csv"
DRIFT_METRICS_PATH = OUTPUT_DIR / "drift_metrics.csv"
NULL_BASELINE_PATH = OUTPUT_DIR / "null_baseline.json"
SIGNIFICANCE_RESULTS_PATH = OUTPUT_DIR / "significance_results.json"

logger = setup_logger("drift_analysis")

def setup_module_logger(name: str) -> logging.Logger:
    """Setup a logger for the module."""
    return get_logger(name)

def load_importance_profiles(path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load importance profiles from CSV."""
    if path is None:
        path = PROFILES_PATH
    
    if not path.exists():
        raise FileNotFoundError(f"Importance profiles not found at {path}")
    
    profiles = []
    with open(path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            profile = {
                'window_id': int(row['window_id']),
                'feature': row['feature'],
                'importance_score': float(row['importance_score'])
            }
            profiles.append(profile)
    return profiles

def extract_window_rankings(profiles: List[Dict[str, Any]], window_id: int) -> Dict[str, float]:
    """Extract importance scores for a specific window."""
    return {p['feature']: p['importance_score'] for p in profiles if p['window_id'] == window_id}

def calculate_rank_correlation(rankings1: Dict[str, float], rankings2: Dict[str, float]) -> Tuple[float, float]:
    """
    Calculate Spearman rank correlation between two sets of feature importances.
    Returns (rho, p_value).
    """
    common_features = set(rankings1.keys()) & set(rankings2.keys())
    if len(common_features) < 2:
        return 0.0, 1.0  # Not enough features to correlate

    # Rank the features
    features = sorted(common_features)
    ranks1 = {f: i + 1 for i, f in enumerate(sorted(features, key=lambda x: rankings1[x], reverse=True))}
    ranks2 = {f: i + 1 for i, f in enumerate(sorted(features, key=lambda x: rankings2[x], reverse=True))}

    # Calculate Spearman's rho
    n = len(features)
    d_squared_sum = sum((ranks1[f] - ranks2[f]) ** 2 for f in features)
    rho = 1 - (6 * d_squared_sum) / (n * (n ** 2 - 1))

    # Approximate p-value using t-distribution (for n > 10)
    # For small n, we use a simpler heuristic or permutation (handled elsewhere)
    if n > 10:
        t_stat = rho * math.sqrt((n - 2) / (1 - rho ** 2))
        # Approximate p-value (two-tailed) using a simplified t-distribution approach
        # In production, use scipy.stats, but avoiding external heavy deps if possible
        # Here we use a simplified approximation for the p-value
        p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(t_stat) / math.sqrt(2))))
    else:
        # For small n, return a placeholder p-value; actual significance tested via permutation
        p_value = 1.0

    return rho, p_value

def compute_pairwise_drift(profiles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Compute drift metrics between consecutive windows."""
    windows = sorted(list(set(p['window_id'] for p in profiles)))
    drift_metrics = []

    for i in range(len(windows) - 1):
        window_t = windows[i]
        window_t_plus_1 = windows[i + 1]
        
        rankings_t = extract_window_rankings(profiles, window_t)
        rankings_t_plus_1 = extract_window_rankings(profiles, window_t_plus_1)
        
        rho, p_value = calculate_rank_correlation(rankings_t, rankings_t_plus_1)
        
        drift_metrics.append({
            'window_t': window_t,
            'window_t_plus_1': window_t_plus_1,
            'rho': rho,
            'p_value': p_value,
            'high_drift': False  # Will be updated by flag_high_drift
        })
    
    return drift_metrics

def load_null_baseline(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load null baseline results from JSON."""
    if path is None:
        path = NULL_BASELINE_PATH
    
    if not path.exists():
        raise FileNotFoundError(f"Null baseline not found at {path}")
    
    with open(path, 'r') as f:
        return json.load(f)

def load_p_values_from_significance_test(path: Optional[Path] = None) -> Dict[int, float]:
    """Load p-values from significance test results."""
    if path is None:
        path = SIGNIFICANCE_RESULTS_PATH
    
    if not path.exists():
        logger.warning(f"Significance results not found at {path}. Using default p-values.")
        return {}
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Assume structure: {"p_values": {"window_t": p_value, ...}}
    return {int(k): v for k, v in data.get('p_values', {}).items()}

def flag_high_drift(drift_metrics: List[Dict[str, Any]], null_baseline: Dict[str, Any], p_values: Dict[int, float]) -> List[Dict[str, Any]]:
    """
    Flag transitions as high drift based on p-value threshold.
    Uses p-value from significance test if available, otherwise falls back to null baseline.
    """
    threshold = 0.05
    null_mean_rho = null_baseline.get('mean_rho', 0.0)
    
    for metric in drift_metrics:
        window_t = metric['window_t']
        p_value = p_values.get(window_t, metric['p_value'])
        
        # Flag if p-value < threshold
        metric['high_drift'] = p_value < threshold
    
    return drift_metrics

def save_drift_metrics(drift_metrics: List[Dict[str, Any]], path: Optional[Path] = None) -> Path:
    """Save drift metrics to CSV."""
    if path is None:
        path = DRIFT_METRICS_PATH
    
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', newline='') as f:
        fieldnames = ['window_t', 'window_t_plus_1', 'rho', 'p_value', 'high_drift']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(drift_metrics)
    
    logger.info(f"Saved drift metrics to {path}")
    return path

def run_drift_analysis(profiles_path: Optional[Path] = None, 
                       null_baseline_path: Optional[Path] = None,
                       significance_results_path: Optional[Path] = None) -> Path:
    """
    Run the full drift analysis pipeline:
    1. Load importance profiles
    2. Compute pairwise drift
    3. Load null baseline and p-values
    4. Flag high drift
    5. Save metrics
    """
    profiles = load_importance_profiles(profiles_path)
    drift_metrics = compute_pairwise_drift(profiles)
    
    try:
        null_baseline = load_null_baseline(null_baseline_path)
    except FileNotFoundError:
        logger.warning("Null baseline not found. Skipping high drift flagging.")
        null_baseline = {'mean_rho': 0.0}
    
    try:
        p_values = load_p_values_from_significance_test(significance_results_path)
    except FileNotFoundError:
        logger.warning("Significance results not found. Using default p-values.")
        p_values = {}
    
    drift_metrics = flag_high_drift(drift_metrics, null_baseline, p_values)
    output_path = save_drift_metrics(drift_metrics)
    
    return output_path

def main():
    """Main entry point for drift analysis."""
    logger.info("Starting drift analysis...")
    try:
        output_path = run_drift_analysis()
        logger.info(f"Drift analysis complete. Results saved to {output_path}")
    except Exception as e:
        logger.error(f"Drift analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()