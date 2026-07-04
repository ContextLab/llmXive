"""
CLI argument parser and entry point for the Embodied Curriculum Learning pipeline.

Supports modes for secondary analysis and synthetic data generation,
along with configuration for input paths, sensitivity sweep thresholds,
and random seeds.
"""
import argparse
import sys
from typing import List, Optional

from .logging_config import setup_logging
from .utils import set_seed
from .data_loader import load_public_dataset, calculate_gain_scores
from .synthetic_gen import SyntheticDataGenerator

logger = setup_logging(__name__)


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Parse command-line arguments.

    Args:
        args: Optional list of arguments. If None, uses sys.argv[1:].

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        prog="embodied_curriculum",
        description="Pipeline for Embodied Curriculum Learning: Physical Simulation for Abstract Concept Teaching",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--mode",
        type=str,
        required=True,
        choices=["secondary_analysis", "synthetic"],
        help="Operation mode: 'secondary_analysis' to process existing data, "
             "'synthetic' to generate synthetic datasets.",
    )

    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to input data file (CSV or JSON). Required for 'secondary_analysis' mode. "
             "Optional for 'synthetic' mode (overrides default generation path).",
    )

    parser.add_argument(
        "--sweep_thresholds",
        type=str,
        default=None,
        help="Comma-separated list of thresholds for sensitivity analysis (e.g., '0.01,0.05,0.1'). "
             "Only used when applicable.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42).",
    )

    parsed_args = parser.parse_args(args)

    # Validation logic
    if parsed_args.mode == "secondary_analysis" and not parsed_args.input:
        parser.error("--input is required for 'secondary_analysis' mode.")

    # Parse sweep thresholds if provided
    if parsed_args.sweep_thresholds:
        try:
            parsed_args.sweep_thresholds = [float(t.strip()) for t in parsed_args.sweep_thresholds.split(",")]
        except ValueError:
            parser.error("--sweep_thresholds must be a comma-separated list of numbers.")

    return parsed_args


def run_secondary_analysis(args: argparse.Namespace) -> int:
    """
    Execute the secondary analysis mode.
    Loads public data, validates, calculates gain scores, and writes to data/processed/.
    """
    logger.info(f"Running secondary analysis on: {args.input}")
    set_seed(args.seed)

    try:
        # Load and validate dataset (includes automatic synthetic fallback if needed per T012/T016)
        records = load_public_dataset(args.input)
        if not records:
            logger.error("No valid records loaded from input.")
            return 1

        # Calculate gain scores
        processed_records = calculate_gain_scores(records)
        if not processed_records:
            logger.warning("No records passed gain score calculation (all skipped).")
            return 1

        # Write output to data/processed/
        output_path = "data/processed/secondary_analysis_results.csv"
        logger.info(f"Writing processed results to: {output_path}")

        # Ensure directory exists
        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', newline='') as f:
            if processed_records:
                # Write header
                first_record = processed_records[0]
                writer = None
                for record in processed_records:
                    if writer is None:
                        writer = csv.DictWriter(f, fieldnames=record.keys())
                        writer.writeheader()
                    writer.writerow(record)
            else:
                logger.warning("No data to write.")

        logger.info("Secondary analysis completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Error during secondary analysis: {e}", exc_info=True)
        return 1


def run_synthetic_generation(args: argparse.Namespace) -> int:
    """
    Execute the synthetic data generation mode.
    Generates datasets and writes to data/synthetic/.
    """
    logger.info("Running synthetic data generation.")
    set_seed(args.seed)

    try:
        generator = SyntheticDataGenerator()
        
        # Determine output path
        output_path = "data/synthetic/generated_dataset.csv"
        mapping_log_path = "data/synthetic/mapping_log.json"
        
        if args.input:
            # If input provided in synthetic mode, it might be a config override
            # For now, we generate to default paths but could extend to use input as config
            logger.info(f"Ignoring --input for synthetic generation (using defaults). "
                        f"Use config files for parameter overrides.")

        # Generate data
        logger.info("Generating synthetic dataset...")
        records = generator.generate()
        
        if not records:
            logger.error("Synthetic generation returned no records.")
            return 1

        # Ensure directories exist
        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        os.makedirs(os.path.dirname(mapping_log_path), exist_ok=True)

        # Write dataset
        logger.info(f"Writing synthetic dataset to: {output_path}")
        with open(output_path, 'w', newline='') as f:
            if records:
                writer = None
                for record in records:
                    if writer is None:
                        writer = csv.DictWriter(f, fieldnames=record.keys())
                        writer.writeheader()
                    writer.writerow(record)

        # Write mapping log (Constitution Principle VI)
        logger.info(f"Writing mapping log to: {mapping_log_path}")
        mapping_log = generator.generate_mapping_log()
        with open(mapping_log_path, 'w') as f:
            json.dump(mapping_log, f, indent=2)

        logger.info("Synthetic generation completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Error during synthetic generation: {e}", exc_info=True)
        return 1


def main() -> int:
    """
    CLI entry point. Delegates to mode-specific handlers.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    try:
        args = parse_args()
        logger.info(f"Starting pipeline in mode: {args.mode}")
        logger.info(f"Input: {args.input}")
        logger.info(f"Seed: {args.seed}")
        if args.sweep_thresholds:
            logger.info(f"Sweep thresholds: {args.sweep_thresholds}")

        if args.mode == "secondary_analysis":
            return run_secondary_analysis(args)
        elif args.mode == "synthetic":
            return run_synthetic_generation(args)
        else:
            logger.error(f"Unknown mode: {args.mode}")
            return 1

    except SystemExit as e:
        # argparse calls sys.exit on error; we catch it to return the code cleanly
        return e.code if isinstance(e.code, int) else 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())