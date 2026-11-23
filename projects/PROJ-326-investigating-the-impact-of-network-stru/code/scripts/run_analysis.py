"""
Script to run the full analysis pipeline.
This script is invoked by the main pipeline to generate final_results.json.
"""
import argparse
import logging
import sys
from pathlib import Path

from code.src.analysis.run_analysis import main as run_analysis_main

def setup_logging():
    """Setup basic logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    """Main entry point for analysis script."""
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Running analysis via wrapper script...")

    # Simulate command line arguments for the analysis module
    sys.argv = [
        'run_analysis',
        '--config', 'code/config.yaml',
        '--output', 'data'
    ]

    try:
        run_analysis_main()
        logger.info("Analysis completed successfully")
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
