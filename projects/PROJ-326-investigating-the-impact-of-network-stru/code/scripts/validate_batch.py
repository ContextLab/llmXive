"""
Script to validate batch generation and analysis results.
This script is invoked by the main pipeline to generate validation_report.json.
"""
import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

from code.src.validation.validate_batch import main as validate_batch_main

def main():
    """Main entry point for validation script."""
    parser = argparse.ArgumentParser(description="Validate batch generation and analysis")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Config file")
    parser.add_argument("--output", type=str, default="data", help="Output directory")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)
    logger.info("Running batch validation...")

    # Simulate command line arguments for the validation module
    sys.argv = [
        'validate_batch',
        '--config', args.config,
        '--output', args.output
    ]

    try:
        validate_batch_main()
        logger.info("Batch validation completed successfully")
    except Exception as e:
        logger.error(f"Batch validation failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
