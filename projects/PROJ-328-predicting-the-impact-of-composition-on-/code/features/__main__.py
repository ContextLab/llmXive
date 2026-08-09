"""
Main entry point for the features module.
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from seed import init_reproducibility
from features.transformer import main as run_transformer
from features.descriptor_engine import main as run_descriptor_engine
from features.collinearity import main as run_collinearity

logger = logging.getLogger(__name__)


def main():
    """
    Run all feature engineering self-tests.
    """
    init_reproducibility(seed=42)

    logger.info("Starting Feature Engineering Module Self-Tests...")

    try:
        logger.info("--- Running Transformer Test ---")
        run_transformer()
    except Exception as e:
        logger.error("Transformer test failed: %s", e)

    try:
        logger.info("--- Running Descriptor Engine Test ---")
        run_descriptor_engine()
    except Exception as e:
        logger.error("Descriptor Engine test failed: %s", e)

    try:
        logger.info("--- Running Collinearity Test ---")
        run_collinearity()
    except Exception as e:
        logger.error("Collinearity test failed: %s", e)

    logger.info("Feature Engineering Module Self-Tests Completed.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()