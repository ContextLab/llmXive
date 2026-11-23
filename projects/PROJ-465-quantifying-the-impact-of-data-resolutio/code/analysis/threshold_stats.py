"""
Threshold Statistics Module.

Implements calculation of standard deviation for resolution thresholds
across the event population, with handling for insufficient data.

This module ensures strict typing and comprehensive documentation
as per task T039 requirements.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

def calculate_threshold_for_event(event_metrics: List[Dict[str, Any]]) -> Optional[int]:
    """
    Calculate the lowest viable sampling rate for a single event.
    
    This function is a duplicate of the logic in aggregate.py to ensure
    modularity and independence for this specific statistical calculation.
    
    Args:
        event_metrics: List of metrics for a single event.
        
    Returns:
        The identified sampling rate (int) or None if no threshold found.
    """
    # Filter out inconclusive results
    valid_metrics = []
    for m in event_metrics:
        posterior_meta = m.get('posterior_metadata', {})
        status = posterior_meta.get('status', 'valid')
        width_ratio = posterior_meta.get('width_to_prior_ratio', 0.0)
        
        is_inconclusive = (status == 'inconclusive') or (width_ratio > 0.5)
        if not is_inconclusive:
            valid_metrics.append(m)
    
    if not valid_metrics:
        return None
    
    # Find the lowest rate where bias exceeds threshold
    failing_rates = [m['sampling_rate'] for m in valid_metrics if m.get('exceeds_threshold', False)]
    
    if failing_rates:
        return min(failing_rates)
    
    return None

def calculate_threshold_std(event_thresholds: List[Optional[int]]) -> Dict[str, Any]:
    """
    Calculate the standard deviation of the identified resolution thresholds.
    
    Implements the conditional logic:
    - If N >= 2: Calculate and report SD.
    - If N < 2: Report "Insufficient data for population consistency".
    
    Args:
        event_thresholds: List of threshold rates (ints) or None for each event.
        
    Returns:
        Dictionary with 'std_dev', 'count', 'message', and 'values'.
    """
    # Filter out None values (events with no threshold)
    valid_thresholds = [t for t in event_thresholds if t is not None]
    n = len(valid_thresholds)
    
    result = {
        'count': n,
        'values': valid_thresholds,
        'message': ''
    }
    
    if n < 2:
        result['std_dev'] = None
        result['message'] = "Insufficient data for population consistency (N < 2)"
        logger.warning(f"Insufficient data for SD calculation: N={n}")
    else:
        # Calculate standard deviation
        std_val = np.std(valid_thresholds, ddof=1) # Sample standard deviation
        result['std_dev'] = float(std_val)
        result['message'] = f"Standard deviation calculated over {n} events."
        logger.info(f"Calculated threshold SD: {std_val:.2f} (N={n})")
    
    return result

def main() -> None:
    """
    Main entry point for threshold statistics calculation.
    
    Loads aggregation results and calculates the standard deviation of thresholds.
    """
    from code.config import RESULTS_DIR
    
    # Load aggregation results
    agg_file = RESULTS_DIR / 'aggregation_report.json'
    if not agg_file.exists():
        logger.error(f"Aggregation report not found at {agg_file}. Run aggregate.py first.")
        return
    
    with open(agg_file, 'r') as f:
        agg_data = json.load(f)
    
    thresholds = agg_data.get('valid_thresholds', [])
    
    stats = calculate_threshold_std(thresholds)
    
    # Save stats
    stats_file = RESULTS_DIR / 'threshold_stats.json'
    stats_file.parent.mkdir(parents=True, exist_ok=True)
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Threshold statistics saved to {stats_file}")

if __name__ == '__main__':
    main()
