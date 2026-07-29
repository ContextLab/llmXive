"""
Wrapper script to execute T030: Generate scaling plot.

This script orchestrates the generation of the scaling plot as required by T030.
It assumes that the scaling data (results from T027/T028) has been generated
and is available at the default input path.

Usage:
    python code/run_scaling_plot.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add code directory to path if running as script
sys.path.insert(0, str(Path(__file__).parent))

from analysis.scaling_plot_generator import build_parser, main as plot_main


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the T030 scaling plot generation task."
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/scaling_results.json",
        help="Path to the input JSON file with scaling analysis results."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/scaling_plot.pdf",
        help="Path to save the output PDF plot."
    )
    parser.add_argument(
        "--agents",
        type=str,
        default=None,
        help="Comma-separated list of agent counts to include."
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # Override the default arguments of the underlying plot generator
    sys.argv = [
        "run_scaling_plot.py",
        "--input", args.input,
        "--output", args.output,
        "--agents", args.agents if args.agents else ""
    ]
    # Filter out empty strings if --agents was not provided
    sys.argv = [arg for arg in sys.argv if arg]

    plot_main()


if __name__ == "__main__":
    main()
