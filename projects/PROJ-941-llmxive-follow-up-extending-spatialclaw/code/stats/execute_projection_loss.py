"""
Execution script for T059b: Execute Projection Loss Quantification.
Runs the analysis implemented in T059a (code/stats/analyze_projection_loss.py)
against the final paired dataset generated in T047c.
"""
import os
import sys
import json
import logging
import argparse
from typing import Dict, Any, Optional

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from stats.analyze_projection_loss import run_projection_loss_analysis
from data.loader import load_dataset, DataLoadError
from utils.logging import setup_logging

logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Execute Projection Loss Quantification (T059b)")
    parser.add_argument(
        "--paired-dataset",
        type=str,
        default="results/analysis/final_paired_dataset.csv",
        help="Path to the final paired dataset CSV (from T047c)"
    )
    parser.add_argument(
        "--raw-data",
        type=str,
        default="data/raw/synthetic_spatialclaw_v1.json",
        help="Path to the raw synthetic dataset JSON (for ground truth lookup)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/analysis/projection_loss_breakdown.json",
        help="Path to write the projection loss breakdown JSON"
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default="results/logs/execution.log",
        help="Path to the execution log file"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Setup logging
    setup_logging(log_file=args.log_file, verbose=args.verbose)
    logger.info(f"Starting T059b: Execute Projection Loss Quantification")
    logger.info(f"Input paired dataset: {args.paired_dataset}")
    logger.info(f"Input raw data: {args.raw_data}")
    logger.info(f"Output file: {args.output}")

    # Verify input files exist
    if not os.path.exists(args.paired_dataset):
        logger.error(f"Paired dataset not found: {args.paired_dataset}")
        logger.error("Dependency T047c (Execute Final Paired Dataset Assembly) must be completed first.")
        sys.exit(1)

    if not os.path.exists(args.raw_data):
        logger.error(f"Raw dataset not found: {args.raw_data}")
        logger.error("Dependency T006b (Full Data Generation) must be completed first.")
        sys.exit(1)

    try:
        # Run the projection loss analysis
        # This calls the implementation from T059a
        result = run_projection_loss_analysis(
            paired_dataset_path=args.paired_dataset,
            raw_data_path=args.raw_data
        )

        if result is None:
            logger.error("Projection loss analysis returned None. Check logs for errors.")
            sys.exit(1)

        # Ensure output directory exists
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"Created output directory: {output_dir}")

        # Write the result to the output file
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)

        logger.info(f"Successfully wrote projection loss breakdown to: {args.output}")
        logger.info(f"Results: {json.dumps(result, indent=2)}")
        
        # Verify output contains required fields
        required_fields = ['percentage_projection_loss', 'percentage_action_restriction']
        missing_fields = [field for field in required_fields if field not in result]
        if missing_fields:
            logger.error(f"Output missing required fields: {missing_fields}")
            sys.exit(1)

        logger.info("T059b completed successfully.")
        return 0

    except DataLoadError as e:
        logger.error(f"Data loading error: {e}")
        logger.error("Ensure the raw dataset and paired dataset are valid and accessible.")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during projection loss quantification: {e}")
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())