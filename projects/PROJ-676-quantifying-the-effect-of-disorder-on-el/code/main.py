"""
Main orchestration script for the project.
"""
import argparse
import logging
import sys
from pathlib import Path

from code.config import get_config
from code.analyze_pr import run_scaling_analysis
from code.visualize import main as viz_main
from code.apply_bonferroni import main as bonferroni_main
from code.aggregate_and_correct_stats import main as aggregate_main
from code.generate_multiL_pr_dataset import main as generate_dataset_main

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_orchestration(args):
    """Run the full orchestration based on arguments."""
    config = get_config()

    # Override config with CLI arguments if provided
    if args.Llist:
        config["L_LIST"] = [int(x) for x in args.Llist]
    if args.Wlist:
        config["W_LIST"] = [float(x) for x in args.Wlist]
    if args.realizations:
        config["NUM_REALIZATIONS"] = int(args.realizations)
    if args.seed:
        config["SEED"] = int(args.seed)

    if args.mode == "generate_and_analyze":
        logger.info("Generating raw PR dataset...")
        # This creates data/processed/pr_raw_multiL.json
        generate_dataset_main()

        logger.info("Running scaling analysis...")
        run_scaling_analysis(config)
        logger.info("Scaling analysis complete.")

        # Run aggregation and Bonferroni correction
        logger.info("Running aggregation and Bonferroni correction...")
        aggregate_main()
        bonferroni_main()
        logger.info("Aggregation and correction complete.")

    elif args.mode == "scaling_analysis":
        if args.output:
            config["OUTPUT_PATH"] = args.output
        run_scaling_analysis(config)

    elif args.mode == "visualize":
        viz_main()

    else:
        logger.error(f"Unknown mode: {args.mode}")
        sys.exit(1)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Main orchestration script")
    parser.add_argument(
        "--mode",
        type=str,
        required=True,
        choices=["generate_and_analyze", "scaling_analysis", "visualize"],
        help="Mode to run"
    )
    parser.add_argument("--Llist", nargs='+', type=int, help="List of system sizes")
    parser.add_argument("--Wlist", nargs='+', type=float, help="List of disorder widths")
    parser.add_argument("--realizations", type=int, help="Number of realizations")
    parser.add_argument("--seed", type=int, help="Random seed")
    parser.add_argument("--output", type=str, help="Output file path")

    args = parser.parse_args()
    run_orchestration(args)


if __name__ == "__main__":
    main()
