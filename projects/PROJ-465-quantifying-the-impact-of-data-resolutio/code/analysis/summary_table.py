"""
Summary Table Module.

Generates a summary table identifying the lowest viable sampling rate
where the majority rule is met.

This module ensures strict typing and comprehensive documentation
as per task T039 requirements.
"""
import os
import json
import logging
import csv
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

def load_aggregation_results(agg_file: Path) -> Optional[Dict[str, Any]]:
    """
    Load the aggregation report from a JSON file.
    
    Args:
        agg_file: Path to the aggregation report.
        
    Returns:
        Dictionary of aggregation results or None if file not found.
    """
    if not agg_file.exists():
        logger.error(f"Aggregation file not found: {agg_file}")
        return None
    
    with open(agg_file, 'r') as f:
        return json.load(f)

def calculate_majority_rule_threshold(agg_data: Dict[str, Any]) -> Optional[int]:
    """
    Extract the global threshold determined by the majority rule logic.
    
    Args:
        agg_data: The aggregation report dictionary.
        
    Returns:
        The threshold sampling rate (int) or None if not found.
    """
    return agg_data.get('global_threshold')

def generate_summary_table(agg_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate a summary table (list of dictionaries) from aggregation data.
    
    Includes:
    - Global Threshold
    - Number of Valid Events
    - Standard Deviation of Thresholds (if available)
    
    Args:
        agg_data: Aggregation report.
        
    Returns:
        List of summary rows.
    """
    global_threshold = calculate_majority_rule_threshold(agg_data)
    valid_thresholds = agg_data.get('valid_thresholds', [])
    count = len(valid_thresholds)
    
    # Calculate SD if possible
    std_dev = None
    if count >= 2:
        import numpy as np
        std_dev = float(np.std(valid_thresholds, ddof=1))
    
    rows = [
        {
            'metric': 'Global Threshold (Hz)',
            'value': global_threshold if global_threshold else 'Not Found',
            'description': 'Lowest rate where majority rule (bias > limit) is met'
        },
        {
            'metric': 'Valid Events (N)',
            'value': count,
            'description': 'Number of events contributing to the threshold'
        }
    ]
    
    if std_dev is not None:
        rows.append({
            'metric': 'Threshold Standard Deviation',
            'value': f"{std_dev:.2f}",
            'description': 'Consistency of threshold across events'
        })
    else:
        rows.append({
            'metric': 'Threshold Standard Deviation',
            'value': 'Insufficient Data (N < 2)',
            'description': 'Not enough events to calculate consistency'
        })
    
    return rows

def save_summary_table(rows: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save the summary table to a CSV file.
    
    Args:
        rows: List of summary dictionaries.
        output_path: Path to the output CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['metric', 'value', 'description'])
        writer.writeheader()
        writer.writerows(rows)
    
    logger.info(f"Summary table saved to {output_path}")

def main() -> None:
    """
    Main entry point for summary table generation.
    """
    from code.config import RESULTS_DIR
    
    agg_file = RESULTS_DIR / 'aggregation_report.json'
    output_file = RESULTS_DIR / 'summary_table.csv'
    
    agg_data = load_aggregation_results(agg_file)
    if not agg_data:
        return
    
    rows = generate_summary_table(agg_data)
    save_summary_table(rows, output_file)

if __name__ == '__main__':
    main()
