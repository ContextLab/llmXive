import json
import os
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any

from config import get_results_dir

logger = logging.getLogger(__name__)

def load_results_from_log(log_path: Path) -> List[Dict[str, Any]]:
    """Load simulation results from the JSON log file."""
    if not log_path.exists():
        raise FileNotFoundError(f"Log file not found: {log_path}")
    with open(log_path, 'r') as f:
        return json.load(f)

def aggregate_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate results into the format required for coverage_metrics.csv."""
    # The runner already aggregates per (phi, n) in run_paired_trial
    # So we just need to format them for CSV
    aggregated = []
    for res in results:
        if res.get('condition') == 'paired':
            aggregated.append({
                'phi': res['phi'],
                'n': res['n'],
                'ordered_cov': res['ordered_coverage'],
                'shuffled_cov': res['shuffled_coverage'],
                'diff': res['diff'],
                'p_value': res['p_value']
            })
    return aggregated

def write_csv(aggregated: List[Dict[str, Any]], csv_path: Path) -> None:
    """Write aggregated results to CSV."""
    if not aggregated:
        logger.warning("No data to write to CSV.")
        return

    fieldnames = ['phi', 'n', 'ordered_cov', 'shuffled_cov', 'diff', 'p_value']
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in aggregated:
            # Format p_value to 6 decimal places
            row['p_value'] = f"{row['p_value']:.6f}"
            writer.writerow(row)
    logger.info(f"CSV written to {csv_path}")

def main():
    """Main entry point to generate the metrics CSV."""
    results_dir = get_results_dir()
    log_path = results_dir / "simulation_logs.json"
    csv_path = results_dir / "coverage_metrics.csv"

    try:
        results = load_results_from_log(log_path)
        aggregated = aggregate_results(results)
        write_csv(aggregated, csv_path)
    except Exception as e:
        logger.error(f"Failed to generate metrics CSV: {e}")
        raise

if __name__ == "__main__":
    main()