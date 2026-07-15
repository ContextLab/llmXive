"""
Main entry point for running the full EvoMem experiment.
Executes the runner script with the 'full' configuration.
"""
import sys
import os
import argparse
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.analysis.runner import main as run_experiment_main

def main():
    parser = argparse.ArgumentParser(description="Run the full EvoMem experiment.")
    parser.add_argument(
        "--config",
        type=str,
        default="full",
        choices=["full", "quick"],
        help="Configuration mode: 'full' for complete run, 'quick' for subset."
    )
    args = parser.parse_args()

    # Set environment variable for the runner to pick up the config mode
    os.environ["EXPERIMENT_CONFIG"] = args.config

    print(f"Starting experiment with config: {args.config}")
    try:
        run_experiment_main()
        print("Experiment completed successfully.")
    except Exception as e:
        print(f"Experiment failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
