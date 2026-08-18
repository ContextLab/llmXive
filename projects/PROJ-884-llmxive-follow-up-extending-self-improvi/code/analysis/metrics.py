"""
Metrics calculation module for BES experiments.

Calculates success rates, wall-clock time, and energy consumption (Joules)
from execution logs. Also performs scaling analysis to determine complexity classes.
"""
import json
import os
import math
import csv
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

# Import from local project structure
from code.utils.logger import setup_logging

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ExperimentMetrics:
    """Dataclass to hold calculated metrics for an experiment."""
    experiment_id: str
    success_rate: float
    avg_wall_clock_seconds: float
    total_wall_clock_seconds: float
    avg_energy_joules: float
    total_energy_joules: float
    total_puzzles: int
    successful_puzzles: int
    failed_puzzles: int
    avg_time_per_puzzle_seconds: float
    complexity_class: Optional[str] = None
    scaling_slope: Optional[float] = None
    r_squared: Optional[float] = None


def load_experiment_logs(logs_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all experiment log files from the specified directory.

    Args:
        logs_dir: Path to the directory containing experiment logs.

    Returns:
        List of dictionaries, each representing a log entry.
    """
    logs = []
    if not logs_dir.exists():
        logger.warning(f"Logs directory does not exist: {logs_dir}")
        return logs

    for log_file in logs_dir.glob("*.log"):
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        logs.append(entry)
                    except json.JSONDecodeError:
                        logger.warning(f"Skipping invalid JSON line in {log_file}: {line[:50]}...")
        except Exception as e:
            logger.error(f"Error reading log file {log_file}: {e}")

    return logs


def calculate_metrics_from_logs(logs: List[Dict[str, Any]]) -> ExperimentMetrics:
    """
    Calculate metrics from a list of log entries.

    Args:
        logs: List of log entry dictionaries.

    Returns:
        ExperimentMetrics object with calculated values.
    """
    if not logs:
        logger.warning("No logs provided, returning default metrics")
        return ExperimentMetrics(
            experiment_id="unknown",
            success_rate=0.0,
            avg_wall_clock_seconds=0.0,
            total_wall_clock_seconds=0.0,
            avg_energy_joules=0.0,
            total_energy_joules=0.0,
            total_puzzles=0,
            successful_puzzles=0,
            failed_puzzles=0,
            avg_time_per_puzzle_seconds=0.0
        )

    # Filter for puzzle execution entries
    puzzle_logs = [
        log for log in logs
        if log.get('event') == 'puzzle_solved' or log.get('event') == 'puzzle_failed'
    ]

    total_puzzles = len(puzzle_logs)
    successful_puzzles = sum(1 for log in puzzle_logs if log.get('success', False))
    failed_puzzles = total_puzzles - successful_puzzles

    success_rate = successful_puzzles / total_puzzles if total_puzzles > 0 else 0.0

    # Calculate wall-clock times
    wall_clock_times = []
    energy_values = []

    for log in puzzle_logs:
        if 'wall_clock_seconds' in log:
            wall_clock_times.append(log['wall_clock_seconds'])
        if 'energy_joules' in log:
            energy_values.append(log['energy_joules'])

    total_wall_clock = sum(wall_clock_times)
    avg_wall_clock = total_wall_clock / len(wall_clock_times) if wall_clock_times else 0.0
    avg_time_per_puzzle = total_wall_clock / total_puzzles if total_puzzles > 0 else 0.0

    total_energy = sum(energy_values)
    avg_energy = total_energy / len(energy_values) if energy_values else 0.0

    # Extract experiment ID from logs if available
    experiment_id = "unknown"
    for log in logs:
        if 'experiment_id' in log:
            experiment_id = log['experiment_id']
            break

    return ExperimentMetrics(
        experiment_id=experiment_id,
        success_rate=success_rate,
        avg_wall_clock_seconds=avg_wall_clock,
        total_wall_clock_seconds=total_wall_clock,
        avg_energy_joules=avg_energy,
        total_energy_joules=total_energy,
        total_puzzles=total_puzzles,
        successful_puzzles=successful_puzzles,
        failed_puzzles=failed_puzzles,
        avg_time_per_puzzle_seconds=avg_time_per_puzzle
    )


def save_metrics_to_csv(metrics: ExperimentMetrics, output_path: Path) -> None:
    """
    Save metrics to a CSV file.

    Args:
        metrics: ExperimentMetrics object to save.
        output_path: Path to the output CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow([
            'experiment_id', 'success_rate', 'avg_wall_clock_seconds',
            'total_wall_clock_seconds', 'avg_energy_joules', 'total_energy_joules',
            'total_puzzles', 'successful_puzzles', 'failed_puzzles',
            'avg_time_per_puzzle_seconds', 'complexity_class', 'scaling_slope', 'r_squared'
        ])
        # Write data
        writer.writerow([
            metrics.experiment_id,
            metrics.success_rate,
            metrics.avg_wall_clock_seconds,
            metrics.total_wall_clock_seconds,
            metrics.avg_energy_joules,
            metrics.total_energy_joules,
            metrics.total_puzzles,
            metrics.successful_puzzles,
            metrics.failed_puzzles,
            metrics.avg_time_per_puzzle_seconds,
            metrics.complexity_class,
            metrics.scaling_slope,
            metrics.r_squared
        ])

    logger.info(f"Metrics saved to {output_path}")


def perform_scaling_analysis(
    logs: List[Dict[str, Any]],
    output_path: Path
) -> Tuple[Optional[str], Optional[float], Optional[float]]:
    """
    Perform scaling analysis to determine complexity class via log-log linear regression.

    Args:
        logs: List of log entries containing puzzle size and execution time.
        output_path: Path to save the scaling analysis CSV.

    Returns:
        Tuple of (complexity_class, slope, r_squared) or (None, None, None) if insufficient data.
    """
    # Extract (size, time) pairs
    data_points = []
    for log in logs:
        if log.get('event') in ['puzzle_solved', 'puzzle_failed']:
            size = log.get('puzzle_size')
            time_val = log.get('wall_clock_seconds')
            if size is not None and time_val is not None and size > 0 and time_val > 0:
                data_points.append((size, time_val))

    if len(data_points) < 3:
        logger.warning("Insufficient data points for scaling analysis")
        return None, None, None

    # Log-log transformation
    log_sizes = [math.log10(size) for size, _ in data_points]
    log_times = [math.log10(time) for _, time in data_points]

    n = len(log_sizes)
    sum_x = sum(log_sizes)
    sum_y = sum(log_times)
    sum_xy = sum(x * y for x, y in zip(log_sizes, log_times))
    sum_x2 = sum(x * x for x in log_sizes)
    sum_y2 = sum(y * y for y in log_times)

    # Linear regression: y = mx + b
    denominator = n * sum_x2 - sum_x * sum_x
    if denominator == 0:
        logger.warning("Zero denominator in regression calculation")
        return None, None, None

    slope = (n * sum_xy - sum_x * sum_y) / denominator
    intercept = (sum_y - slope * sum_x) / n

    # Calculate R-squared
    mean_y = sum_y / n
    ss_tot = sum((y - mean_y) ** 2 for y in log_times)
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(log_sizes, log_times))

    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    # Determine complexity class based on slope thresholds
    # slope < 1.2 -> O(n)
    # 1.2 <= slope < 1.8 -> O(n log n)
    # slope >= 1.8 -> O(n^2)
    if slope < 1.2:
        complexity_class = "O(n)"
    elif slope < 1.8:
        complexity_class = "O(n log n)"
    else:
        complexity_class = "O(n^2)"

    # Save analysis to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['puzzle_size', 'wall_clock_seconds', 'log_size', 'log_time'])
        for (size, time_val), log_s, log_t in zip(data_points, log_sizes, log_times):
            writer.writerow([size, time_val, log_s, log_t])

        # Add summary row
        writer.writerow([])
        writer.writerow(['slope', slope])
        writer.writerow(['intercept', intercept])
        writer.writerow(['r_squared', r_squared])
        writer.writerow(['complexity_class', complexity_class])

    logger.info(f"Scaling analysis saved to {output_path}")
    logger.info(f"Complexity class: {complexity_class}, slope: {slope:.4f}, R²: {r_squared:.4f}")

    return complexity_class, slope, r_squared


def main():
    """Main entry point for metrics calculation."""
    setup_logging()

    # Define paths
    project_root = Path(__file__).parent.parent.parent
    logs_dir = project_root / "data" / "processed"
    metrics_output = project_root / "data" / "processed" / "metrics.csv"
    scaling_output = project_root / "data" / "processed" / "scaling_analysis.csv"

    logger.info(f"Loading experiment logs from {logs_dir}")
    logs = load_experiment_logs(logs_dir)

    if not logs:
        logger.error("No logs found. Ensure experiment has been run.")
        return

    logger.info(f"Calculating metrics from {len(logs)} log entries")
    metrics = calculate_metrics_from_logs(logs)

    logger.info(f"Metrics: Success Rate={metrics.success_rate:.2%}, "
                f"Avg Time={metrics.avg_wall_clock_seconds:.3f}s, "
                f"Avg Energy={metrics.avg_energy_joules:.3f}J")

    logger.info("Saving metrics to CSV")
    save_metrics_to_csv(metrics, metrics_output)

    logger.info("Performing scaling analysis")
    complexity_class, slope, r_squared = perform_scaling_analysis(logs, scaling_output)

    if complexity_class:
        logger.info(f"Complexity analysis complete: {complexity_class}")
        # Update metrics with scaling results
        metrics.complexity_class = complexity_class
        metrics.scaling_slope = slope
        metrics.r_squared = r_squared
        save_metrics_to_csv(metrics, metrics_output)
    else:
        logger.warning("Scaling analysis could not be completed (insufficient data)")

    logger.info("Metrics calculation complete")


if __name__ == "__main__":
    main()