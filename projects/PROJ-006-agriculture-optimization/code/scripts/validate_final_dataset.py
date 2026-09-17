"""
Script to validate the final analysis dataset (T022).
Runs src/cli/validate.py against data/processed/analysis_dataset.csv
to ensure it meets all schema requirements.
"""
import argparse
import logging
import sys
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.cli.validate import main as validate_main
from src.utils.io_helpers import setup_logging

def main() -> int:
    """
    Main entry point for the final dataset validation script.
    Returns exit code 0 if validation passes, 1 otherwise.
    """
    parser = argparse.ArgumentParser(
        description="Validate the final analysis dataset against schema contracts."
    )
    parser.add_argument(
        "--dataset-path",
        type=Path,
        default=project_root / "data" / "processed" / "analysis_dataset.csv",
        help="Path to the final analysis dataset CSV file."
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO)."
    )

    args = parser.parse_args()

    logger = setup_logging("validate_final_dataset", args.log_level)

    if not args.dataset_path.exists():
        logger.error(f"Final dataset not found at: {args.dataset_path}")
        logger.error("Run the pipeline first to generate the dataset.")
        return 1

    logger.info(f"Validating final dataset: {args.dataset_path}")

    # Construct arguments for validate_main
    original_argv = sys.argv
    try:
        sys.argv = [
            "validate_final_dataset.py",
            str(args.dataset_path),
            "--schema-type", "dataset",
            "--log-level", args.log_level
        ]
        exit_code = validate_main()

        if exit_code == 0:
            logger.info("Final dataset validation PASSED.")
        else:
            logger.error("Final dataset validation FAILED.")

        return exit_code

    finally:
        sys.argv = original_argv

if __name__ == "__main__":
    sys.exit(main())