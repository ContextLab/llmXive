"""
Metrics calculation module for US3.
Calculates success rates, wall-clock time, and energy consumption from execution logs.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
import csv

# Constants for energy estimation (approximate TDP based power draw)
# These are rough estimates for CPU-bound inference on a standard server node
# Adjust based on actual hardware profiling if available
DEFAULT_CPU_POWER_WATTS = 65.0  # Watts
DEFAULT_GPU_POWER_WATTS = 0.0   # Not used in CPU-only mode per constraints

@dataclass
class ExperimentMetrics:
    """Container for calculated experiment metrics."""
    experiment_id: str
    total_runs: int
    successful_runs: int
    success_rate: float
    avg_wall_clock_seconds: float
    total_wall_clock_seconds: float
    avg_energy_joules: float
    total_energy_joules: float
    method: str  # 'symbolic' or 'neural'
    
def load_experiment_logs(log_dir: str) -> List[Dict[str, Any]]:
    """
    Load all JSON log files from the specified directory.
    
    Args:
        log_dir: Path to the directory containing experiment logs.
        
    Returns:
        List of log entries as dictionaries.
    """
    log_path = Path(log_dir)
    if not log_path.exists():
        raise FileNotFoundError(f"Log directory not found: {log_dir}")
        
    logs = []
    for file_path in log_path.glob("*.json"):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                # Handle both single-entry files and list-of-entries files
                if isinstance(data, list):
                    logs.extend(data)
                else:
                    logs.append(data)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not parse {file_path}: {e}")
            
    return logs

def calculate_metrics_from_logs(
    logs: List[Dict[str, Any]], 
    method: str = "symbolic"
) -> ExperimentMetrics:
    """
    Calculate aggregate metrics from a list of log entries.
    
    Args:
        logs: List of log entries (dictionaries).
        method: Label for the method used ('symbolic' or 'neural').
        
    Returns:
        ExperimentMetrics object with calculated values.
    """
    if not logs:
        return ExperimentMetrics(
            experiment_id="unknown",
            total_runs=0,
            successful_runs=0,
            success_rate=0.0,
            avg_wall_clock_seconds=0.0,
            total_wall_clock_seconds=0.0,
            avg_energy_joules=0.0,
            total_energy_joules=0.0,
            method=method
        )

    total_runs = len(logs)
    successful_runs = 0
    total_wall_clock = 0.0
    total_energy = 0.0

    for entry in logs:
        # Determine success
        # Log format typically includes 'success', 'status', or 'result'
        is_success = False
        if 'success' in entry:
            is_success = bool(entry['success'])
        elif 'status' in entry:
            is_success = entry['status'] == 'success'
        elif 'result' in entry:
            is_success = entry['result'].get('valid', False)
        
        if is_success:
            successful_runs += 1

        # Accumulate wall-clock time
        # Look for 'wall_clock', 'duration', or 'time' fields
        wall_clock = 0.0
        if 'wall_clock' in entry:
            wall_clock = float(entry['wall_clock'])
        elif 'duration' in entry:
            wall_clock = float(entry['duration'])
        elif 'time' in entry:
            wall_clock = float(entry['time'])
        
        total_wall_clock += wall_clock

        # Accumulate energy (if available in logs)
        # If not directly available, estimate based on wall-clock and power
        energy = 0.0
        if 'energy_joules' in entry:
            energy = float(entry['energy_joules'])
        elif wall_clock > 0:
            # Estimate energy: Power (Watts) * Time (Seconds) = Energy (Joules)
            # Using a conservative CPU power estimate for the active period
            power_watts = DEFAULT_CPU_POWER_WATTS
            energy = wall_clock * power_watts
        
        total_energy += energy

    success_rate = successful_runs / total_runs if total_runs > 0 else 0.0
    avg_wall_clock = total_wall_clock / total_runs if total_runs > 0 else 0.0
    avg_energy = total_energy / total_runs if total_runs > 0 else 0.0

    # Extract experiment ID if available, otherwise generate one
    exp_id = logs[0].get('experiment_id', 'unknown') if logs else 'unknown'

    return ExperimentMetrics(
        experiment_id=exp_id,
        total_runs=total_runs,
        successful_runs=successful_runs,
        success_rate=success_rate,
        avg_wall_clock_seconds=avg_wall_clock,
        total_wall_clock_seconds=total_wall_clock,
        avg_energy_joules=avg_energy,
        total_energy_joules=total_energy,
        method=method
    )

def save_metrics_to_csv(metrics_list: List[ExperimentMetrics], output_path: str) -> None:
    """
    Save a list of metrics to a CSV file.
    
    Args:
        metrics_list: List of ExperimentMetrics objects.
        output_path: Path to the output CSV file.
    """
    if not metrics_list:
        return

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        'experiment_id', 'method', 'total_runs', 'successful_runs', 
        'success_rate', 'avg_wall_clock_seconds', 'total_wall_clock_seconds',
        'avg_energy_joules', 'total_energy_joules'
    ]

    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for metrics in metrics_list:
            writer.writerow(asdict(metrics))

def main():
    """
    Main entry point to calculate and save metrics from experiment logs.
    Reads from data/processed/experiment.log (JSON lines) or directory.
    Outputs to data/processed/metrics_summary.csv.
    """
    # Default paths based on project structure
    log_dir = "data/processed"
    output_path = "data/processed/metrics_summary.csv"
    
    # Check for specific log file or directory
    log_file = Path(log_dir) / "experiment.log"
    if log_file.exists():
        # If it's a single JSON lines file or a single JSON object
        try:
            with open(log_file, 'r') as f:
                content = f.read().strip()
                if content.startswith('['):
                    logs = json.loads(content)
                else:
                    # Assume JSON lines or single object
                    logs = [json.loads(line) for line in content.split('\n') if line.strip()]
        except json.JSONDecodeError:
            # Fallback to treating it as a directory or error
            print(f"Error parsing {log_file}, trying directory scan...")
            logs = load_experiment_logs(log_dir)
    else:
        logs = load_experiment_logs(log_dir)

    if not logs:
        print("No valid logs found to process.")
        return

    # Group logs by method if possible, or process all as one
    # Assuming logs have a 'method' or 'type' field, or we infer from filename/path
    # For simplicity, we'll calculate metrics for the whole batch if method isn't explicit
    # or split if we detect multiple methods in the data.
    
    # Simple heuristic: if logs have 'method' field, group by it.
    # Otherwise, assume all are 'symbolic' (default for this project phase)
    grouped_logs = {}
    for log in logs:
        method = log.get('method', 'symbolic') # Default to symbolic if missing
        if method not in grouped_logs:
            grouped_logs[method] = []
        grouped_logs[method].append(log)

    metrics_list = []
    for method, method_logs in grouped_logs.items():
        metrics = calculate_metrics_from_logs(method_logs, method=method)
        metrics_list.append(metrics)
        print(f"Calculated metrics for {method}: Success Rate={metrics.success_rate:.2%}, "
              f"Avg Time={metrics.avg_wall_clock_seconds:.2f}s, Avg Energy={metrics.avg_energy_joules:.2f}J")

    save_metrics_to_csv(metrics_list, output_path)
    print(f"Metrics saved to {output_path}")

if __name__ == "__main__":
    main()
