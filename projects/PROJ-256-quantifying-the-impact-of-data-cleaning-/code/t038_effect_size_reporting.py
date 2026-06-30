"""
Task T038: Implement per-dataset effect-size change reporting.

Calculates Median and IQR of effect-size changes across datasets and cleaning strategies.
Includes a statistical limitation warning if the sample size (n) is 2.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime

from utils import setup_logging

# Configure logging
logger = setup_logging("T038_EffectSizeReporting")

def load_json(filepath: str) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return its contents."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        return None
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in file: {filepath}")
        return None

def calculate_effect_size_delta(baseline_effect: float, cleaned_effect: float) -> float:
    """Calculate the absolute difference in effect sizes."""
    if baseline_effect is None or cleaned_effect is None:
        return None
    return abs(cleaned_effect - baseline_effect)

def calculate_median_and_iqr(values: List[float]) -> Dict[str, float]:
    """
    Calculate the median and Interquartile Range (IQR) for a list of values.
    Returns a dict with 'median' and 'iqr' keys.
    """
    if not values:
        return {'median': None, 'iqr': None}
    
    arr = np.array(values)
    median = float(np.median(arr))
    q1 = float(np.percentile(arr, 25))
    q3 = float(np.percentile(arr, 75))
    iqr = q3 - q1
    
    return {'median': median, 'iqr': iqr}

def load_metrics(baseline_path: str, cleaned_path: str) -> List[Dict[str, Any]]:
    """
    Load baseline and cleaned metrics and compute effect size deltas for each dataset.
    Returns a list of dicts containing dataset info and the delta.
    """
    baseline_data = load_json(baseline_path)
    cleaned_data = load_json(cleaned_path)

    if not baseline_data or not cleaned_data:
        logger.warning("Could not load metrics files. Skipping calculation.")
        return []

    # Normalize data structure if it's wrapped in a 'datasets' key or similar
    # Assuming the structure matches T012/T023 output: list of results or dict of results
    # We expect a list of entries where each entry has 'dataset_id', 'effect_size', etc.
    
    # Handle potential structure variations
    if isinstance(baseline_data, dict) and 'results' in baseline_data:
        baseline_list = baseline_data['results']
    elif isinstance(baseline_data, list):
        baseline_list = baseline_data
    else:
        logger.error("Unexpected baseline metrics structure.")
        return []

    if isinstance(cleaned_data, dict) and 'results' in cleaned_data:
        cleaned_list = cleaned_data['results']
    elif isinstance(cleaned_data, list):
        cleaned_list = cleaned_data
    else:
        logger.error("Unexpected cleaned metrics structure.")
        return []

    # Create a lookup for cleaned metrics by dataset_id and strategy
    # We need to match baseline to specific cleaned variants.
    # For this task, we calculate deltas for every valid pair found.
    
    deltas = []
    
    # Assuming baseline_list contains entries like: {'dataset_id': '...', 'effect_size': 0.5, ...}
    # And cleaned_list contains entries like: {'dataset_id': '...', 'strategy': 'iqr', 'effect_size': 0.6, ...}
    
    baseline_map = {}
    for b in baseline_list:
        ds_id = b.get('dataset_id')
        if ds_id and 'effect_size' in b:
            baseline_map[ds_id] = b['effect_size']

    for c in cleaned_list:
        ds_id = c.get('dataset_id')
        strategy = c.get('strategy', 'unknown')
        effect = c.get('effect_size')
        
        if ds_id in baseline_map and effect is not None:
            base_eff = baseline_map[ds_id]
            delta = calculate_effect_size_delta(base_eff, effect)
            if delta is not None:
                deltas.append({
                    'dataset_id': ds_id,
                    'strategy': strategy,
                    'baseline_effect_size': base_eff,
                    'cleaned_effect_size': effect,
                    'effect_size_delta': delta
                })
    
    return deltas

def generate_per_dataset_effect_size_report(deltas: List[Dict[str, Any]], output_path: str) -> None:
    """
    Generate a report containing per-dataset effect size changes and aggregate statistics.
    Logs a warning if n=2.
    """
    if not deltas:
        logger.warning("No effect size deltas found to report.")
        # Create an empty report to indicate completion
        report = {
            'status': 'no_data',
            'message': 'No effect size changes calculated.',
            'timestamp': datetime.now().isoformat()
        }
    else:
        deltas_values = [d['effect_size_delta'] for d in deltas]
        stats = calculate_median_and_iqr(deltas_values)
        
        n = len(deltas_values)
        
        report = {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'n_datasets': n,
            'statistics': stats,
            'per_dataset_details': deltas
        }

        # Constraint Check: If n=2, log specific limitation message
        if n == 2:
            logger.warning("STATISTICAL_LIMITATION: Median/IQR calculated on n=2, results are unstable.")
        elif n < 2:
            logger.warning(f"STATISTICAL_LIMITATION: Median/IQR calculated on n={n}, results are statistically invalid.")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Effect size report written to {output_path}")

def main():
    """Main entry point for T038."""
    # Paths based on project conventions
    baseline_path = os.path.join("data", "processed", "baseline_metrics.json")
    cleaned_path = os.path.join("data", "processed", "cleaned_metrics.json")
    output_path = os.path.join("data", "processed", "effect_size_changes.json")

    logger.info("Starting T038: Per-dataset effect-size change reporting")
    
    deltas = load_metrics(baseline_path, cleaned_path)
    generate_per_dataset_effect_size_report(deltas, output_path)
    
    logger.info("T038 completed successfully.")

if __name__ == "__main__":
    main()