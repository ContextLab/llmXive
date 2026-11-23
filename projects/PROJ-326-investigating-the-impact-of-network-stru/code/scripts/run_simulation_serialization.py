"""
Script to run the simulation result serialization process.
This script is invoked by the run-book to produce data/analysis/simulation_results.json.
"""
import argparse
import logging
import sys
from pathlib import Path

from code.src.analysis.serialize_simulation import setup_logging, main as serialization_main

def main() -> None:
    """Main entry point for the simulation serialization script."""
    parser = argparse.ArgumentParser(description="Run simulation result serialization.")
    parser.add_argument(
        "--config",
        type=str,
        default="code/config.yaml",
        help="Path to the configuration file."
    )
    args = parser.parse_args()
    
    setup_logging()
    serialization_main()

if __name__ == "__main__":
    main()