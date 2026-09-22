"""
Script to run the Final Report Generation.
Generates the final markdown report combining all metrics and analyses.
"""
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.validation.final_evaluator import main as run_pipeline
from src.utils.logging_config import setup_logging

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Executing Final Report Generation Script...")
    run_pipeline()
    logger.info("Final Report Generation Script completed.")

if __name__ == "__main__":
    main()
