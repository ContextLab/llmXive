import os
import csv
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Constants for validation thresholds based on graph theory constraints
# Global Efficiency: Theoretically (0, 1] for connected graphs, but can be 0 if disconnected.
# In practice, we expect > 0.
EFFICIENCY_MIN = 0.0
EFFICIENCY_MAX = 1.0

# Clustering Coefficient: [0, 1]
CLUSTERING_MIN = 0.0
CLUSTERING_MAX = 1.0

# Modularity: Typically [-0.5, 1.0], often positive. We set a safe lower bound.
MODULARITY_MIN = -1.0
MODULARITY_MAX = 1.0

# Input/Output paths
INPUT_CSV_PATH = Path("data/processed/graph_metrics.csv")
OUTPUT_LOG_PATH = Path("data/processed/graph_metric_validation.log")

def load_graph_metrics(csv_path: Path) -> List[Dict[str, Any]]:
    """Load graph metrics from the aggregated CSV file."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Input file not found: {csv_path}")
    
    metrics = []
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                metrics.append({
                    'subject_id': row['subject_id'],
                    'metric_name': row['metric_name'],
                    'value': float(row['value'])
                })
            except (ValueError, KeyError) as e:
                # Log parsing errors but continue or fail loudly depending on strictness
                # For this task, we treat parsing errors as anomalies
                raise ValueError(f"Error parsing row in {csv_path}: {e}")
    return metrics

def validate_metric_value(metric_name: str, value: float) -> Tuple[bool, str]:
    """
    Validate a metric value against expected numerical ranges.
    Returns (is_valid, reason_string).
    """
    if metric_name == 'global_efficiency':
        if not (EFFICIENCY_MIN <= value <= EFFICIENCY_MAX):
            return False, f"Value {value} out of range [{EFFICIENCY_MIN}, {EFFICIENCY_MAX}]"
    elif metric_name == 'clustering_coefficient':
        if not (CLUSTERING_MIN <= value <= CLUSTERING_MAX):
            return False, f"Value {value} out of range [{CLUSTERING_MIN}, {CLUSTERING_MAX}]"
    elif metric_name == 'modularity':
        if not (MODULARITY_MIN <= value <= MODULARITY_MAX):
            return False, f"Value {value} out of range [{MODULARITY_MIN}, {MODULARITY_MAX}]"
    elif metric_name == 'average_path_length':
        # Path length is non-negative. Upper bound is hard to define but usually < N.
        if value < 0:
            return False, f"Value {value} is negative"
    else:
        # Generic check for NaN or Inf
        import math
        if math.isnan(value) or math.isinf(value):
            return False, f"Value is NaN or Inf"
    
    return True, "OK"

def write_anomalies(anomalies: List[Tuple[str, str, float, str]], log_path: Path):
    """Write anomalies to the log file in the specified format."""
    # Ensure directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'w', encoding='utf-8') as f:
        for subject_id, metric, value, reason in anomalies:
            # Format: [SUBJECT_ID] [METRIC] [VALUE] [REASON]
            line = f"[{subject_id}] [{metric}] [{value}] [{reason}]\n"
            f.write(line)

def main():
    """Main entry point for validation."""
    print(f"Validating graph metrics from {INPUT_CSV_PATH}...")
    
    if not INPUT_CSV_PATH.exists():
        print(f"Error: Input file {INPUT_CSV_PATH} does not exist. "
              f"Please ensure T026 (Aggregate Graph Metrics) has been run successfully.")
        sys.exit(1)

    try:
        data = load_graph_metrics(INPUT_CSV_PATH)
    except Exception as e:
        print(f"Error loading metrics: {e}")
        sys.exit(1)

    anomalies = []
    for row in data:
        is_valid, reason = validate_metric_value(row['metric_name'], row['value'])
        if not is_valid:
            anomalies.append((row['subject_id'], row['metric_name'], row['value'], reason))

    # Write anomalies (even if empty, the file should be created to show completion)
    write_anomalies(anomalies, OUTPUT_LOG_PATH)
    
    print(f"Validation complete. Found {len(anomalies)} anomalies.")
    print(f"Anomalies written to {OUTPUT_LOG_PATH}")

    if len(anomalies) > 0:
        # Optional: Print first few anomalies for quick inspection
        print("Sample anomalies:")
        for a in anomalies[:5]:
            print(f"  {a}")

if __name__ == "__main__":
    main()
