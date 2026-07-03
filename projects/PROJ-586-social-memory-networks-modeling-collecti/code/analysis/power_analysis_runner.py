"""Runner script to execute power analysis and generate report.

This script runs the power analysis on existing experiment results
and generates the required report file.
"""
from __future__ import annotations

import sys
from pathlib import Path

from analysis.power import build_parser, main as power_main


def main():
    """Run power analysis with default parameters."""
    # Set up default arguments
    sys.argv = [
        "power_analysis_runner.py",
        "--results", "data/results_full.csv",
        "--output", "results/power_analysis_report.json",
        "--metrics", "specialization_index", "retrieval_efficiency",
        "--target-power", "0.80",
        "--alpha", "0.05"
    ]

    power_main()


if __name__ == "__main__":
    main()
