"""Wrapper script to generate scaling plot for T030.

This script ensures the scaling plot is generated after T029 has completed.
It loads the results from scaling_confidence_intervals.json and produces
scaling_plot.pdf with the required limitation note.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from analysis.scaling_plot import main as scaling_plot_main


def main():
    """Run the scaling plot generation."""
    # Default paths
    results_dir = Path("projects/PROJ-586-social-memory-networks-modeling-collecti/results")
    output_path = results_dir / "scaling_plot.pdf"

    # Ensure results directory exists
    results_dir.mkdir(parents=True, exist_ok=True)

    # Check if input data exists
    input_file = results_dir / "scaling_confidence_intervals.json"
    if not input_file.exists():
        print(
            f"ERROR: Input file not found: {input_file}",
            file=sys.stderr
        )
        print(
            "Please run T029 (code/analysis/scaling_ci.py) first to generate the required data.",
            file=sys.stderr
        )
        sys.exit(1)

    # Run the scaling plot generation
    sys.argv = [
        "run_scaling_plot.py",
        "--results-dir", str(results_dir),
        "--output", str(output_path)
    ]
    scaling_plot_main()


if __name__ == "__main__":
    main()