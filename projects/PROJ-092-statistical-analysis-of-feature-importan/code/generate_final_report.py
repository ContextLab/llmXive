import os
import sys
import json
import logging
from pathlib import Path
import csv

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logger import get_logger
from utils.config import get_config

logger = get_logger(__name__)
config = get_config()

def load_drift_metrics(filepath: Path) -> list:
    """
    Load drift metrics from CSV.
    Returns a list of dictionaries containing drift data.
    """
    if not filepath.exists():
        logger.error(f"Drift metrics file not found: {filepath}")
        return []
    
    metrics = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric strings to floats
            row_data = {}
            for k, v in row.items():
                if k in ['rho', 'p_value']:
                    try:
                        row_data[k] = float(v)
                    except ValueError:
                        row_data[k] = None
                else:
                    row_data[k] = v
            metrics.append(row_data)
    return metrics

def load_stability_report(filepath: Path) -> dict:
    """
    Load stability report from JSON.
    Returns a dictionary containing stability metrics.
    """
    if not filepath.exists():
        logger.error(f"Stability report file not found: {filepath}")
        return {}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def aggregate_global_stats(drift_metrics: list, stability_report: dict) -> dict:
    """
    Aggregate global statistics from drift metrics and stability report.
    
    Returns a dictionary with keys:
    - mean_rho: float (average of all rho values)
    - trend_direction: str (from Mann-Kendall test result in drift metrics)
    - p_value: float (block permutation p-value)
    - stable_window_count: int (from stability report)
    """
    if not drift_metrics:
        logger.warning("No drift metrics found for aggregation.")
        return {
            "mean_rho": 0.0,
            "trend_direction": "insufficient_data",
            "p_value": 1.0,
            "stable_window_count": 0
        }

    # Calculate mean_rho
    rhos = [m['rho'] for m in drift_metrics if m.get('rho') is not None]
    mean_rho = sum(rhos) / len(rhos) if rhos else 0.0

    # Determine trend_direction
    # Look for the most recent or first entry with a trend direction if available
    # Usually the Mann-Kendall result is aggregated or stored in the last row or a specific column
    # Based on T025 integration, we assume the last row or a specific 'trend_direction' key exists
    trend_direction = "unknown"
    for m in reversed(drift_metrics):
        if m.get('trend_direction'):
            trend_direction = m['trend_direction']
            break
    
    # If not found in rows, default based on mean_rho sign if available
    if trend_direction == "unknown":
        if mean_rho < 0:
            trend_direction = "monotonic decrease"
        elif mean_rho > 0:
            trend_direction = "monotonic increase"
        else:
            trend_direction = "no trend"

    # Get p_value (block permutation)
    # Assume it's stored in the last row or a dedicated column
    p_value = 1.0
    for m in reversed(drift_metrics):
        if m.get('p_value') is not None:
            p_value = m['p_value']
            break

    # Get stable_window_count from stability report
    stable_window_count = stability_report.get('stable_window_count', 0)

    return {
        "mean_rho": round(mean_rho, 6),
        "trend_direction": trend_direction,
        "p_value": round(p_value, 6),
        "stable_window_count": stable_window_count
    }

def save_final_report(stats: dict, filepath: Path) -> None:
    """
    Save the aggregated global statistics to a JSON file.
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Final report saved to {filepath}")

def run_report_generation(output_dir: Path) -> dict:
    """
    Main logic to generate the final report.
    Loads drift_metrics.csv and stability report, aggregates stats, saves global_stats.json.
    """
    drift_metrics_path = output_dir / "drift_metrics.csv"
    stability_report_path = output_dir / "stability_report.json"
    final_report_path = output_dir / "global_stats.json"

    logger.info("Starting final report generation...")

    drift_metrics = load_drift_metrics(drift_metrics_path)
    stability_report = load_stability_report(stability_report_path)

    if not drift_metrics and not stability_report:
        logger.error("No input data found to generate report.")
        return {}

    stats = aggregate_global_stats(drift_metrics, stability_report)
    save_final_report(stats, final_report_path)

    return stats

def main():
    """
    Entry point for the script.
    """
    config = get_config()
    output_dir = Path(config.get('paths.output_dir', 'outputs'))
    
    if not output_dir.exists():
        logger.error(f"Output directory does not exist: {output_dir}")
        sys.exit(1)

    try:
        stats = run_report_generation(output_dir)
        if stats:
            print(json.dumps(stats, indent=2))
            sys.exit(0)
        else:
            logger.error("Report generation failed to produce results.")
            sys.exit(1)
    except Exception as e:
        logger.exception(f"Error during report generation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()