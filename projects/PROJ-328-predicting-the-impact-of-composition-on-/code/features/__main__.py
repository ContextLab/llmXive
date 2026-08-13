"""
Main entry point for the features module.
"""
import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from seed import init_reproducibility
from features.transformer import main as run_transformer
from features.descriptor_engine import main as run_descriptor_engine

logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for the features module.
    """
    init_reproducibility()
    logger.info("Starting Features Module")

    # Run transformer test
    logger.info("Running CLR Transformer test...")
    run_transformer()

    # Run descriptor engine test
    logger.info("Running Descriptor Engine test...")
    run_descriptor_engine()

    logger.info("Features Module completed successfully")

if __name__ == "__main__":
    main()