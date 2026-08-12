"""
Sensitivity Analysis for Lazy Heuristic Thresholds.

This script performs a sensitivity analysis on the Lazy traversal strategy
by varying the evidence threshold parameter across a defined range.
It reads existing execution results from T019a (Clean) and T019c (Noisy),
groups them by threshold, and computes aggregate statistics.

Output: data/processed/sensitivity_analysis.csv
"""
import os
import csv
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = DATA_DIR / "sensitivity_analysis.csv"

# Threshold range for sensitivity analysis
# These values correspond to the dynamic thresholds used in T019a/T019c
THRESHOLD_RANGE = [0.1, 0.3, 0.5, 0.7, 0.9]

def load_results_from_csv(filepath: Path) -> List[Dict[str, Any]]:
    """Load results from a CSV file into a list of dictionaries."""
    if not filepath.exists():
        logger.error(f"File not found: {filepath}")
        return []
    
    results = []
    try:
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Parse numeric fields
                parsed_row = {}
                for key, value in row.items():
                    if key in ['accuracy', 'nodes_visited', 'latency_ms', 'evidence_threshold']:
                        try:
                            parsed_row[key] = float(value)
                        except (ValueError, TypeError):
                            parsed_row[key] = None
                    else:
                        parsed_row[key] = value
                results.append(parsed_row)
    except Exception as e:
        logger.error(f"Error reading {filepath}: {e}")
        return []
    
    return results

def compute_aggregate_stats(results: List[Dict[str, Any]], threshold_val: float) -> Dict[str, Any]:
    """
    Compute aggregate statistics for a specific threshold.
    Matches results where evidence_threshold is close to threshold_val (within 0.05 tolerance).
    """
    tolerance = 0.05
    matching_results = [
        r for r in results 
        if r.get('evidence_threshold') is not None and 
        abs(r['evidence_threshold'] - threshold_val) <= tolerance
    ]

    if not matching_results:
        return {
            'threshold': threshold_val,
            'count': 0,
            'mean_accuracy': None,
            'std_accuracy': None,
            'mean_nodes_visited': None,
            'mean_latency_ms': None,
            'completion_rate': 0.0
        }

    accuracies = [r['accuracy'] for r in matching_results if r['accuracy'] is not None]
    nodes = [r['nodes_visited'] for r in matching_results if r['nodes_visited'] is not None]
    latencies = [r['latency_ms'] for r in matching_results if r['latency_ms'] is not None]
    
    # Calculate completion rate (non-null accuracy)
    total_tasks = len(matching_results)
    completed_tasks = len(accuracies)
    completion_rate = (completed_tasks / total_tasks) if total_tasks > 0 else 0.0

    return {
        'threshold': threshold_val,
        'count': total_tasks,
        'mean_accuracy': float(np.mean(accuracies)) if accuracies else None,
        'std_accuracy': float(np.std(accuracies)) if len(accuracies) > 1 else 0.0,
        'mean_nodes_visited': float(np.mean(nodes)) if nodes else None,
        'mean_latency_ms': float(np.mean(latencies)) if latencies else None,
        'completion_rate': completion_rate
    }

def run_sensitivity_analysis():
    """
    Main entry point for sensitivity analysis.
    Loads clean and noisy results, aggregates by threshold, and writes CSV.
    """
    logger.info("Starting Sensitivity Analysis...")
    
    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Load Clean Results (T019a)
    clean_path = DATA_DIR / "lazy_results.csv"
    clean_results = load_results_from_csv(clean_path)
    logger.info(f"Loaded {len(clean_results)} clean results from {clean_path}")

    # Load Noisy Results (T019c)
    noisy_path = DATA_DIR / "noisy_lazy_results.csv"
    noisy_results = load_results_from_csv(noisy_path)
    logger.info(f"Loaded {len(noisy_results)} noisy results from {noisy_path}")

    # Combine results (optional: keep separate or merge. Here we merge for overall trend)
    # We will analyze them separately to see the impact of noise
    all_results_clean = clean_results
    all_results_noisy = noisy_results

    analysis_rows = []

    # Process Clean Data
    logger.info("Analyzing Clean Data...")
    for thresh in THRESHOLD_RANGE:
        stats = compute_aggregate_stats(all_results_clean, thresh)
        stats['dataset'] = 'clean'
        analysis_rows.append(stats)

    # Process Noisy Data
    logger.info("Analyzing Noisy Data...")
    for thresh in THRESHOLD_RANGE:
        stats = compute_aggregate_stats(all_results_noisy, thresh)
        stats['dataset'] = 'noisy'
        analysis_rows.append(stats)

    # Write to CSV
    logger.info(f"Writing results to {OUTPUT_FILE}...")
    fieldnames = [
        'dataset', 'threshold', 'count', 'mean_accuracy', 'std_accuracy', 
        'mean_nodes_visited', 'mean_latency_ms', 'completion_rate'
    ]

    try:
        with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in analysis_rows:
                writer.writerow(row)
        
        logger.info(f"Sensitivity analysis complete. Output written to {OUTPUT_FILE}")
        return True
    except Exception as e:
        logger.error(f"Failed to write output file: {e}")
        return False

def main():
    """Command line entry point."""
    success = run_sensitivity_analysis()
    if not success:
        exit(1)

if __name__ == "__main__":
    main()
