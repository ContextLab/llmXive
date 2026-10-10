"""
Script to generate the aggregated metrics CSV required by task T007.

It reads the per‑replicate estimation results produced by the simulation
pipeline (`data/results/estimation_results.csv`) and writes the
aggregated summary (`data/results/aggregated_metrics.csv`) using the
statistical utilities defined in ``analysis.stats``.
"""

import sys
from pathlib import Path

# Ensure the project root is on the Python path so sibling imports work.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analysis.stats import generate_aggregated_metrics

def main() -> int:
    """
    Execute the aggregation.

    Returns:
        Exit code (0 for success, non‑zero for failure).
    """
    input_csv = Path("data/results/estimation_results.csv")
    output_csv = Path("data/results/aggregated_metrics.csv")

    if not input_csv.is_file():
        print(f"ERROR: Expected estimation results at {input_csv}", file=sys.stderr)
        return 1

    try:
        generate_aggregated_metrics(
            input_csv_path=input_csv,
            output_csv_path=output_csv,
            nominal_coverage=0.95,
            bonferroni_alpha=0.01
        )
    except Exception as exc:
        print(f"Aggregation failed: {exc}", file=sys.stderr)
        return 1

    print(f"Aggregated metrics written to {output_csv}")
    return 0

if __name__ == "__main__":
    sys.exit(main())