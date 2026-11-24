"""
src/run_pipeline.py
-------------------

Entry point for the end‑to‑end study pipeline.

This script seeds all randomness sources, reads a simple YAML
configuration file and then runs the individual pipeline stages in
order:

1. Data curation
2. Participant simulation
3. Validation (vector‑match + semantic similarity)
4. Statistical analysis
5. Report generation

The script now also supports a ``--version`` flag that prints a
semantic version string.  The version is defined here as
``0.1.0``; bump it as appropriate for future releases.
"""

import argparse
import sys
import random
import numpy as np
import yaml
from pathlib import Path

# Import the main entry points from the project modules
from src.curators.curate_failed_figures import main as curate_main
from src.simulation.simulate_participants import main as simulate_main
from src.validation.run_validation import main as validate_main
from src.analysis.wilcoxon_analysis import main as analyze_main
from src.report.generate_report import main as report_main

__version__ = "0.1.0"


def seed_all(seed: int = 42) -> None:
    """Seed all common random number generators for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
    except ImportError:
        pass


def run_with_args(func, args):
    """Helper to call a ``main()`` function that uses ``argparse`` by mocking ``sys.argv``."""
    import unittest.mock as mock
    with mock.patch.object(sys, "argv", ["src.run_pipeline"] + args):
        func()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the end‑to‑end study pipeline."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to config file",
    )
    # Version flag – prints the semantic version and exits.
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show program's version number and exit",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Config file {args.config} not found.")
        return 1

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    seed = config.get("seed", 42)
    num_tasks = config.get("num_tasks", 50)
    participants = config.get("participants", 30)

    seed_all(seed)
    print(f"Pipeline started with seed {seed}...")

    try:
        # 1. Data Curation
        print("Running data curation...")
        run_with_args(
            curate_main,
            ["--num-tasks", str(num_tasks), "--output-dir", "data/"],
        )

        # 2. Simulation
        print("Running participant simulation...")
        run_with_args(
            simulate_main,
            [
                "--participants",
                str(participants),
                "--seed",
                str(seed),
                "--log-dir",
                "data/logs/",
            ],
        )

        # 3. Validation
        print("Running combined validation...")
        run_with_args(
            validate_main,
            [
                "--log-dir",
                "data/logs/",
                "--ground-truth-dir",
                "data/ground_truth/",
                "--output-dir",
                "data/validation/",
            ],
        )

        # 4. Analysis
        print("Running statistical analysis...")
        run_with_args(
            analyze_main,
            ["--validation-dir", "data/validation/", "--output-dir", "outputs/"],
        )

        # 5. Report Generation
        print("Generating final report...")
        run_with_args(
            report_main,
            ["--validation-dir", "data/validation/", "--output-dir", "outputs/"],
        )

        print("Pipeline completed")
        return 0
    except Exception as e:
        print(f"Pipeline failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
