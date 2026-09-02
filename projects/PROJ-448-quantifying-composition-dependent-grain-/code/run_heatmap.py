"""
Script to generate the segregation heatmap figure (T024b).
This script integrates the plotting logic from T024a (code/services/plotter.py)
to produce the final artifact: data/figures/segregation_heatmap.png.
"""
import logging
import sys
from pathlib import Path

# Add project root to path to ensure imports work correctly
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.services.plotter import main as plotter_main
from code.config import get_logger

def main():
    """
    Entry point for T024b.
    Executes the plotting service to generate data/figures/segregation_heatmap.png.
    """
    logger = get_logger("T024b_Heatmap")
    logger.info("Starting T024b: Integrating plotting logic to generate segregation heatmap.")
    
    try:
        # Delegate to the plotting service implementation (T024a)
        # This function reads data/processed/segregation_profiles.json and writes
        # data/figures/segregation_heatmap.png
        plotter_main()
        
        logger.info("T024b completed successfully. Output: data/figures/segregation_heatmap.png")
    except Exception as e:
        logger.error(f"T024b failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
