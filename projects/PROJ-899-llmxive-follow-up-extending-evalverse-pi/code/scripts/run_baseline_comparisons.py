import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.evaluate import main as evaluate_main
from src.utils import setup_logging

def main() -> None:
    """Wrapper to run baseline comparisons."""
    logger = setup_logging("run_baseline_comparisons")
    logger.info("Running baseline comparisons (T019a)...")
    
    try:
        evaluate_main()
        logger.info("Baseline comparisons completed successfully.")
    except Exception as e:
        logger.error(f"Failed to run baseline comparisons: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
