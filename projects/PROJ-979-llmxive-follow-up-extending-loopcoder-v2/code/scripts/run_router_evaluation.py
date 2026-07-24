"""
Script to run the router evaluation (T020).

This script executes the router evaluation logic to compare the dynamic router's
prediction accuracy against a random baseline (predicting k=1 for all samples)
and performs a paired t-test to confirm statistical significance.
"""

import os
import sys
import logging
from pathlib import Path

# Add the code directory to the path
code_dir = Path(__file__).parent.parent
src_dir = code_dir / "src"
sys.path.insert(0, str(code_dir))

from router_evaluation import main as run_router_evaluation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main() -> None:
    """
    Main entry point for the router evaluation script.
    """
    logger.info("Starting router evaluation script (T020)...")

    # Run the evaluation
    run_router_evaluation()

    logger.info("Router evaluation script completed.")


if __name__ == "__main__":
    main()
