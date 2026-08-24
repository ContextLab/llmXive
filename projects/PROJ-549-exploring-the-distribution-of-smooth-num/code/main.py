"""
Main entry point for the Smooth Numbers Distribution Project.

This module provides a CLI interface to trigger:
1. Segmented sieve generation (US1)
2. Smoothness density analysis across parameter grids (US2)
3. Statistical analysis and visualization orchestration (US3)
"""

import argparse
import json
import logging
import sys
from typing import Optional

from config import load_config
from sieve import run_sieve
from smoothness import run_smoothness_analysis, parse_args as smoothness_parse_args
from analysis import run_plan_primary_analysis, run_spec_mandatory_analysis, run_chi_square_goodness_of_fit
from utils import setup_logging


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="CLI entry point for Smooth Numbers Distribution analysis."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Sieve command
    sieve_parser = subparsers.add_parser(
        "sieve", help="Generate primes using the segmented sieve."
    )
    sieve_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Upper bound for prime generation (default: from config).",
    )
    sieve_parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output CSV path (default: from config).",
    )
    sieve_parser.add_argument(
        "--validate",
        action="store_true",
        default=True,
        help="Run deterministic validation after generation (default: True).",
    )
    sieve_parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set logging level.",
    )

    # Analyze command (US2)
    analyze_parser = subparsers.add_parser(
        "analyze", help="Run smoothness density analysis (US2)."
    )
    analyze_parser.add_argument(
        "--primes-path",
        type=str,
        default=None,
        help="Path to the validated primes CSV (default: from config).",
    )
    analyze_parser.add_argument(
        "--output-spec",
        type=str,
        default=None,
        help="Output CSV path for Spec grid density measurements (default: from config).",
    )
    analyze_parser.add_argument(
        "--output-plan",
        type=str,
        default=None,
        help="Output CSV path for Plan grid density measurements (default: from config).",
    )

    analyze_parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set logging level.",
    )

    # Run Analysis command (US3)
    run_analysis_parser = subparsers.add_parser(
        "run-analysis", help="Run full statistical analysis (US3)."
    )
    run_analysis_parser.add_argument(
        "--input-spec",
        type=str,
        default=None,
        help="Input CSV path for Spec grid (default: from config).",
    )
    run_analysis_parser.add_argument(
        "--input-plan",
        type=str,
        default=None,
        help="Input CSV path for Plan grid (default: from config).",
    )
    run_analysis_parser.add_argument(
        "--output-fits",
        type=str,
        default=None,
        help="Output JSON path for model fits (default: from config).",
    )
    run_analysis_parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set logging level.",
    )

    return parser.parse_args()


def main() -> int:
    """
    Main entry point.

    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    args = parse_args()

    if not args.command:
        print("Error: No command specified. Use 'python code/main.py --help' for usage.")
        return 1

    # Setup logging
    logger = setup_logging(level=getattr(args, 'log_level', 'INFO'))
    logger.info("Starting Smooth Numbers Distribution Project CLI.")

    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return 1

    if args.command == "sieve":
        logger.info("Triggering segmented sieve generation (US1).")

        # Override config with CLI args if provided
        limit = args.limit if args.limit is not None else config.grid.get("sieve_limit", 10**9)
        output_path = args.output if args.output is not None else config.paths.get("primes_output", "data/primes_1e9.csv")

        logger.info(f"Running segmented sieve up to {limit:,}")
        logger.info(f"Output path: {output_path}")

        try:
            success, checksum, count = run_sieve(
                limit=limit,
                output_path=output_path,
                validate=args.validate,
                logger=logger
            )

            if success:
                logger.info(f"Sieve completed successfully. Count: {count:,}, Checksum: {checksum}")
                return 0
            else:
                logger.error("Sieve validation failed or runtime limit exceeded.")
                return 1

        except Exception as e:
            logger.exception(f"Error during sieve execution: {e}")
            return 1

    elif args.command == "analyze":
        logger.info("Triggering smoothness density analysis (US2).")

        # Override config with CLI args if provided
        primes_path = args.primes_path if args.primes_path is not None else config.paths.get("primes_input", "data/primes_1e9.csv")
        output_spec_path = args.output_spec if args.output_spec is not None else config.paths.get("density_output_spec", "data/density_measurements_spec.csv")
        output_plan_path = args.output_plan if args.output_plan is not None else config.paths.get("density_output_plan", "data/density_measurements_plan.csv")

        logger.info(f"Using primes from: {primes_path}")
        logger.info(f"Output path (Spec): {output_spec_path}")
        logger.info(f"Output path (Plan): {output_plan_path}")

        try:
            success = run_smoothness_analysis(
                primes_path=primes_path,
                output_spec_path=output_spec_path,
                output_plan_path=output_plan_path,
                logger=logger
            )

            if success:
                logger.info("Analysis completed successfully.")
                return 0
            else:
                logger.error("Analysis failed.")
                return 1

        except Exception as e:
            logger.exception(f"Error during analysis execution: {e}")
            return 1

    elif args.command == "run-analysis":
        logger.info("Triggering full statistical analysis (US3).")

        # Override config with CLI args if provided
        input_spec_path = args.input_spec if args.input_spec is not None else config.paths.get("density_input_spec", "data/density_measurements_spec.csv")
        input_plan_path = args.input_plan if args.input_plan is not None else config.paths.get("density_input_plan", "data/density_measurements_plan.csv")
        output_fits_path = args.output_fits if args.output_fits is not None else config.paths.get("model_fits_output", "data/model_fits.json")

        logger.info(f"Input path (Spec): {input_spec_path}")
        logger.info(f"Input path (Plan): {input_plan_path}")
        logger.info(f"Output path (Fits): {output_fits_path}")

        try:
            # Run Plan-Primary Analysis (Power-law regression on deviation ratio)
            logger.info("Running Plan-Primary Analysis (Deviation Ratio Regression)...")
            plan_results = run_plan_primary_analysis(input_plan_path, logger)

            # Run Spec-Mandatory Analysis (Power-law regression on raw density)
            logger.info("Running Spec-Mandatory Analysis (Raw Density Regression)...")
            spec_results = run_spec_mandatory_analysis(input_spec_path, logger)

            # Run Chi-Square Goodness-of-Fit Test (Spec-Mandatory)
            logger.info("Running Chi-Square Goodness-of-Fit Test...")
            chi_square_results = run_chi_square_goodness_of_fit(input_spec_path, logger)

            # Aggregate results
            fits_data = {
                "plan_primary": plan_results,
                "spec_mandatory": spec_results,
                "chi_square_test": chi_square_results
            }

            # Write to JSON
            with open(output_fits_path, 'w', encoding='utf-8') as f:
                json.dump(fits_data, f, indent=2, default=str)

            logger.info(f"Model fits saved to {output_fits_path}")
            logger.info("Full statistical analysis completed successfully.")
            return 0

        except Exception as e:
            logger.exception(f"Error during statistical analysis execution: {e}")
            return 1

    else:
        logger.error(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())