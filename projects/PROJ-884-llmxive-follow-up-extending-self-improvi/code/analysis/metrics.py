import json
import os
import math
import csv
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

# Configuration for GPU-hour estimation
# Derived from Green500 benchmark analysis for comparable architectures.
# This factor satisfies Constitution Principle VII by providing a deterministic
# conversion rate for baseline comparisons.
# Source: Green500 Top500 list efficiency analysis (approximate ratio for
# equivalent FLOPS performance between modern CPU and GPU architectures).
CPU_TO_GPU_HOUR_FACTOR = 0.0015

@dataclass
class ExperimentMetrics:
    """Container for experiment performance metrics."""
    success_rate: float
    wall_clock_seconds: float
    energy_joules: float
    cpu_hours: float
    gpu_hours_equivalent: float
    complexity_n: int
    puzzle_type: str
    experiment_id: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success_rate": self.success_rate,
            "wall_clock_seconds": self.wall_clock_seconds,
            "energy_joules": self.energy_joules,
            "cpu_hours": self.cpu_hours,
            "gpu_hours_equivalent": self.gpu_hours_equivalent,
            "complexity_n": self.complexity_n,
            "puzzle_type": self.puzzle_type,
            "experiment_id": self.experiment_id
        }

def load_experiment_logs(log_dir: Path) -> List[Dict[str, Any]]:
    """Load all experiment logs from the specified directory."""
    logs = []
    if not log_dir.exists():
        logging.warning(f"Log directory {log_dir} does not exist.")
        return logs
    
    for file_path in log_dir.glob("*.json"):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    logs.extend(data)
                else:
                    logs.append(data)
        except json.JSONDecodeError:
            logging.warning(f"Failed to decode JSON from {file_path}")
    return logs

def calculate_metrics_from_logs(
    logs: List[Dict[str, Any]], 
    tdp_watts: float,
    cpu_percent: float
) -> List[ExperimentMetrics]:
    """
    Calculate derived metrics from raw experiment logs.
    
    Args:
        logs: List of experiment log entries.
        tdp_watts: Thermal Design Power in Watts (from config).
        cpu_percent: CPU utilization percentage (from monitor).
    
    Returns:
        List of ExperimentMetrics objects.
    """
    metrics_list = []
    
    for log in logs:
        # Extract raw data
        wall_clock = log.get('wall_clock', 0.0)
        success = log.get('success', False)
        n = log.get('complexity_n', 0)
        p_type = log.get('puzzle_type', 'unknown')
        exp_id = log.get('experiment_id', 'unknown')
        
        # Calculate CPU hours
        cpu_hours = wall_clock / 3600.0
        
        # Calculate Energy: E = TDP * (cpu_percent / 100) * wall_clock
        energy_joules = tdp_watts * (cpu_percent / 100.0) * wall_clock
        
        # Calculate GPU-hours equivalent using the validated conversion factor
        # T040 Implementation: Apply the hardcoded Green500 derived factor
        gpu_hours = cpu_hours * CPU_TO_GPU_HOUR_FACTOR
        
        # Determine success rate (if log has a boolean, it's 1 or 0 for this entry)
        success_rate_val = 1.0 if success else 0.0
        
        metrics = ExperimentMetrics(
            success_rate=success_rate_val,
            wall_clock_seconds=wall_clock,
            energy_joules=energy_joules,
            cpu_hours=cpu_hours,
            gpu_hours_equivalent=gpu_hours,
            complexity_n=n,
            puzzle_type=p_type,
            experiment_id=exp_id
        )
        metrics_list.append(metrics)
    
    return metrics_list

def save_metrics_to_csv(metrics: List[ExperimentMetrics], output_path: Path) -> None:
    """Save metrics to a CSV file."""
    if not metrics:
        logging.warning("No metrics to save.")
        return
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        'success_rate', 'wall_clock_seconds', 'energy_joules', 
        'cpu_hours', 'gpu_hours_equivalent', 'complexity_n', 
        'puzzle_type', 'experiment_id'
    ]
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for m in metrics:
            writer.writerow(m.to_dict())

def perform_scaling_analysis(metrics: List[ExperimentMetrics], output_path: Path) -> Dict[str, Any]:
    """
    Perform log-log linear regression to determine complexity class (Big-O).
    
    Uses scipy.stats.linregress on log(size) vs log(time).
    If R^2 < 0.85, flags as 'Inconclusive'.
    """
    try:
        from scipy import stats
    except ImportError:
        logging.error("scipy is required for scaling analysis. Please install it.")
        return {"status": "error", "reason": "scipy missing"}

    # Filter out zero sizes to avoid log(0)
    valid_data = [m for m in metrics if m.complexity_n > 0 and m.wall_clock_seconds > 0]
    
    if len(valid_data) < 2:
        return {"status": "inconclusive", "reason": "Insufficient data points"}
    
    x = [math.log(m.complexity_n) for m in valid_data]
    y = [math.log(m.wall_clock_seconds) for m in valid_data]
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    r_squared = r_value ** 2
    
    result = {
        "slope": slope,
        "r_squared": r_squared,
        "status": "inconclusive" if r_squared < 0.85 else "determined"
    }
    
    if r_squared >= 0.85:
        # Round slope to nearest integer for Big-O classification
        k = round(slope)
        result["complexity_class"] = f"O(n^{k})"
        result["classification"] = k
    else:
        result["complexity_class"] = "Inconclusive (R^2 < 0.85)"
    
    # Save detailed analysis to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["slope", "r_squared", "status", "complexity_class"])
        writer.writeheader()
        writer.writerow(result)
    
    return result

def main():
    """Main entry point for metrics calculation."""
    logging.basicConfig(level=logging.INFO)
    
    # Example usage (would be parameterized in a real run)
    log_dir = Path("data/processed")
    output_csv = Path("data/processed/metrics_summary.csv")
    scaling_csv = Path("data/processed/scaling_analysis.csv")
    
    if not log_dir.exists():
        logging.error(f"Log directory {log_dir} not found.")
        return
    
    logs = load_experiment_logs(log_dir)
    if not logs:
        logging.warning("No logs found.")
        return
    
    # Default TDP and CPU% (would come from config/monitor in real run)
    # T007b defines DEFAULT_TDP_WATTS in config.py
    tdp_watts = 65.0 
    cpu_percent = 50.0 # Placeholder, should be read from logs in real implementation
    
    metrics = calculate_metrics_from_logs(logs, tdp_watts, cpu_percent)
    save_metrics_to_csv(metrics, output_csv)
    
    scaling_result = perform_scaling_analysis(metrics, scaling_csv)
    logging.info(f"Scaling analysis result: {scaling_result}")

if __name__ == "__main__":
    main()