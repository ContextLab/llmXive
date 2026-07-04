"""
Wrapper script to run the scaling plot generation.

This script ensures the scaling data exists and then generates the plot.
It is called by the main pipeline for Task T030.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from analysis.scaling_plot_generator import main as plot_main


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser."""
    parser = argparse.ArgumentParser(
        description='Run scaling plot generation for User Story 3.'
    )
    parser.add_argument(
        '--data',
        type=str,
        default='data/scaling_results.csv',
        help='Path to scaling data CSV'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf',
        help='Path to output PDF'
    )
    return parser


def main():
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()
    
    data_path = Path(args.data)
    output_path = Path(args.output)
    
    # Check if data exists
    if not data_path.exists():
        print(f"Error: Scaling data not found at {data_path}", file=sys.stderr)
        print("Please run the scaling simulation first (T027/T029).", file=sys.stderr)
        return 1
    
    # Run plot generation
    return plot_main()


if __name__ == '__main__':
    sys.exit(main())