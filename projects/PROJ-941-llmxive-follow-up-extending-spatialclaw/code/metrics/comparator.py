"""
Paired comparison logic for 2D and 3D agent results.

This module implements the logic to merge results from the 2D restricted agent
and the 3D baseline agent, calculate differences, and output a summary CSV.

It depends on T023b completion (data generation) to ensure the baseline results
file exists.
"""

import csv
import json
import logging
import os
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


def load_results_csv(path: str) -> List[Dict[str, Any]]:
    """
    Load results from a CSV file into a list of dictionaries.
    
    Args:
        path: Path to the CSV file.
        
    Returns:
        List of dictionaries representing each row.
        
    Raises:
        FileNotFoundError: If the file does not exist (fail loudly per constraints).
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Required results file not found: {path}. "
                                f"Ensure T023b (baseline generation) has completed.")
    
    results = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric strings to float/int where appropriate
            for key, value in row.items():
                if key in ['wall_clock_time_ms', 'latency_ms', 'blocked_time_ms']:
                    try:
                        row[key] = float(value) if value else 0.0
                    except ValueError:
                        row[key] = 0.0
                elif key == 'success_flag':
                    # Handle string representations of booleans
                    if isinstance(value, str):
                        row[key] = value.lower() == 'true'
                    else:
                        row[key] = bool(value)
            results.append(row)
    return results


def compare_results(
    results_2d_path: str,
    results_3d_path: str,
    output_path: str
) -> None:
    """
    Compare results from 2D and 3D agents and write a paired comparison CSV.
    
    This function performs the paired comparison logic required for FR-004.
    It matches rows by task_id, calculates time differences, and aggregates
    success rates.
    
    Args:
        results_2d_path: Path to the CSV containing 2D agent results.
        results_3d_path: Path to the CSV containing 3D agent results.
        output_path: Path where the comparison CSV will be written.
        
    Raises:
        FileNotFoundError: If either input file is missing.
        ValueError: If task_ids do not align for a valid paired comparison.
    """
    logger.info(f"Starting paired comparison: {results_2d_path} vs {results_3d_path}")
    
    # Load data (will fail loudly if missing)
    results_2d = load_results_csv(results_2d_path)
    results_3d = load_results_csv(results_3d_path)
    
    if not results_2d:
        raise ValueError(f"No data found in 2D results file: {results_2d_path}")
    if not results_3d:
        raise ValueError(f"No data found in 3D results file: {results_3d_path}")

    # Index results by task_id for efficient lookup
    indexed_2d = {r['task_id']: r for r in results_2d}
    indexed_3d = {r['task_id']: r for r in results_3d}

    # Identify unique task IDs found in both sets for strict pairing
    # The task implies a paired comparison, so we focus on intersecting IDs
    # but also report on any mismatches if they exist.
    common_task_ids = set(indexed_2d.keys()) & set(indexed_3d.keys())
    
    if not common_task_ids:
        raise ValueError("No common task_ids found between 2D and 3D results. "
                         "Ensure both agents ran on the same dataset.")
    
    # Also log warnings for task_ids present in one but not the other
    only_2d = set(indexed_2d.keys()) - common_task_ids
    only_3d = set(indexed_3d.keys()) - common_task_ids
    if only_2d:
        logger.warning(f"Task IDs found only in 2D results (skipping comparison): {len(only_2d)}")
    if only_3d:
        logger.warning(f"Task IDs found only in 3D results (skipping comparison): {len(only_3d)}")

    comparison_rows = []

    # Iterate over common task IDs to ensure valid pairing
    for task_id in sorted(common_task_ids):
        row_2d = indexed_2d[task_id]
        row_3d = indexed_3d[task_id]

        # Determine task type (prefer 3D if available, else 2D)
        task_type = None
        if 'task_type' in row_3d and row_3d['task_type']:
            task_type = row_3d['task_type']
        elif 'task_type' in row_2d and row_2d['task_type']:
            task_type = row_2d['task_type']
        
        if not task_type:
            task_type = 'unknown'

        # Extract metrics
        success_2d = row_2d.get('success_flag')
        success_3d = row_3d.get('success_flag')
        
        # Ensure numeric types for time
        time_2d = float(row_2d.get('wall_clock_time_ms', 0.0))
        time_3d = float(row_3d.get('wall_clock_time_ms', 0.0))

        # Calculate difference (2D - 3D)
        time_diff = time_2d - time_3d

        # Determine success diff (1 if 2D succeeded and 3D failed, -1 if vice versa, 0 if same)
        # This helps in McNemar's test later
        if success_2d and not success_3d:
            success_diff = 1
        elif not success_2d and success_3d:
            success_diff = -1
        else:
            success_diff = 0

        comparison_row = {
            'task_id': task_id,
            'task_type': task_type,
            'success_flag_2d': str(success_2d).lower() if success_2d is not None else '',
            'success_flag_3d': str(success_3d).lower() if success_3d is not None else '',
            'time_2d_ms': f"{time_2d:.2f}",
            'time_3d_ms': f"{time_3d:.2f}",
            'time_diff_ms': f"{time_diff:.2f}",
            'success_diff': success_diff
        }

        comparison_rows.append(comparison_row)

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Write to output CSV
    fieldnames = [
        'task_id', 'task_type', 'success_flag_2d', 'success_flag_3d',
        'time_2d_ms', 'time_3d_ms', 'time_diff_ms', 'success_diff'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(comparison_rows)

    logger.info(f"Comparison results written to {output_path}")
    logger.info(f"Total paired comparisons: {len(comparison_rows)}")

def main():
    """
    CLI entry point for the comparator.
    Usage: python -m metrics.comparator --2d <path> --3d <path> --out <path>
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Compare 2D and 3D agent results.")
    parser.add_argument("--2d", required=True, help="Path to 2D results CSV")
    parser.add_argument("--3d", required=True, help="Path to 3D results CSV")
    parser.add_argument("--out", required=True, help="Path for output comparison CSV")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    compare_results(args._2d, args._3d, args.out)

if __name__ == "__main__":
    main()