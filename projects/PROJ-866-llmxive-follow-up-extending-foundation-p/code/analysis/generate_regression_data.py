import json
import os
import sys
import csv
import random
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# Import from sibling modules as per API surface
# Note: We assume tradeoff_model.py has been updated to provide the regression curve data
# or we implement the calculation here based on the logs.
# Based on the API surface, tradeoff_model.py has 'generate_regression_data' but T031
# implies the threshold is the main output. We need to generate the full curve.
# We will load the processed logs and calculate the curve points.

def load_processed_logs(log_dir: Path) -> List[Dict[str, Any]]:
    """Load all execution logs from the processed directory."""
    logs = []
    if not log_dir.exists():
        return logs
    
    for file_path in log_dir.glob("*.json"):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                # Handle both single log objects and lists
                if isinstance(data, list):
                    logs.extend(data)
                else:
                    logs.append(data)
        except (json.JSONDecodeError, IOError):
            continue
    return logs

def calculate_error_rate(logs: List[Dict[str, Any]], reduction_pct: float, tolerance: float = 1.0) -> float:
    """
    Calculate the error rate (policy violation rate) for a given reduction percentage.
    tolerance: The window around the reduction_pct to consider (e.g., +/- 1%).
    """
    matching_logs = []
    for log in logs:
        # context_reduction_pct can be a number or "[deferred]"
        val = log.get('context_reduction_pct', 0)
        if isinstance(val, str) and val == "[deferred]":
            continue
        try:
            pct = float(val)
            if abs(pct - reduction_pct) <= tolerance:
                matching_logs.append(log)
        except (ValueError, TypeError):
            continue
    
    if not matching_logs:
        return 0.0
    
    violations = sum(1 for log in matching_logs if log.get('policy_violations', []))
    return violations / len(matching_logs)

def bootstrap_confidence_interval(logs: List[Dict[str, Any]], reduction_pct: float, 
                                  n_bootstrap: int = 1000, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate bootstrap confidence interval for the error rate at a given reduction_pct.
    """
    # Filter logs for this reduction_pct
    matching_logs = []
    tolerance = 1.0
    for log in logs:
        val = log.get('context_reduction_pct', 0)
        if isinstance(val, str) and val == "[deferred]":
            continue
        try:
            pct = float(val)
            if abs(pct - reduction_pct) <= tolerance:
                matching_logs.append(log)
        except (ValueError, TypeError):
            continue
    
    if len(matching_logs) < 2:
        return 0.0, 0.0
    
    error_rates = []
    for _ in range(n_bootstrap):
        # Resample with replacement
        sample = [random.choice(matching_logs) for _ in range(len(matching_logs))]
        violations = sum(1 for log in sample if log.get('policy_violations', []))
        error_rates.append(violations / len(sample))
    
    error_rates.sort()
    lower_idx = int((1 - confidence) / 2 * n_bootstrap)
    upper_idx = int((1 + confidence) / 2 * n_bootstrap)
    
    return error_rates[lower_idx], error_rates[upper_idx]

def get_unique_reduction_pcts(logs: List[Dict[str, Any]]) -> List[float]:
    """Extract unique reduction percentages from logs."""
    pcts = set()
    for log in logs:
        val = log.get('context_reduction_pct', 0)
        if isinstance(val, str) and val == "[deferred]":
            continue
        try:
            pcts.add(round(float(val), 2))
        except (ValueError, TypeError):
            continue
    return sorted(list(pcts))

def save_regression_data_to_csv(data: List[Dict[str, Any]], output_path: Path) -> None:
    """Save regression data to CSV."""
    if not data:
        # Write headers even if empty
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['reduction_pct', 'error_rate', 'depth', 'ci_lower', 'ci_upper'])
        return

    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['reduction_pct', 'error_rate', 'depth', 'ci_lower', 'ci_upper'])
        for row in data:
            writer.writerow([
                row['reduction_pct'],
                row['error_rate'],
                row['depth'],
                row['ci_lower'],
                row['ci_upper']
            ])

def generate_regression_data(logs: List[Dict[str, Any]], output_path: Path) -> List[Dict[str, Any]]:
    """
    Generate the tradeoff curve data points with confidence intervals.
    This function aggregates logs by reduction_pct, calculates error rates,
    and computes bootstrap confidence intervals.
    """
    reduction_pcts = get_unique_reduction_pcts(logs)
    
    if not reduction_pcts:
        # Fallback if no valid logs found, create a minimal placeholder structure
        # to satisfy the file existence requirement, though it won't have real data.
        # In a real run, this should not happen if previous tasks succeeded.
        pass

    results = []
    for pct in reduction_pcts:
        error_rate = calculate_error_rate(logs, pct)
        ci_lower, ci_upper = bootstrap_confidence_interval(logs, pct)
        
        # Determine a representative depth for this reduction_pct
        # We take the median depth of logs in this bucket
        matching_depths = []
        for log in logs:
            val = log.get('context_reduction_pct', 0)
            if isinstance(val, str): continue
            try:
                if abs(float(val) - pct) <= 1.0:
                    if 'depth' in log:
                        matching_depths.append(log['depth'])
            except:
                continue
        
        median_depth = 0
        if matching_depths:
            median_depth = int(sorted(matching_depths)[len(matching_depths)//2])

        results.append({
            'reduction_pct': round(pct, 2),
            'error_rate': round(error_rate, 4),
            'depth': median_depth,
            'ci_lower': round(ci_lower, 4),
            'ci_upper': round(ci_upper, 4)
        })
    
    # Sort by reduction_pct
    results.sort(key=lambda x: x['reduction_pct'])
    
    save_regression_data_to_csv(results, output_path)
    return results

def main():
    """Main entry point for generating regression data."""
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    logs_dir = project_root / 'data' / 'processed'
    results_dir = project_root / 'data' / 'results'
    output_file = results_dir / 'tradeoff_curve.csv'
    
    # Ensure output directory exists
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Load logs
    logs = load_processed_logs(logs_dir)
    
    if not logs:
        print(f"Warning: No logs found in {logs_dir}. Generating empty CSV.")
        # Create empty file with headers
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['reduction_pct', 'error_rate', 'depth', 'ci_lower', 'ci_upper'])
        return
    
    # Generate data
    results = generate_regression_data(logs, output_file)
    print(f"Generated {len(results)} data points for tradeoff curve in {output_file}")

if __name__ == '__main__':
    main()