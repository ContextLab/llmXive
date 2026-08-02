"""
Validation script for graph metrics computed in User Story 2.

This script reads the aggregated graph metrics from `data/processed/graph_metrics.csv`,
validates numerical ranges for each metric type, and writes any anomalies to
`data/processed/graph_metric_validation.log`.

Valid ranges (approximate based on graph theory):
- Global Efficiency: [0.0, 1.0]
- Clustering Coefficient: [0.0, 1.0]
- Modularity: [0.0, 1.0] (typically, though can theoretically be slightly higher in specific definitions, we cap at 1.0 for standard Louvain)
- Other metrics (if any): TBD based on CSV content, but currently we focus on the three above.

Anomaly format: [SUBJECT_ID] [METRIC] [VALUE] [REASON]
"""

import os
import csv
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Define expected valid ranges for each metric
METRIC_RANGES = {
    "global_efficiency": (0.0, 1.0),
    "clustering_coefficient": (0.0, 1.0),
    "modularity": (0.0, 1.0),
    # Add more if other metrics are added to the pipeline later
}

def load_graph_metrics(csv_path: Path) -> List[Dict[str, Any]]:
    """Load graph metrics from CSV file."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Graph metrics file not found: {csv_path}")
    
    metrics = []
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            metrics.append(row)
    return metrics

def validate_metric_value(metric_name: str, value_str: str) -> Tuple[bool, str]:
    """
    Validate a single metric value against expected ranges.
    
    Returns:
        Tuple of (is_valid, reason_string)
    """
    if metric_name not in METRIC_RANGES:
        return True, f"Metric '{metric_name}' has no defined range; skipping validation"
    
    try:
        value = float(value_str)
    except (ValueError, TypeError):
        return False, f"Non-numeric value: '{value_str}'"
    
    min_val, max_val = METRIC_RANGES[metric_name]
    
    if value < min_val or value > max_val:
        return False, f"Value {value} outside expected range [{min_val}, {max_val}]"
    
    return True, "OK"

def write_anomalies(anomalies: List[str], log_path: Path):
    """Write anomalies to the validation log file."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        for anomaly in anomalies:
            f.write(anomaly + "\n")
    print(f"Validation complete. Found {len(anomalies)} anomalies.")
    if anomalies:
        print(f"Anomalies written to: {log_path}")
    else:
        print("No anomalies found. All metrics within expected ranges.")

def main():
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    csv_path = project_root / "data" / "processed" / "graph_metrics.csv"
    log_path = project_root / "data" / "processed" / "graph_metric_validation.log"

    print(f"Loading graph metrics from: {csv_path}")
    try:
        metrics = load_graph_metrics(csv_path)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if not metrics:
        print("No metrics found in CSV. Validation skipped.")
        # Write empty log to indicate completion
        write_anomalies([], log_path)
        return

    anomalies = []
    print(f"Validating {len(metrics)} metric entries...")

    for entry in metrics:
        subject_id = entry.get("subject_id", "UNKNOWN")
        metric_name = entry.get("metric_name", "UNKNOWN").lower()
        value_str = entry.get("value", "")

        is_valid, reason = validate_metric_value(metric_name, value_str)

        if not is_valid:
            anomaly_line = f"[{subject_id}] [{metric_name}] [{value_str}] [{reason}]"
            anomalies.append(anomaly_line)
            print(f"ANOMALY: {anomaly_line}")

    write_anomalies(anomalies, log_path)

if __name__ == "__main__":
    main()
