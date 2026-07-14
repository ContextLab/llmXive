import os
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.logging_config import get_logger
from code.analysis.correlations import main as correlations_main

logger = get_logger(__name__)

def main():
    """
    Wrapper to ensure full metrics are generated.
    Invokes the main logic from correlations.py which handles T023a and T023b.
    """
    logger.log("create_full_metrics_start")
    try:
        correlations_main()
        logger.log("create_full_metrics_success")
    except Exception as e:
        logger.log("create_full_metrics_failed", error=str(e))
        raise

if __name__ == "__main__":
    main()