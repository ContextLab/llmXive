"""
Script to run power analysis.
This script is invoked by the main pipeline to generate power_analysis_report.json.
"""
import argparse
import logging
import sys
from pathlib import Path

from code.src.analysis.power import main as power_main

def setup_logging():
    """Setup basic logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    """Main entry point for power analysis script."""
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Running power analysis via wrapper script...")

    # Simulate command line arguments for the power module
    sys.argv = [
        'run_power_analysis',
        '--config', 'code/config.yaml',
        '--output', 'data'
    ]

    try:
        power_main()
        logger.info("Power analysis completed successfully")
    except Exception as e:
        logger.error(f"Power analysis failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
