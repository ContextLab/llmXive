import json
import os
import sys
import csv
import random
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# Ensure we can import sibling modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.tradeoff_model import load_processed_logs, filter_invalid_workflows_from_logs, fit_tradeoff_curve
from analysis.threshold_detection import bootstrap_threshold

def calculate_error_rate(logs: List[Dict], reduction_pct: float) -> float:
    """
    Calculate the policy violation error rate for a specific context reduction percentage.
    
    Args:
        logs: List of execution logs.
        reduction_pct: The context reduction percentage to filter by.
        
    Returns:
        Error rate (0.0 to 1.0) for the given reduction percentage.
    """
    # Filter logs for the specific reduction percentage (with tolerance for float comparison)
    tolerance = 0.01
    matching_logs = [
        log for log in logs
        if abs(float(log.get('context_reduction_pct', 0)) - reduction_pct) < tolerance
    ]
    
    if not matching_logs:
        return 0.0
        
    # Calculate error rate (proportion of logs with policy violations)
    errors = sum(1 for log in matching_logs if log.get('policy_violations', []) and len(log['policy_violations']) > 0)
    return errors / len(matching_logs)

def get_unique_reduction_pcts(logs: List[Dict]) -> List[float]:
    """
    Extract unique context reduction percentages from logs.
    
    Args:
        logs: List of execution logs.
        
    Returns:
        Sorted list of unique reduction percentages.
    """
    pcts = set()
    for log in logs:
        pct = log.get('context_reduction_pct')
        if pct is not None and isinstance(pct, (int, float)):
            pcts.add(float(pct))
    return sorted(list(pcts))

def bootstrap_confidence_interval(
    logs: List[Dict],
    reduction_pct: float,
    n_bootstrap: int = 1000,
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate bootstrap confidence interval for error rate at a specific reduction percentage.
    
    Args:
        logs: List of execution logs.
        reduction_pct: The context reduction percentage.
        n_bootstrap: Number of bootstrap resamples.
        confidence: Confidence level (e.g., 0.95 for 95% CI).
        
    Returns:
        Tuple of (lower_bound, upper_bound) for the error rate CI.
    """
    # Filter logs for this reduction percentage
    tolerance = 0.01
    target_logs = [
        log for log in logs
        if abs(float(log.get('context_reduction_pct', 0)) - reduction_pct) < tolerance
    ]
    
    if len(target_logs) < 2:
        # Not enough data for bootstrap, return point estimate
        if not target_logs:
            return 0.0, 0.0
        errors = sum(1 for log in target_logs if log.get('policy_violations') and len(log['policy_violations']) > 0)
        rate = errors / len(target_logs)
        return rate, rate
    
    # Bootstrap resampling
    error_rates = []
    for _ in range(n_bootstrap):
        # Resample with replacement
        sample = [random.choice(target_logs) for _ in range(len(target_logs))]
        errors = sum(1 for log in sample if log.get('policy_violations') and len(log['policy_violations']) > 0)
        error_rates.append(errors / len(sample))
    
    error_rates.sort()
    alpha = 1 - confidence
    lower_idx = int((alpha / 2) * n_bootstrap)
    upper_idx = int((1 - alpha / 2) * n_bootstrap)
    
    return error_rates[lower_idx], error_rates[upper_idx]

def save_regression_data_to_csv(
    data: List[Dict],
    output_path: str
) -> None:
    """
    Save regression data to a CSV file.
    
    Args:
        data: List of dictionaries containing regression data points.
        output_path: Path to the output CSV file.
    """
    if not data:
        raise ValueError("No data to write to CSV")
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['reduction_pct', 'error_rate', 'depth', 'ci_lower', 'ci_upper']
    
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def generate_regression_data(
    logs: List[Dict],
    model_params: Optional[Dict] = None
) -> List[Dict]:
    """
    Generate regression data points for the tradeoff curve.
    
    Args:
        logs: List of execution logs.
        model_params: Optional pre-fitted model parameters.
        
    Returns:
        List of dictionaries containing regression data points with CI.
    """
    # Get unique reduction percentages
    unique_pcts = get_unique_reduction_pcts(logs)
    
    if not unique_pcts:
        return []
    
    data_points = []
    
    # Calculate error rate and CI for each unique reduction percentage
    for pct in unique_pcts:
        error_rate = calculate_error_rate(logs, pct)
        ci_lower, ci_upper = bootstrap_confidence_interval(logs, pct)
        
        # Get representative depth for this reduction percentage
        # (average depth of logs at this reduction level)
        matching_logs = [
            log for log in logs
            if abs(float(log.get('context_reduction_pct', 0)) - pct) < 0.01
        ]
        avg_depth = sum(log.get('compression_depth', 0) for log in matching_logs) / len(matching_logs) if matching_logs else 0
        
        data_points.append({
            'reduction_pct': round(pct, 2),
            'error_rate': round(error_rate, 4),
            'depth': round(avg_depth, 2),
            'ci_lower': round(ci_lower, 4),
            'ci_upper': round(ci_upper, 4)
        })
    
    # Sort by reduction percentage
    data_points.sort(key=lambda x: x['reduction_pct'])
    
    return data_points

def main():
    """
    Main entry point for generating regression data CSV.
    """
    # Define paths
    processed_logs_path = Path('data/processed/compressed_context_logs.json')
    output_csv_path = Path('data/results/tradeoff_curve.csv')
    
    # Ensure output directory exists
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load processed logs
    if not processed_logs_path.exists():
        print(f"Error: Processed logs not found at {processed_logs_path}")
        sys.exit(1)
    
    with open(processed_logs_path, 'r') as f:
        logs = json.load(f)
    
    # Filter invalid workflows
    valid_logs = filter_invalid_workflows_from_logs(logs)
    
    if not valid_logs:
        print("Error: No valid logs found for analysis")
        sys.exit(1)
    
    # Generate regression data
    regression_data = generate_regression_data(valid_logs)
    
    if not regression_data:
        print("Error: Could not generate regression data")
        sys.exit(1)
    
    # Save to CSV
    save_regression_data_to_csv(regression_data, str(output_csv_path))
    print(f"Regression data saved to {output_csv_path}")
    print(f"Generated {len(regression_data)} data points")

if __name__ == '__main__':
    main()