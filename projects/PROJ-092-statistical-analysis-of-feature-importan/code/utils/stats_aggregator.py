import os
import sys
import json
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.logger import get_logger
from utils.config import get_config

logger = get_logger(__name__)

def calculate_stability_metrics(importance_profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate stability metrics from importance profiles."""
    if not importance_profiles:
        return {
            'total_windows': 0,
            'stable_window_count': 0,
            'average_r_squared': 0.0
        }
    
    total_windows = len(importance_profiles)
    # Assume 'r_squared' is in the profile
    r_squared_values = []
    stable_count = 0
    
    for profile in importance_profiles:
        if 'r_squared' in profile:
            r_sq = float(profile['r_squared'])
            r_squared_values.append(r_sq)
            # Consider a window stable if R² > 0.8 (from T012)
            if r_sq > 0.8:
                stable_count += 1
    
    avg_r_sq = sum(r_squared_values) / len(r_squared_values) if r_squared_values else 0.0
    
    return {
        'total_windows': total_windows,
        'stable_window_count': stable_count,
        'average_r_squared': avg_r_sq
    }

def aggregate_from_profiles(profiles_path: str) -> Dict[str, Any]:
    """Aggregate stability metrics from importance profiles file."""
    profiles = []
    if not os.path.exists(profiles_path):
        logger.warning(f"Profiles file not found: {profiles_path}")
        return calculate_stability_metrics([])
    
    with open(profiles_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            profiles.append(row)
    
    return calculate_stability_metrics(profiles)

def save_stability_report(metrics: Dict[str, Any], output_path: str):
    """Save stability report to JSON."""
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved stability report to {output_path}")

def main():
    """Entry point for stats aggregator."""
    config = get_config()
    profiles_path = config.get('paths', {}).get('importance_profiles', 'outputs/importance_profiles.csv')
    output_path = config.get('paths', {}).get('stability_report', 'outputs/stability_report.json')
    
    metrics = aggregate_from_profiles(profiles_path)
    save_stability_report(metrics, output_path)

if __name__ == '__main__':
    main()
