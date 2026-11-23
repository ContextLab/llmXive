"""
Script wrapper for running the provenance aggregation.

This script provides a CLI entry point for the provenance aggregation
module, allowing it to be invoked from the command line.
"""
import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.src.analysis.provenance import main as provenance_main

def setup_logging():
    """Configure logging for the script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    """Main entry point for the provenance script."""
    parser = argparse.ArgumentParser(
        description='Aggregate seed and parameter provenance for the batch'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='code/config.yaml',
        help='Path to configuration file (not used directly but kept for consistency)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Custom output path for provenance file'
    )

    args = parser.parse_args()
    setup_logging()

    # Note: The provenance module uses fixed paths based on project structure
    # The --output argument is accepted for CLI consistency but not used
    # as the output path is determined by the aggregation logic

    return provenance_main()

if __name__ == '__main__':
    sys.exit(main())
