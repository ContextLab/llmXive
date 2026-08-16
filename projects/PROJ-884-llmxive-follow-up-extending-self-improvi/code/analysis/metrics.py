import json
import os
import math
import csv
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict

@dataclass
class ExperimentMetrics:
    experiment_id: str
    problem_size: int
    success: bool
    wall_clock_time: float
    energy_joules: float
    complexity_class: Optional[str] = None

def load_experiment_logs(log_path: Path) -> List[Dict[str, Any]]:
    """
    Load experiment logs from a JSON file.
    Expects a list of log entries or a JSON object with a 'logs' key.
    """
    if not log_path.exists():
        raise FileNotFoundError(f"Log file not found: {log_path}")
    
    with open(log_path, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'logs' in data:
        return data['logs']
    else:
        # Try to parse as a single log entry wrapped in a list
        return [data]

def calculate_metrics_from_logs(logs: List[Dict[str, Any]]) -> List[ExperimentMetrics]:
    """
    Extract metrics from raw log entries.
    Assumes logs contain: problem_size, success, wall_clock_time, energy_joules
    """
    metrics = []
    for log in logs:
        try:
            metric = ExperimentMetrics(
                experiment_id=log.get('experiment_id', 'unknown'),
                problem_size=int(log.get('problem_size', 0)),
                success=bool(log.get('success', False)),
                wall_clock_time=float(log.get('wall_clock_time', 0.0)),
                energy_joules=float(log.get('energy_joules', 0.0))
            )
            metrics.append(metric)
        except (ValueError, TypeError) as e:
            # Skip malformed entries
            continue
    return metrics

def save_metrics_to_csv(metrics: List[ExperimentMetrics], output_path: Path) -> None:
    """Save metrics to a CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        'experiment_id', 'problem_size', 'success', 
        'wall_clock_time', 'energy_joules', 'complexity_class'
    ]
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for m in metrics:
            writer.writerow(asdict(m))

def perform_scaling_analysis(metrics: List[ExperimentMetrics], output_path: Path) -> None:
    """
    Perform log-log linear regression to determine complexity class.
    
    Steps:
    1. Filter successful runs (optional, but typical for complexity analysis).
    2. Log-transform problem_size and wall_clock_time.
    3. Perform linear regression: log(time) = m * log(size) + c.
    4. Classify complexity based on slope 'm':
       - m ~ 1.0 -> O(n)
       - m ~ 2.0 -> O(n^2)
       - m ~ 3.0 -> O(n^3)
       - m > 10.0 -> Exponential (approx)
       - else -> Unknown
    5. Save results to CSV with 'complexity_class' column.
    """
    if not metrics:
        raise ValueError("No metrics provided for scaling analysis.")

    # Filter for successful runs to analyze performance complexity
    successful_metrics = [m for m in metrics if m.success]
    
    if len(successful_metrics) < 2:
        # Not enough data points for regression
        # Fallback to marking all as 'Unknown' or just copy without classification
        for m in successful_metrics:
            m.complexity_class = "Unknown"
        save_metrics_to_csv(successful_metrics, output_path)
        return

    # Prepare data for regression
    x_vals = [] # log(problem_size)
    y_vals = [] # log(wall_clock_time)
    
    valid_points = []
    
    for m in successful_metrics:
        if m.problem_size > 0 and m.wall_clock_time > 0:
            x_vals.append(math.log(m.problem_size))
            y_vals.append(math.log(m.wall_clock_time))
            valid_points.append(m)
    
    if len(valid_points) < 2:
        for m in valid_points:
            m.complexity_class = "Unknown"
        save_metrics_to_csv(valid_points, output_path)
        return

    # Linear Regression: y = mx + c
    n = len(x_vals)
    sum_x = sum(x_vals)
    sum_y = sum(y_vals)
    sum_xy = sum(x * y for x, y in zip(x_vals, y_vals))
    sum_x2 = sum(x * x for x in x_vals)
    
    denominator = n * sum_x2 - sum_x * sum_x
    if denominator == 0:
        slope = 0.0
    else:
        slope = (n * sum_xy - sum_x * sum_y) / denominator
    
    # Classify complexity based on slope
    # Thresholds: |slope - 1| < 0.2 -> O(n), |slope - 2| < 0.2 -> O(n^2), etc.
    complexity_class = "Unknown"
    
    if abs(slope - 1.0) < 0.25:
        complexity_class = "O(n)"
    elif abs(slope - 2.0) < 0.25:
        complexity_class = "O(n^2)"
    elif abs(slope - 3.0) < 0.25:
        complexity_class = "O(n^3)"
    elif slope > 5.0:
        complexity_class = "Exponential"
    elif slope < 0.5:
        complexity_class = "O(1)"
    else:
        # Fallback to nearest integer power if within reasonable range
        nearest_power = round(slope)
        if nearest_power > 0:
            complexity_class = f"O(n^{nearest_power})"
    
    # Assign class to all valid points
    for m in valid_points:
        m.complexity_class = complexity_class
    
    # Sort by problem size for cleaner output
    valid_points.sort(key=lambda x: x.problem_size)
    
    save_metrics_to_csv(valid_points, output_path)

def main():
    """
    Main entry point for scaling analysis.
    Reads logs, performs regression, and saves results to data/processed/scaling_analysis.csv
    """
    log_path = Path("data/processed/experiment.log")
    output_path = Path("data/processed/scaling_analysis.csv")
    
    if not log_path.exists():
        print(f"Error: Log file not found at {log_path}")
        return
    
    try:
        logs = load_experiment_logs(log_path)
        metrics = calculate_metrics_from_logs(logs)
        perform_scaling_analysis(metrics, output_path)
        print(f"Scaling analysis complete. Results saved to {output_path}")
    except Exception as e:
        print(f"Error during scaling analysis: {e}")
        raise

if __name__ == "__main__":
    main()