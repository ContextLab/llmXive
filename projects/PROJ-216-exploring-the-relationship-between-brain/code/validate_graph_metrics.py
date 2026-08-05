import os
import csv
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Expected valid ranges for graph metrics based on graph theory properties
VALID_RANGES = {
    "global_efficiency": (0.0, 1.0),
    "clustering_coefficient": (0.0, 1.0),
    "modularity": (0.0, 1.0),  # Louvain modularity typically in [0, 1]
    "characteristic_path_length": (0.0, float("inf")),  # Must be positive
    "average_clustering_coefficient": (0.0, 1.0),
    "transitivity": (0.0, 1.0),
}

def load_graph_metrics(csv_path: str) -> List[Dict[str, Any]]:
    """Load graph metrics from CSV file."""
    metrics = []
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Graph metrics file not found: {csv_path}")
    
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            metrics.append(row)
    return metrics

def validate_metric_value(subject_id: str, metric_name: str, value_str: str) -> Tuple[bool, str]:
    """
    Validate a single metric value against expected ranges.
    
    Returns:
        Tuple of (is_valid, reason_string)
        If valid: (True, "")
        If invalid: (False, "REASON: <description>")
    """
    try:
        value = float(value_str)
    except (ValueError, TypeError):
        return False, "REASON: Value is not a valid number"

    if metric_name not in VALID_RANGES:
        # Unknown metric - skip validation but log as info if needed
        return True, ""

    min_val, max_val = VALID_RANGES[metric_name]

    if value < min_val:
        return False, f"REASON: Value {value} is below minimum {min_val}"
    
    if max_val != float("inf") and value > max_val:
        return False, f"REASON: Value {value} exceeds maximum {max_val}"

    return True, ""

def write_anomalies(anomalies: List[Tuple[str, str, str, str]], log_path: str):
    """
    Write anomalies to a log file with format:
    [SUBJECT_ID] [METRIC] [VALUE] [REASON]
    """
    log_file = Path(log_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_file, "w", encoding="utf-8") as f:
        for subject_id, metric, value, reason in anomalies:
            f.write(f"[{subject_id}] [{metric}] [{value}] [{reason}]\n")

def main():
    """Main entry point for graph metrics validation."""
    # Paths relative to project root
    csv_path = "data/processed/graph_metrics.csv"
    log_path = "data/processed/graph_metric_validation.log"

    print(f"Loading graph metrics from {csv_path}...")
    try:
        metrics = load_graph_metrics(csv_path)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    if not metrics:
        print("WARNING: No metrics found in CSV file.", file=sys.stderr)
        # Write empty log file to indicate completion
        write_anomalies([], log_path)
        print(f"Validation log written to {log_path} (empty).")
        return

    anomalies = []
    valid_count = 0

    for row in metrics:
        subject_id = row.get("subject_id", "UNKNOWN")
        metric_name = row.get("metric_name", "UNKNOWN")
        value_str = row.get("value", "")

        is_valid, reason = validate_metric_value(subject_id, metric_name, value_str)
        
        if not is_valid:
            anomalies.append((subject_id, metric_name, value_str, reason))
        else:
            valid_count += 1

    # Write anomalies
    write_anomalies(anomalies, log_path)

    print(f"Validation complete.")
    print(f"  Total entries processed: {len(metrics)}")
    print(f"  Valid entries: {valid_count}")
    print(f"  Anomalies detected: {len(anomalies)}")
    print(f"  Anomaly log written to: {log_path}")

    if anomalies:
        print("WARNING: Anomalies detected. Check validation log for details.")
        # Do not exit with error code to allow pipeline to continue, 
        # but the log file serves as the record of issues.

if __name__ == "__main__":
    main()
