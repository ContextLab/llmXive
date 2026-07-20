import json
import os
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any

from config import get_results_dir

def load_results_from_log(log_path: str) -> List[Dict[str, Any]]:
    """Load simulation results from the JSON log file."""
    if not os.path.exists(log_path):
        raise FileNotFoundError(f"Log file not found: {log_path}")

    with open(log_path, "r") as f:
        return json.load(f)

def aggregate_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Aggregate results into the format required for coverage_metrics.csv.
    Expects 'paired' condition results which already contain aggregated stats.
    """
    # Filter for paired results if mixed
    paired_results = [r for r in results if r.get("condition") == "paired"]

    if not paired_results:
        logging.warning("No paired results found in log file.")
        return []

    # The run_full_batch_paired already aggregates, so we just format
    # Ensure consistent key ordering and formatting
    formatted = []
    for r in paired_results:
        formatted.append({
            "phi": r["phi"],
            "n": r["n"],
            "ordered_cov": round(r["ordered_coverage"], 6),
            "shuffled_cov": round(r["shuffled_coverage"], 6),
            "diff": round(r["diff"], 6),
            "p_value": f"{r['p_value']:.6f}",
        })

    # Sort by phi then n for readability
    formatted.sort(key=lambda x: (x["phi"], x["n"]))
    return formatted

def write_csv(data: List[Dict[str, Any]], output_path: str):
    """Write aggregated results to a CSV file."""
    if not data:
        logging.warning("No data to write to CSV.")
        return

    fieldnames = ["phi", "n", "ordered_cov", "shuffled_cov", "diff", "p_value"]

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    logging.info(f"CSV written to {output_path}")

def main():
    results_dir = get_results_dir()
    log_path = os.path.join(results_dir, "simulation_logs.json")
    csv_path = os.path.join(results_dir, "coverage_metrics.csv")

    logging.basicConfig(level=logging.INFO)

    try:
        results = load_results_from_log(log_path)
        aggregated = aggregate_results(results)
        write_csv(aggregated, csv_path)
        logging.info("Metrics CSV generation complete.")
    except FileNotFoundError as e:
        logging.error(str(e))
        logging.error("Run 'python code/runner.py --full' first to generate logs.")

if __name__ == "__main__":
    main()
