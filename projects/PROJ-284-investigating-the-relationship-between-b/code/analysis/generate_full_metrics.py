"""
Alternative runner for full metrics generation.
Calls the correlations module's main function to ensure consistency.
"""
import os
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.logging_config import get_logger
from code.analysis.correlations import main as correlations_main

logger = get_logger(__name__)

def main():
    """Main entry point."""
    logger.log("generate_full_metrics_start", {})

    try:
        correlations_main()
        logger.log("generate_full_metrics_complete", {})
    except Exception as e:
        logger.log("generate_full_metrics_error", {"error": str(e)})
        raise

if __name__ == "__main__":
    main()
