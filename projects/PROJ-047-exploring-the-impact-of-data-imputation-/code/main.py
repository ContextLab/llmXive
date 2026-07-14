"""
Main entry point for the data imputation impact simulation.

This script provides a CLI skeleton to accept configuration and output paths.
It does not yet contain the simulation loop logic (reserved for T029a).
"""

import argparse
import sys
from typing import Optional


def parse_args(args: Optional[list] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run the data imputation impact simulation."
    )
    parser.add_argument(
        "--config",
        type=str,
        required=False,
        help="Path to the configuration file (e.g., JSON or YAML).",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=False,
        default="data/results/simulation_summary.csv",
        help="Path to the output file for results.",
    )
    return parser.parse_args(args)


def main(args: Optional[list] = None) -> int:
    """
    Entry point for the simulation.

    Currently a skeleton that parses arguments and prints status.
    The full simulation loop will be implemented in T029a.
    """
    parsed_args = parse_args(args)

    print(f"Simulation started.")
    print(f"Config path: {parsed_args.config}")
    print(f"Output path: {parsed_args.output}")

    # TODO: Implement simulation loop (T029a)
    # TODO: Load config, iterate beta, generate data, run imputation, aggregate results

    print("Simulation skeleton complete. No loop logic executed yet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
