"""
Script to run stability tests and verify divergence handling.

This script executes the stability checks and demonstrates the mandatory
edge case handling for simulation divergence.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.simulation.stability import main as stability_main
from code.src.utils.logging import init_logging
from code.src.utils.config import load_config


def setup_logging() -> logging.Logger:
    """Configure logging for the stability test script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('data/run_stability_test.log')
        ]
    )
    return logging.getLogger(__name__)


def main() -> int:
    """
    Main entry point for running stability tests.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger = setup_logging()
    logger.info("Starting stability tests...")
    
    try:
        # Initialize logging infrastructure
        init_logging()
        
        # Load configuration
        config = load_config()
        logger.info(f"Loaded configuration with seed: {config.get('global_seed', 'N/A')}")
        
        # Run stability tests
        stability_main()
        
        logger.info("Stability tests completed successfully.")
        return 0
        
    except Exception as e:
        logger.error(f"Stability tests failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run numerical stability tests for spin simulations"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="code/config.yaml",
        help="Path to configuration file"
    )
    
    args = parser.parse_args()
    sys.exit(main())