import os
import sys
import logging
from pathlib import Path
from code.analysis.correlations import main as correlations_main
from code.logging_config import get_logger

logger = get_logger(__name__)

def main():
    """Runner for PCA analysis."""
    logger.info("Running PCA analysis via correlations module...")
    try:
        correlations_main()
    except Exception as e:
        logger.error(f"PCA analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
