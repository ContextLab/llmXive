"""
Runner script for T013b: Stratified sampling for consensus validation.

This script executes the sampling pipeline to select a stratified random
sample of flagged pairs for LLM consensus validation, as required by FR-003.

Output: data/results/consensus_sample.json
"""

import os
import sys
import json
import logging
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sampling import run_sampling_pipeline
from config import get_config

def main():
    """Execute the T013b sampling task."""
    parser = argparse.ArgumentParser(
        description="T013b: Select stratified random sample for consensus validation"
    )
    parser.add_argument(
        '--comparison-log',
        type=str,
        default=None,
        help="Path to flagged pairs count JSON (T013a output)"
    )
    parser.add_argument(
        '--sample-config',
        type=str,
        default=None,
        help="Path to sample config JSON (T013c output)"
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help="Path to write consensus sample JSON (T013b output)"
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.95,
        help="Similarity threshold for wasted call detection"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Resolve paths
    config = get_config()
    
    if args.comparison_log is None:
        args.comparison_log = os.path.join(
            config.data_dir, 'results', 'flagged_pairs_count.json'
        )
    
    if args.sample_config is None:
        args.sample_config = os.path.join(
            config.data_dir, 'results', 'sample_config.json'
        )
    
    if args.output is None:
        args.output = os.path.join(
            config.data_dir, 'results', 'consensus_sample.json'
        )
    
    logger.info(f"Running T013b sampling pipeline")
    logger.info(f"  Comparison log: {args.comparison_log}")
    logger.info(f"  Sample config: {args.sample_config}")
    logger.info(f"  Output: {args.output}")
    logger.info(f"  Threshold: {args.threshold}")
    
    # Check input files exist
    if not os.path.exists(args.comparison_log):
        logger.error(f"Comparison log not found: {args.comparison_log}")
        logger.error("Please run T013a first to generate flagged_pairs_count.json")
        return 1
    
    if not os.path.exists(args.sample_config):
        logger.error(f"Sample config not found: {args.sample_config}")
        logger.error("Please run T013c first to generate sample_config.json")
        return 1
    
    # Run the sampling pipeline
    result = run_sampling_pipeline(
        comparison_log_path=args.comparison_log,
        sample_config_path=args.sample_config,
        output_path=args.output,
        similarity_threshold=args.threshold
    )
    
    logger.info(f"Task T013b complete")
    logger.info(f"  Total flagged pairs: {result['total_flagged']}")
    logger.info(f"  Sample size: {result['sample_size']}")
    logger.info(f"  Strata count: {result['strata_count']}")
    logger.info(f"  Output written to: {args.output}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())