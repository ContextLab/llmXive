import json
import os
import sys
import csv
import random
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# Constants
DATA_PROCESSED_DIR = Path("data/processed")
DATA_RESULTS_DIR = Path("data/results")

def load_processed_logs() -> List[Dict[str, Any]]:
    """
    Load all processed execution logs from data/processed/.
    """
    logs = []
    
    if not DATA_PROCESSED_DIR.exists():
        raise FileNotFoundError(f"Directory not found: {DATA_PROCESSED_DIR}")
    
    for file_path in DATA_PROCESSED_DIR.iterdir():
        if file_path.is_file() and file_path.suffix == '.json':
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    # Handle both single log and list of logs
                    if isinstance(data, list):
                        logs.extend(data)
                    elif isinstance(data, dict):
                        if 'logs' in data and isinstance(data['logs'], list):
                            logs.extend(data['logs'])
                        else:
                            logs.append(data)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Could not parse {file_path}: {e}", file=sys.stderr)
    
    return logs

def calculate_error_rate(logs: List[Dict[str, Any]]) -> float:
    """
    Calculate the policy violation error rate from logs.
    """
    if not logs:
        return 0.0
    
    violations = sum(1 for log in logs if log.get('policy_violations', []))
    return violations / len(logs)

def bootstrap_confidence_interval(
    logs: List[Dict[str, Any]], 
    n_bootstrap: int = 1000, 
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate bootstrap confidence interval for error rate.
    """
    if not logs:
        return (0.0, 0.0)
    
    error_rates = []
    for _ in range(n_bootstrap):
        sample = random.choices(logs, k=len(logs))
        error_rate = calculate_error_rate(sample)
        error_rates.append(error_rate)
    
    error_rates.sort()
    lower_idx = int((1 - confidence) / 2 * n_bootstrap)
    upper_idx = int((1 + confidence) / 2 * n_bootstrap)
    
    return (error_rates[lower_idx], error_rates[upper_idx])

def get_unique_reduction_pcts(logs: List[Dict[str, Any]]) -> List[float]:
    """
    Get unique context reduction percentages from logs.
    """
    reduction_pcts = set()
    for log in logs:
        reduction_pct = log.get('context_reduction_pct')
        if isinstance(reduction_pct, (int, float)):
            reduction_pcts.add(float(reduction_pct))
        elif isinstance(reduction_pct, str) and reduction_pct != "[deferred]":
            try:
                reduction_pcts.add(float(reduction_pct))
            except ValueError:
                pass
    
    return sorted(list(reduction_pcts))

def save_regression_data_to_csv(
    data: List[Dict[str, Any]], 
    output_path: Path
) -> None:
    """
    Save regression data to CSV file.
    """
    if not data:
        raise ValueError("No data to save")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['reduction_pct', 'error_rate', 'depth', 'ci_lower', 'ci_upper']
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def generate_regression_data() -> None:
    """
    Main function to generate regression data for trade-off analysis.
    """
    print("Loading processed logs...")
    logs = load_processed_logs()
    
    if not logs:
        print("No logs found for analysis.", file=sys.stderr)
        sys.exit(1)
    
    print(f"Loaded {len(logs)} logs")
    
    # Get unique reduction percentages
    reduction_pcts = get_unique_reduction_pcts(logs)
    print(f"Found {len(reduction_pcts)} unique reduction percentages")
    
    # Group logs by reduction percentage and calculate statistics
    regression_data = []
    for reduction_pct in reduction_pcts:
        # Filter logs for this reduction percentage
        filtered_logs = [
            log for log in logs 
            if isinstance(log.get('context_reduction_pct'), (int, float)) and 
            abs(float(log['context_reduction_pct']) - reduction_pct) < 0.01
        ]
        
        if not filtered_logs:
            continue
        
        # Calculate error rate and confidence interval
        error_rate = calculate_error_rate(filtered_logs)
        ci_lower, ci_upper = bootstrap_confidence_interval(filtered_logs)
        
        # Get average depth for this bin
        depths = [log.get('compression_depth', 0) for log in filtered_logs 
                 if isinstance(log.get('compression_depth'), (int, float))]
        avg_depth = sum(depths) / len(depths) if depths else 0
        
        regression_data.append({
            'reduction_pct': round(reduction_pct, 2),
            'error_rate': round(error_rate, 4),
            'depth': round(avg_depth, 2),
            'ci_lower': round(ci_lower, 4),
            'ci_upper': round(ci_upper, 4)
        })
    
    # Sort by reduction percentage
    regression_data.sort(key=lambda x: x['reduction_pct'])
    
    # Save to CSV
    output_path = DATA_RESULTS_DIR / "tradeoff_curve.csv"
    save_regression_data_to_csv(regression_data, output_path)
    
    print(f"Saved regression data to {output_path}")
    print(f"Generated {len(regression_data)} data points")

def main():
    """
    Entry point for the script.
    """
    generate_regression_data()

if __name__ == "__main__":
    main()
