"""
Script to execute T014: Baseline Active Ranker.

This script provides a CLI entry point for running the T014 task
as part of the quickstart pipeline.
"""
import os
import sys
import argparse
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ranker import main as run_baseline_main

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """CLI entry point for T014."""
    parser = argparse.ArgumentParser(
        description='Execute T014: Baseline Active Ranker'
    )
    parser.add_argument(
        '--dataset',
        type=str,
        default=None,
        help='Specific dataset to process (optional, processes all by default)'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='bert-base-uncased',
        help='Embedding model to use (default: bert-base-uncased)'
    )
    
    args = parser.parse_args()
    
    logger.info("Starting T014: Baseline Active Ranker")
    logger.info(f"Dataset filter: {args.dataset or 'all'}")
    logger.info(f"Embedding model: {args.model}")
    
    # Run the main T014 logic
    exit_code = run_baseline_main()
    
    if exit_code == 0:
        logger.info("T014 completed successfully")
    else:
        logger.error(f"T014 failed with exit code {exit_code}")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())