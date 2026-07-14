"""
Task T001c: Create data directory: data/results/

This script ensures the existence of the data/results/ directory
as required by the project setup phase.
"""
import os
import sys
from pathlib import Path
import logging

# Add parent directory to path to allow imports from code/
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_config, ensure_dirs

def main():
    """
    Main entry point for T001c.
    Creates the data/results/ directory if it doesn't exist.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("T001c")

    logger.info("Starting T001c: Creating data/results/ directory")

    # Load configuration
    config = get_config()
    
    # Get the data directory path from config
    data_dir = Path(config.get('paths', {}).get('data', 'data'))
    results_dir = data_dir / 'results'

    logger.info(f"Ensuring directory exists: {results_dir}")
    
    # Use the ensure_dirs utility from config module
    # This function is already imported in the API surface
    ensure_dirs([results_dir], logger=logger)

    # Verify creation
    if results_dir.exists() and results_dir.is_dir():
        logger.info(f"SUCCESS: Directory {results_dir} created or already exists.")
        # Create a placeholder .gitkeep file to ensure the directory is tracked
        gitkeep = results_dir / '.gitkeep'
        if not gitkeep.exists():
            gitkeep.touch()
            logger.info(f"Created placeholder file: {gitkeep}")
        return 0
    else:
        logger.error(f"FAILED: Directory {results_dir} was not created.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
