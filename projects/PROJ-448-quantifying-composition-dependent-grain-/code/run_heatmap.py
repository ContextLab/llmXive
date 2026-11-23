"""
Entry point script to generate the segregation heatmap.
This script orchestrates the execution of the plotter service to produce
data/figures/segregation_heatmap.png as required by task T024b.
"""
import logging
import sys
from pathlib import Path

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from code.services.plotter import main as plotter_main
from code.config import get_logger

def main():
    logger = get_logger(__name__)
    logger.info("Starting heatmap generation pipeline (T024b)...")
    
    try:
        # Execute the plotting logic from T024a
        plotter_main()
        logger.info("Heatmap generation completed successfully.")
    except Exception as e:
        logger.error(f"Failed to generate heatmap: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()