"""
Module to generate coverage metrics CSV from simulation logs.

Converts JSON simulation results to CSV format for analysis.
"""
import json
import os
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np


def load_results_from_log(log_path: str = "results/simulation_logs.json") -> List[Dict[str, Any]]:
    """
    Load simulation results from JSON log file.
    
    Args:
        log_path: Path to the simulation logs JSON file.
    
    Returns:
        List of result dictionaries.
    """
    if not os.path.exists(log_path):
        logging.warning(f"Log file not found: {log_path}")
        return []
    
    with open(log_path, 'r') as f:
        data = json.load(f)
    
    return data if isinstance(data, list) else [data]


def aggregate_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Aggregate results by phi and n values.
    
    Args:
        results: List of result dictionaries.
    
    Returns:
        List of aggregated result dictionaries.
    """
    if not results:
        return []
    
    # Group by phi and n
    grouped = {}
    for r in results:
        key = (r['phi'], r['n'])
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(r)
    
    aggregated = []
    for (phi, n), group in grouped.items():
        aggregated.append({
            'phi': phi,
            'n': n,
            'ordered_cov': np.mean([r['ordered_coverage'] for r in group]),
            'shuffled_cov': np.mean([r['shuffled_coverage'] for r in group]),
            'diff': np.mean([r['coverage_drop'] for r in group]),
            'p_value': np.mean([r['p_value'] for r in group]),
            'ci_width_ratio': np.mean([r['ci_width_ratio'] for r in group]),
            'bias_block': np.mean([r.get('bias_block', 0) for r in group])
        })
    
    return aggregated


def write_csv(aggregated_results: List[Dict[str, Any]], 
              output_path: str = "results/coverage_metrics.csv") -> None:
    """
    Write aggregated results to CSV file.
    
    Args:
        aggregated_results: List of aggregated result dictionaries.
        output_path: Path for the output CSV file.
    """
    if not aggregated_results:
        logging.warning("No results to write to CSV")
        return
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    fieldnames = ['phi', 'n', 'ordered_cov', 'shuffled_cov', 'diff', 
                 'p_value', 'ci_width_ratio', 'bias_block']
    
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(aggregated_results)
    
    logging.info(f"Metrics CSV written to {output_path}")


def main():
    """Main entry point for generating metrics CSV."""
    logging.basicConfig(level=logging.INFO)
    
    results = load_results_from_log()
    if not results:
        logging.warning("No simulation results found. Run simulation first.")
        return
    
    aggregated = aggregate_results(results)
    write_csv(aggregated)
    
    logging.info(f"Generated metrics CSV with {len(aggregated)} rows")


if __name__ == "__main__":
    main()
