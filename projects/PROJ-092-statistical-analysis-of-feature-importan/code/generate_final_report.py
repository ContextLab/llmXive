import os
import sys
import json
import logging
from pathlib import Path
import csv

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import get_logger

# Configure logger
logger = get_logger("generate_final_report")

def load_drift_metrics(csv_path: str) -> list:
    """
    Load drift metrics from CSV file.
    Returns a list of dictionaries containing rho, p_value, etc.
    """
    if not os.path.exists(csv_path):
        logger.error(f"Drift metrics file not found: {csv_path}")
        return []
    
    metrics = []
    with open(csv_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                metrics.append({
                    'window_t': row.get('window_t', ''),
                    'window_t_plus_1': row.get('window_t_plus_1', ''),
                    'rho': float(row.get('rho', 0.0)),
                    'p_value': float(row.get('p_value', 1.0))
                })
            except ValueError as e:
                logger.warning(f"Skipping invalid row in drift metrics: {e}")
                continue
    return metrics

def load_stability_report(json_path: str) -> dict:
    """
    Load stability report from JSON file.
    Returns dictionary containing stable_window_count, etc.
    """
    if not os.path.exists(json_path):
        logger.error(f"Stability report file not found: {json_path}")
        return {}
    
    try:
        with open(json_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse stability report JSON: {e}")
        return {}

def aggregate_global_stats(drift_metrics: list, stability_report: dict) -> dict:
    """
    Compute global statistics from drift metrics and stability report.
    Returns a dictionary with keys: mean_rho, trend_direction, p_value, stable_window_count.
    """
    stats = {
        'mean_rho': 0.0,
        'trend_direction': 'unknown',
        'p_value': 1.0,
        'stable_window_count': 0
    }

    # Calculate mean_rho
    if drift_metrics:
        rhos = [m['rho'] for m in drift_metrics if m['rho'] is not None]
        if rhos:
            stats['mean_rho'] = sum(rhos) / len(rhos)

    # Determine trend_direction from stability report or drift metrics
    # Priority: Use explicit trend direction from stability report if available
    if stability_report and 'trend_direction' in stability_report:
        stats['trend_direction'] = stability_report['trend_direction']
    elif drift_metrics:
        # Fallback: infer from mean_rho if no explicit direction
        # Note: In a full implementation, this would come from Mann-Kendall test
        # For now, we assume 'stable' if mean_rho is high, 'decreasing' if low
        # This is a placeholder logic; actual direction should come from T022/T024
        if stats['mean_rho'] > 0.5:
            stats['trend_direction'] = 'stable'
        elif stats['mean_rho'] < -0.5:
            stats['trend_direction'] = 'monotonic decrease'
        else:
            stats['trend_direction'] = 'fluctuating'

    # Extract p_value from stability report (aggregated from T023)
    if stability_report and 'p_value' in stability_report:
        stats['p_value'] = stability_report['p_value']
    elif drift_metrics:
        # Fallback: use minimum p_value from drift metrics if no aggregate available
        p_values = [m['p_value'] for m in drift_metrics if m['p_value'] is not None]
        if p_values:
            stats['p_value'] = min(p_values)

    # Extract stable_window_count from stability report
    if stability_report and 'stable_window_count' in stability_report:
        stats['stable_window_count'] = stability_report['stable_window_count']
    
    return stats

def save_final_report(stats: dict, output_path: str) -> None:
    """
    Save the aggregated global statistics to a JSON file.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Final report saved to {output_path}")

def run_report_generation(drift_metrics_path: str, stability_report_path: str, output_path: str) -> dict:
    """
    Main function to orchestrate report generation.
    Loads inputs, aggregates stats, and saves the final report.
    """
    logger.info("Starting final report generation")
    
    drift_metrics = load_drift_metrics(drift_metrics_path)
    if not drift_metrics:
        logger.warning("No drift metrics found, proceeding with empty list")
    
    stability_report = load_stability_report(stability_report_path)
    if not stability_report:
        logger.warning("No stability report found, proceeding with empty dict")
    
    stats = aggregate_global_stats(drift_metrics, stability_report)
    save_final_report(stats, output_path)
    
    return stats

def main():
    """
    Entry point for the script.
    Expects environment variables or defaults for paths.
    """
    # Default paths relative to project root
    drift_metrics_path = os.environ.get('DRIFT_METRICS_PATH', 'outputs/drift_metrics.csv')
    stability_report_path = os.environ.get('STABILITY_REPORT_PATH', 'outputs/stability_report.json')
    output_path = os.environ.get('FINAL_REPORT_PATH', 'outputs/global_stats.json')
    
    # Resolve relative paths against project root if not absolute
    if not os.path.isabs(drift_metrics_path):
        drift_metrics_path = os.path.join(PROJECT_ROOT, drift_metrics_path)
    if not os.path.isabs(stability_report_path):
        stability_report_path = os.path.join(PROJECT_ROOT, stability_report_path)
    if not os.path.isabs(output_path):
        output_path = os.path.join(PROJECT_ROOT, output_path)
    
    logger.info(f"Loading drift metrics from: {drift_metrics_path}")
    logger.info(f"Loading stability report from: {stability_report_path}")
    logger.info(f"Saving final report to: {output_path}")
    
    run_report_generation(drift_metrics_path, stability_report_path, output_path)
    logger.info("Final report generation completed")

if __name__ == "__main__":
    main()
