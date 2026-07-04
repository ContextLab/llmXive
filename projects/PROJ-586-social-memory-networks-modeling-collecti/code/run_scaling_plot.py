"""Script to generate the scaling plot for User Story 3.

This script runs the scaling plot generation using real data from
the scaling simulation results and produces scaling_plot.pdf with
power-law fits and reliability notes.
"""
from __future__ import annotations

import sys
from pathlib import Path

from analysis.scaling_plot_generator import main as plot_main


def main() -> int:
    """Run scaling plot generation."""
    # Determine paths relative to project root
    project_root = Path(__file__).parent.parent
    data_file = project_root / "data" / "scaling_results.csv"
    output_file = project_root / "results" / "scaling_plot.pdf"

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Check if data exists
    if not data_file.exists():
        print(f"Error: Scaling data not found at {data_file}", file=sys.stderr)
        print("Please run the scaling simulation first to generate scaling_results.csv", file=sys.stderr)
        return 1

    # Prepare arguments
    sys.argv = [
        'run_scaling_plot.py',
        '--data', str(data_file),
        '--output', str(output_file),
        '--note', 'Note: 3 data points limit power-law reliability.'
    ]

    return plot_main()


if __name__ == '__main__':
    sys.exit(main())