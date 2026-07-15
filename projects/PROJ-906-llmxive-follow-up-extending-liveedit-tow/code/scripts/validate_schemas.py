"""
Script to validate existing data artifacts against schema validators.
"""
import os
import sys
import json
import argparse
from pathlib import Path
from contracts.dataset_validator import DatasetValidator
from contracts.metrics_validator import MetricsValidator
from contracts.analysis_validator import AnalysisValidator
from utils.logger import get_logger

logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Validate data artifacts against schema.")
    parser.add_argument(
        "--type",
        choices=["dataset", "metrics", "analysis"],
        required=True,
        help="Type of artifact to validate.",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the JSON file to validate.",
    )
    args = parser.parse_args()

    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    logger.info(f"Validating {args.type} artifact: {args.input}")

    if args.type == "dataset":
        result = DatasetValidator.validate_json_file(args.input)
    elif args.type == "metrics":
        result = MetricsValidator.validate_json_file(args.input)
    elif args.type == "analysis":
        result = AnalysisValidator.validate_analysis_file(args.input)
    else:
        logger.error("Unknown type")
        sys.exit(1)

    if result["valid"]:
        logger.info("Validation PASSED.")
        if "stats" in result:
            logger.info(f"Stats: {json.dumps(result['stats'], indent=2)}")
        sys.exit(0)
    else:
        logger.error("Validation FAILED.")
        logger.error(f"Errors: {json.dumps(result['errors'], indent=2)}")
        sys.exit(1)


if __name__ == "__main__":
    main()