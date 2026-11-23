"""
Script to generate the Cost of Biological Plausibility curve.

This script is the entry point for T074. It invokes the cost curve generator
and ensures the output file is written to the correct location.
"""

import os
import sys
import logging
from pathlib import Path

# Add code to path
code_root = Path(__file__).parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.utils.cost_curve_generator import main as generate_cost_curve_main

def main():
    """Entry point for the cost curve generation script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)
    logger.info("Starting cost curve generation script...")

    try:
        generate_cost_curve_main()
        logger.info("Cost curve generation completed successfully.")
    except Exception as e:
        logger.error(f"Cost curve generation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()