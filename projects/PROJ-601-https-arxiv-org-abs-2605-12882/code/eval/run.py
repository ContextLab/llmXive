#!/usr/bin/env python3
"""Entry point for evaluation and report generation.

This script orchestrates the metric calculation and report generation pipeline
as specified in US2. It invokes the scoring module and formats the final output.
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Ensure the code directory is in the path for imports
code_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(code_root))

from eval.saa_scoring import calculate_metrics, generate_report


def main():
    parser = argparse.ArgumentParser(description="Run evaluation and generate report.")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the input results file (e.g., data/results.csv).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/evaluation_report.json",
        help="Path to save the generated evaluation report.",
    )
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found.")
        sys.exit(1)

    metrics = calculate_metrics(args.input)
    report = generate_report(metrics, args.input)
    
    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"Evaluation complete. Report saved to {args.output}")


if __name__ == "__main__":
    main()
