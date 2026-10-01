import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from flops_analysis import main as run_flops_baseline

def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Running Static k=2 Baseline Calculation (T020a)")
    
    try:
        run_flops_baseline()
        logger.info("Static k=2 Baseline calculation completed successfully.")
    except Exception as e:
        logger.error(f"Failed to run Static k=2 Baseline: {e}")
        raise

if __name__ == "__main__":
    main()
