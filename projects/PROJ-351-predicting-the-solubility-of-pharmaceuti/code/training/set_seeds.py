"""
Script to set random seeds for training reproducibility.

This script demonstrates the usage of the seed configuration utilities
and can be imported into training pipelines to ensure reproducibility.
"""
import os
import sys
import logging
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.seeds import ensure_seeded, get_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Set random seeds for reproducible training'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=None,
        help='Random seed value (default: from environment or 42)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    return parser.parse_args()


def main():
    """Main entry point for setting seeds."""
    args = parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Initializing random seed configuration...")
    
    # Set seeds and get the actual value used
    seed_used = ensure_seeded(args.seed)
    
    logger.info(f"Successfully configured random seeds with value: {seed_used}")
    logger.info("Environment is now seeded for reproducibility.")
    
    # Print environment variable for verification
    logger.info(f"PYTHONHASHSEED environment variable set to: {os.environ.get('PYTHONHASHSEED')}")
    
    return seed_used


if __name__ == "__main__":
    main()
