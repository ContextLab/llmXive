"""
Runner script to execute T006b: Entropy Calculation.
This script is invoked by the main pipeline to ensure the output file
data/processed/entropy_metrics.csv is generated.
"""
import sys
import logging
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent
sys.path.insert(0, str(code_dir))

from entropy import main as entropy_main

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting T006b: Entropy Calculation")
    try:
        entropy_main()
        logger.info("T006b completed successfully.")
    except Exception as e:
        logger.error(f"T006b failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()