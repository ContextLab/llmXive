"""
Entry‑point script for T007 – aggregates per‑replicate estimation results
into a summary CSV conforming to the aggregated_metric.schema.yaml contract.

Usage:
    python code/analysis/aggregate_metrics.py
The script reads ``data/results/estimation_results.csv`` and writes
``data/results/aggregated_metrics.csv``.
"""
import sys
from pathlib import Path

# Import the aggregation function from the stats module
from analysis.stats import generate_aggregated_metrics

def main() -> int:
    # Define default input / output locations (as specified in the spec)
    input_path = Path("data") / "results" / "estimation_results.csv"
    output_path = Path("data") / "results" / "aggregated_metrics.csv"

    try:
        generate_aggregated_metrics(input_path, output_path)
    except Exception as e:
        print(f"ERROR while generating aggregated metrics: {e}", file=sys.stderr)
        return 1

    print(f"Aggregated metrics successfully written to {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
