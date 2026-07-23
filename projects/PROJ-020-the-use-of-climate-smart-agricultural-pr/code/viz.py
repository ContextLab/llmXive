"""
Wrapper script to execute the visualization logic defined in code/viz/plots.py.

This script serves as the entry point referenced in quickstart.md to generate
all visualization artifacts (scatter plots, coefficient plots, distribution plots)
from the processed data and model results.

Usage:
    python code/viz.py
"""
import logging
import sys
from pathlib import Path

# Ensure the code directory is in the path for relative imports
code_root = Path(__file__).resolve().parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from viz.plots import main as viz_main
from utils.logging import initialize_logging

def main():
    """
    Entry point for the visualization wrapper.
    Initializes logging and delegates to the core viz.plots module.
    """
    # Initialize logging
    log_path = code_root / "state" / "viz.log"
    initialize_logging(log_path=log_path, level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info("Starting visualization wrapper script (viz.py)...")
    
    try:
        # Delegate to the core visualization pipeline
        viz_main()
        logger.info("Visualization pipeline completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Missing required data file: {e}")
        logger.error("Ensure that the data ingestion and modeling pipelines have run successfully.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Visualization pipeline failed with unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()