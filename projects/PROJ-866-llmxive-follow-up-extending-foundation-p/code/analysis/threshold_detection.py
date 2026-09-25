import json
import os
import sys
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# Constants
DATA_PROCESSED_DIR = Path("data/processed")
DATA_RESULTS_DIR = Path("data/results")
THRESHOLD_ERROR_RATE = 0.01  # 1% error rate threshold

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

def bootstrap_threshold(
    logs: List[Dict[str, Any]], 
    threshold: float = THRESHOLD_ERROR_RATE,
    n_bootstrap: int = 1000,
    confidence: float = 0.95
) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """
    Bootstrap the threshold detection.
    
    Returns:
        Tuple of (threshold_value, ci_lower, ci_upper)
    """
    if not logs:
        return (None, None, None)
    
    # Sort logs by context reduction percentage
    valid_logs = [
        log for log in logs 
        if isinstance(log.get('context_reduction_pct'), (int, float))
    ]
    
    if not valid_logs:
        return (None, None, None)
    
    valid_logs.sort(key=lambda x: float(x['context_reduction_pct']))
    
    # Find the threshold point
    threshold_point = None
    for i, log in enumerate(valid_logs):
        reduction_pct = float(log['context_reduction_pct'])
        # Calculate cumulative error rate up to this point
        cumulative_logs = valid_logs[:i+1]
        error_rate = calculate_error_rate(cumulative_logs)
        
        if error_rate > threshold:
            threshold_point = reduction_pct
            break
    
    if threshold_point is None:
        # Check if error rate never exceeds threshold
        max_error_rate = calculate_error_rate(valid_logs)
        if max_error_rate < threshold:
            return (None, None, None)  # Undefined threshold
        else:
            # Error rate exceeds threshold immediately
            return (0.0, 0.0, 0.0)
    
    # Bootstrap confidence interval for the threshold
    threshold_samples = []
    for _ in range(n_bootstrap):
        # Resample logs
        sample = np.random.choice(valid_logs, size=len(valid_logs), replace=True)
        sample_logs = sorted(sample, key=lambda x: float(x['context_reduction_pct']))
        
        # Find threshold in sample
        sample_threshold = None
        for log in sample_logs:
            reduction_pct = float(log['context_reduction_pct'])
            cumulative_logs = [l for l in sample_logs if float(l['context_reduction_pct']) <= reduction_pct]
            error_rate = calculate_error_rate(cumulative_logs)
            
            if error_rate > threshold:
                sample_threshold = reduction_pct
                break
        
        if sample_threshold is not None:
            threshold_samples.append(sample_threshold)
    
    if not threshold_samples:
        return (threshold_point, None, None)
    
    threshold_samples.sort()
    lower_idx = int((1 - confidence) / 2 * n_bootstrap)
    upper_idx = int((1 + confidence) / 2 * n_bootstrap)
    
    ci_lower = threshold_samples[lower_idx] if lower_idx < len(threshold_samples) else None
    ci_upper = threshold_samples[upper_idx] if upper_idx < len(threshold_samples) else None
    
    return (threshold_point, ci_lower, ci_upper)

def detect_threshold_with_correction() -> None:
    """
    Main function to detect threshold with statistical correction.
    """
    print("Loading processed logs...")
    
    try:
        logs = load_processed_logs()
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    if not logs:
        print("No logs found for threshold detection.", file=sys.stderr)
        sys.exit(1)
    
    print(f"Loaded {len(logs)} logs")
    
    # Detect threshold with bootstrapping
    print("Detecting threshold with bootstrapping...")
    threshold, ci_lower, ci_upper = bootstrap_threshold(logs)
    
    # Prepare result
    result = {
        'threshold_pct': round(threshold, 2) if threshold is not None else None,
        'ci_lower': round(ci_lower, 2) if ci_lower is not None else None,
        'ci_upper': round(ci_upper, 2) if ci_upper is not None else None,
        'threshold_error_rate': THRESHOLD_ERROR_RATE,
        'method': 'bootstrap',
        'status': 'found' if threshold is not None else 'undefined'
    }
    
    # Handle edge cases
    if threshold is None:
        result['status'] = 'undefined'
        result['note'] = 'Error rate never exceeds threshold or exceeds immediately'
    
    # Save result
    output_path = DATA_RESULTS_DIR / "threshold_ci.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"Saved threshold detection results to {output_path}")
    
    if threshold is not None:
        print(f"Threshold: {threshold:.2f}% (95% CI: {ci_lower:.2f}% - {ci_upper:.2f}%)")
    else:
        print("Threshold could not be determined (undefined)")

def main():
    """
    Entry point for the script.
    """
    detect_threshold_with_correction()

if __name__ == "__main__":
    main()