"""
Script to run simulations on generated networks.
This script is invoked by the main pipeline to generate simulation_results.json.
"""
import argparse
import logging
import sys
from pathlib import Path

from code.src.simulation.run_simulation import main as run_simulation_main

def setup_logging():
    """Setup basic logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    """Main entry point for simulation script."""
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Running simulations via wrapper script...")

    # Simulate command line arguments for the simulation module
    sys.argv = [
        'run_simulation',
        '--config', 'code/config.yaml',
        '--output', 'data'
    ]

    try:
        run_simulation_main()
        logger.info("Simulations completed successfully")
    except Exception as e:
        logger.error(f"Simulation failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()