import os
import sys
import logging
import csv
import json
import math
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import scipy.stats as stats

from utils.logger import get_logger
from utils.config import get_config

logger = get_logger(__name__)
config = get_config()

def setup_module_logger():
    """Initialize logger for this module."""
    return logger

def load_importance_profiles(profiles_path: str) -> List[Dict[str, Any]]:
    """Load importance profiles from CSV."""
    profiles = []
    with open(profiles_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            profiles.append(row)
    return profiles

def extract_window_rankings(profiles: List[Dict[str, Any]]) -> Dict[int, List[float]]:
    """Extract feature rankings for each window."""
    rankings = {}
    for profile in profiles:
        window_id = int(profile['window_id'])
        # Parse importance values (assuming comma-separated string in 'importance_values' or similar)
        # Adjust key based on actual CSV structure from T014
        if 'importance_values' in profile:
            values = [float(x) for x in profile['importance_values'].split(',')]
        elif 'importances' in profile:
            values = [float(x) for x in profile['importances'].split(',')]
        else:
            # Fallback: assume numeric columns are importances
            # This is a heuristic; T014 should produce a consistent key
            numeric_cols = [k for k in profile.keys() if k not in ['window_id', 'timestamp']]
            values = [float(profile[k]) for k in numeric_cols]
        
        # Rank the values (1 = most important)
        # Using scipy.stats.rankdata with 'average' method for ties
        ranks = stats.rankdata(values, method='average')
        rankings[window_id] = list(ranks)
    return rankings

def calculate_rank_correlation(rankings_t: List[float], rankings_t1: List[float]) -> Tuple[float, float]:
    """Calculate Spearman rank correlation between two windows."""
    if len(rankings_t) != len(rankings_t1):
        raise ValueError("Rankings must have the same length")
    
    rho, p_value = stats.spearmanr(rankings_t, rankings_t1)
    return float(rho), float(p_value)

def load_null_baseline(null_baseline_path: str) -> Dict[str, Any]:
    """Load null baseline statistics from JSON."""
    with open(null_baseline_path, 'r') as f:
        return json.load(f)

def load_p_values_from_significance_test(p_values_path: str) -> Dict[int, float]:
    """Load block permutation p-values from significance test output."""
    p_values = {}
    if not os.path.exists(p_values_path):
        logger.warning(f"P-values file not found: {p_values_path}")
        return p_values
    
    with open(p_values_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Assuming columns: window_t, p_value
            window_t = int(row['window_t'])
            p_val = float(row['p_value'])
            p_values[window_t] = p_val
    return p_values

def compute_pairwise_drift(rankings: Dict[int, List[float]], p_values: Dict[int, float], null_baseline: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Compute pairwise drift metrics between consecutive windows."""
    sorted_windows = sorted(rankings.keys())
    drift_metrics = []
    
    # Get null baseline mean rho for comparison
    null_mean_rho = null_baseline.get('mean_rho', 0.0)
    
    for i in range(len(sorted_windows) - 1):
        w_t = sorted_windows[i]
        w_t1 = sorted_windows[i + 1]
        
        rho, p_val_spearman = calculate_rank_correlation(rankings[w_t], rankings[w_t1])
        
        # Get block permutation p-value for this transition
        p_val_perm = p_values.get(w_t, None)
        
        # Flag high drift based on permutation p-value < 0.05
        is_high_drift = False
        if p_val_perm is not None and p_val_perm < 0.05:
            is_high_drift = True
        
        drift_metrics.append({
            'window_t': w_t,
            'window_t1': w_t1,
            'rho': rho,
            'p_value_spearman': p_val_spearman,
            'p_value_permutation': p_val_perm,
            'is_high_drift': is_high_drift,
            'deviation_from_null': rho - null_mean_rho
        })
    
    return drift_metrics

def flag_high_drift(drift_metrics: List[Dict[str, Any]], p_values: Dict[int, float]) -> List[Dict[str, Any]]:
    """Flag transitions as high drift if block permutation p-value < 0.05."""
    # This logic is now integrated into compute_pairwise_drift, but kept for API compatibility
    for metric in drift_metrics:
        w_t = metric['window_t']
        if w_t in p_values and p_values[w_t] < 0.05:
            metric['is_high_drift'] = True
        else:
            metric['is_high_drift'] = False
    return drift_metrics

def save_drift_metrics(drift_metrics: List[Dict[str, Any]], output_path: str):
    """Save drift metrics to CSV."""
    if not drift_metrics:
        logger.warning("No drift metrics to save")
        return
    
    fieldnames = ['window_t', 'window_t1', 'rho', 'p_value_spearman', 'p_value_permutation', 'is_high_drift', 'deviation_from_null']
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(drift_metrics)
    
    logger.info(f"Saved drift metrics to {output_path}")

def run_drift_analysis(profiles_path: str, null_baseline_path: str, p_values_path: str, output_path: str):
    """Main function to run drift analysis pipeline."""
    logger.info(f"Loading importance profiles from {profiles_path}")
    profiles = load_importance_profiles(profiles_path)
    
    logger.info("Extracting window rankings")
    rankings = extract_window_rankings(profiles)
    
    logger.info(f"Loading null baseline from {null_baseline_path}")
    null_baseline = load_null_baseline(null_baseline_path)
    
    logger.info(f"Loading p-values from {p_values_path}")
    p_values = load_p_values_from_significance_test(p_values_path)
    
    logger.info("Computing pairwise drift")
    drift_metrics = compute_pairwise_drift(rankings, p_values, null_baseline)
    
    logger.info(f"Saving drift metrics to {output_path}")
    save_drift_metrics(drift_metrics, output_path)
    
    return drift_metrics

def main():
    """Entry point for drift analysis."""
    config = get_config()
    profiles_path = config.get('paths', {}).get('importance_profiles', 'outputs/importance_profiles.csv')
    null_baseline_path = config.get('paths', {}).get('null_baseline', 'outputs/null_baseline.json')
    p_values_path = config.get('paths', {}).get('p_values', 'outputs/significance_test_results.csv')
    output_path = config.get('paths', {}).get('drift_metrics', 'outputs/drift_metrics.csv')
    
    run_drift_analysis(profiles_path, null_baseline_path, p_values_path, output_path)

if __name__ == '__main__':
    main()
