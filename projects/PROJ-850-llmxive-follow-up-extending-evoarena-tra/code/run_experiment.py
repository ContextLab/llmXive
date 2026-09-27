import sys
import os
import argparse
from pathlib import Path

# Ensure the project root is in the path
sys.path.insert(0, str(Path(__file__).parent))

from src.analysis.runner import main as run_experiment_main
from src.utils.seeding import set_deterministic_seed

def main():
    """
    Entry point for running the full experiment.
    Sets deterministic seeds before executing the experiment.
    """
    # Set deterministic seed for reproducible results
    set_deterministic_seed()

    # Parse arguments
    parser = argparse.ArgumentParser(description="Run EvoMem experiment")
    parser.add_argument(
        "--config",
        type=str,
        default="full",
        help="Configuration name (e.,g., 'full', 'minimal')"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Override the default random seed"
    )
    args = parser.parse_args()

    # If a specific seed is provided, use it
    if args.seed is not None:
        set_deterministic_seed(args.seed)

    # Run the experiment
    run_experiment_main(config_name=args.config)

if __name__ == "__main__":
    main()
