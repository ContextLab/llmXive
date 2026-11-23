"""
Script to run the Manual Curator pipeline.
Ensures data/raw/manual_curated.csv exists and is valid.
"""
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.ingestion.manual_curator import main as run_pipeline
from src.utils.logging_config import setup_logging

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Executing Manual Curator Script...")
    run_pipeline()
    logger.info("Manual Curator Script completed.")

if __name__ == "__main__":
    main()
