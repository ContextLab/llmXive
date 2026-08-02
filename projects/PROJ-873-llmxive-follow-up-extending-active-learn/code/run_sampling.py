"""
CLI wrapper for T013b sampling pipeline.
Executes the stratified sampling of flagged comparisons and writes
consensus_sample.json.
"""
import os
import sys
import json
import logging
import argparse

# Add code directory to path
code_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, code_dir)

from sampling import run_sampling_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """CLI entry point for T013b sampling task."""
    parser = argparse.ArgumentParser(
        description="T013b: Filter and stratify sampled flagged comparisons for LLM consensus validation"
    )
    parser.add_argument(
        "--log-path",
        type=str,
        default="data/processed/comparison_log.json",
        help="Path to comparison log file"
    )
    parser.add_argument(
        "--config-path",
        type=str,
        default="data/results/sample_config.json",
        help="Path to sample configuration file"
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="data/results/consensus_sample.json",
        help="Path to write sample indices"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.95,
        help="Similarity threshold for flagging wasted calls"
    )
    parser.add_argument(
        "--bin-width",
        type=float,
        default=0.01,
        help="Width of similarity bins for stratification"
    )

    args = parser.parse_args()

    logger.info(f"Starting T013b sampling pipeline")
    logger.info(f"  Log path: {args.log_path}")
    logger.info(f"  Config path: {args.config_path}")
    logger.info(f"  Output path: {args.output_path}")
    logger.info(f"  Threshold: {args.threshold}")
    logger.info(f"  Bin width: {args.bin_width}")

    try:
        sample_indices = run_sampling_pipeline(
            log_path=args.log_path,
            config_path=args.config_path,
            output_path=args.output_path,
            threshold=args.threshold,
            bin_width=args.bin_width
        )

        logger.info(f"T013b completed successfully. Selected {len(sample_indices)} samples.")
        print(f"T013b: Selected {len(sample_indices)} samples. Output: {args.output_path}")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        print(f"ERROR: Pipeline failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
