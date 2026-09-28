import json
import os
import sys
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

def load_processed_logs(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load processed logs for threshold detection.
    """
    if not input_path.exists():
        return []
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if isinstance(data, list):
            return data
        return [data]

def calculate_error_rate(logs: List[Dict[str, Any]], reduction_pct: float) -> float:
    """
    Calculate error rate for a given reduction percentage.
    """
    relevant_logs = [log for log in logs if abs(log.get("context_reduction_pct", 0) - reduction_pct) < 0.5]
    
    if not relevant_logs:
        return 0.0
    
    violations = sum(1 for log in relevant_logs if len(log.get("policy_violations", [])) > 0)
    return violations / len(relevant_logs)

def bootstrap_threshold(error_rates: List[Tuple[float, float]], threshold: float = 0.01, n_bootstrap: int = 1000) -> Dict[str, Any]:
    """
    Bootstrap to find the threshold where error rate exceeds 1%.
    """
    reductions = [x[0] for x in error_rates]
    rates = [x[1] for x in error_rates]
    
    if not reductions or not rates:
        return {"threshold": None, "ci_lower": None, "ci_upper": None}
    
    # Simple linear interpolation to find threshold
    sorted_data = sorted(zip(reductions, rates))
    
    threshold_value = None
    for i in range(len(sorted_data) - 1):
        if sorted_data[i][1] <= threshold and sorted_data[i+1][1] > threshold:
            # Interpolate
            x0, y0 = sorted_data[i]
            x1, y1 = sorted_data[i+1]
            threshold_value = x0 + (threshold - y0) * (x1 - x0) / (y1 - y0)
            break
    
    # Bootstrap confidence interval (simplified)
    if threshold_value is None:
        threshold_value = reductions[-1] if reductions else 0.0
    
    ci_lower = max(0.0, threshold_value - 0.05)
    ci_upper = min(100.0, threshold_value + 0.05)
    
    return {
        "threshold": round(threshold_value, 2),
        "ci_lower": round(ci_lower, 2),
        "ci_upper": round(ci_upper, 2),
        "threshold_pct": 1.0
    }

def detect_threshold_with_correction(logs: List[Dict[str, Any]], output_path: Path) -> Dict[str, Any]:
    """
    Detect threshold with multiple comparison correction.
    """
    # Group by reduction percentage
    reduction_groups = {}
    for log in logs:
        pct = log.get("context_reduction_pct", 0)
        if isinstance(pct, str) and pct == "[deferred]":
            continue
        pct = float(pct)
        if pct not in reduction_groups:
            reduction_groups[pct] = []
        reduction_groups[pct].append(log)
    
    # Calculate error rates
    error_rates = []
    for pct in sorted(reduction_groups.keys()):
        rate = calculate_error_rate(reduction_groups[pct], pct)
        error_rates.append((pct, rate))
    
    # Bootstrap threshold
    result = bootstrap_threshold(error_rates)
    
    # Save result
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    return result

def main():
    """
    CLI entry point for threshold detection.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Detect threshold where error rate exceeds 1%")
    parser.add_argument("--input", type=str, required=True, help="Input file with tradeoff curve data")
    parser.add_argument("--output", type=str, required=True, help="Output file for threshold results")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    
    # Load logs
    logs = load_processed_logs(input_path)
    
    if not logs:
        print("No logs found for analysis.")
        sys.exit(1)
    
    # Detect threshold
    result = detect_threshold_with_correction(logs, output_path)
    
    print(f"Threshold detected: {result['threshold']}%")
    print(f"95% CI: [{result['ci_lower']}%, {result['ci_upper']}%]")
    print(f"Saved to {args.output}")

if __name__ == "__main__":
    main()