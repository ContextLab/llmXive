"""
Performance monitoring module for the Socio-Cognitive State Injection pipeline.

Calculates throughput and latency metrics from experiment logs and enforces
build-fail criteria based on SC-003.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Import shared config for paths
# Note: Using relative import based on project structure assumptions
# If run as script, we adjust sys.path
try:
    from config import get_config_summary, ensure_directories
except ImportError:
    # Fallback for direct execution without package structure
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import get_config_summary, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants from SC-003
MIN_THROUGHPUT_TRAJECTORIES_PER_HOUR = 40.0
MAX_LATENCY_SECONDS_PER_TRAJECTORY = 45.0

def load_experiment_logs(log_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load experiment logs from the specified JSON file.

    Args:
        log_path: Path to the experiment_logs.json file. Defaults to
                  data/processed/experiment_logs.json based on config.

    Returns:
        List of log entries.

    Raises:
        FileNotFoundError: If the log file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if log_path is None:
        # Default path construction
        base_dir = Path(__file__).parent.parent.parent
        log_path = base_dir / "data" / "processed" / "experiment_logs.json"

    if not log_path.exists():
        raise FileNotFoundError(f"Experiment logs not found at {log_path}. "
                                "Ensure T028 has been completed and the file exists.")

    with open(log_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        logger.warning(f"Expected list of logs at {log_path}, got {type(data)}. "
                       "Attempting to unwrap if it's a dict with a 'logs' key.")
        if isinstance(data, dict) and 'logs' in data:
            data = data['logs']
        else:
            raise ValueError("Log file must contain a list of trajectory logs or a dict with 'logs' key.")

    return data

def calculate_metrics(logs: List[Dict[str, Any]]) -> Tuple[float, float, int]:
    """
    Calculate throughput and latency from experiment logs.

    Args:
        logs: List of log entries containing 'start_time', 'end_time', 'trajectory_id'.

    Returns:
        Tuple of (throughput, latency, total_trajectories).
        throughput: trajectories per hour.
        latency: average seconds per trajectory.
        total_trajectories: count of processed trajectories.
    """
    if not logs:
        logger.warning("No logs provided. Returning zero metrics.")
        return 0.0, 0.0, 0

    total_duration_seconds = 0.0
    valid_count = 0

    for entry in logs:
        start_str = entry.get('start_time')
        end_str = entry.get('end_time')

        if not start_str or not end_str:
            logger.warning(f"Skipping log entry missing timestamps: {entry.get('trajectory_id', 'unknown')}")
            continue

        try:
            start_dt = datetime.fromisoformat(start_str)
            end_dt = datetime.fromisoformat(end_str)
            duration = (end_dt - start_dt).total_seconds()
            total_duration_seconds += duration
            valid_count += 1
        except ValueError as e:
            logger.warning(f"Invalid timestamp format in log entry: {e}")
            continue

    if valid_count == 0:
        logger.error("No valid log entries with timestamps found.")
        return 0.0, 0.0, 0

    # Calculate average latency (seconds per trajectory)
    avg_latency = total_duration_seconds / valid_count

    # Calculate throughput (trajectories per hour)
    # Throughput = (Count / Total Seconds) * 3600
    total_hours = total_duration_seconds / 3600.0
    throughput = valid_count / total_hours if total_hours > 0 else 0.0

    return throughput, avg_latency, valid_count

def verify_metrics(throughput: float, latency: float) -> bool:
    """
    Verify metrics against SC-003 requirements.

    Args:
        throughput: Trajectories per hour.
        latency: Seconds per trajectory.

    Returns:
        True if metrics meet requirements, False otherwise.
    """
    logger.info(f"Verifying metrics: Throughput={throughput:.2f} traj/hr, Latency={latency:.2f} s/traj")
    logger.info(f"Thresholds: Min Throughput={MIN_THROUGHPUT_TRAJECTORIES_PER_HOUR}, Max Latency={MAX_LATENCY_SECONDS_PER_TRAJECTORY}")

    passed_throughput = throughput >= MIN_THROUGHPUT_TRAJECTORIES_PER_HOUR
    passed_latency = latency <= MAX_LATENCY_SECONDS_PER_TRAJECTORY

    if passed_throughput and passed_latency:
        logger.info("SUCCESS: All performance criteria met.")
        return True
    else:
        reasons = []
        if not passed_throughput:
            reasons.append(f"Throughput {throughput:.2f} < {MIN_THROUGHPUT_TRAJECTORIES_PER_HOUR}")
        if not passed_latency:
            reasons.append(f"Latency {latency:.2f} > {MAX_LATENCY_SECONDS_PER_TRAJECTORY}")

        logger.error(f"FAILURE: Performance criteria not met. Reasons: {'; '.join(reasons)}")
        return False

def generate_report(throughput: float, latency: float, count: int, passed: bool) -> Dict[str, Any]:
    """
    Generate a structured performance report.

    Args:
        throughput: Calculated throughput.
        latency: Calculated latency.
        count: Number of trajectories processed.
        passed: Whether verification passed.

    Returns:
        Dictionary containing the report data.
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "metrics": {
            "throughput_trajectories_per_hour": throughput,
            "latency_seconds_per_trajectory": latency,
            "total_trajectories_processed": count
        },
        "thresholds": {
            "min_throughput": MIN_THROUGHPUT_TRAJECTORIES_PER_HOUR,
            "max_latency": MAX_LATENCY_SECONDS_PER_TRAJECTORY
        },
        "verification": {
            "passed": passed,
            "criteria": {
                "throughput_check": throughput >= MIN_THROUGHPUT_TRAJECTORIES_PER_HOUR,
                "latency_check": latency <= MAX_LATENCY_SECONDS_PER_TRAJECTORY
            }
        }
    }
    return report

def main():
    """
    Main entry point for performance monitoring.
    Loads logs, calculates metrics, verifies against thresholds,
    and exits with code 1 if verification fails.
    """
    logger.info("Starting Performance Monitor (T042)...")

    try:
        logs = load_experiment_logs()
        logger.info(f"Loaded {len(logs)} log entries.")

        throughput, latency, count = calculate_metrics(logs)
        logger.info(f"Calculated metrics: Throughput={throughput:.2f}, Latency={latency:.2f}, Count={count}")

        passed = verify_metrics(throughput, latency)
        report = generate_report(throughput, latency, count, passed)

        # Save report to data/results
        ensure_directories()
        base_dir = Path(__file__).parent.parent.parent
        results_dir = base_dir / "data" / "results"
        results_dir.mkdir(parents=True, exist_ok=True)

        report_path = results_dir / "performance_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Report saved to {report_path}")

        if not passed:
            logger.error("Performance verification failed. Exiting with code 1.")
            sys.exit(1)
        else:
            logger.info("Performance verification passed. Exiting with code 0.")
            sys.exit(0)

    except FileNotFoundError as e:
        logger.error(f"Data file error: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during performance monitoring: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()