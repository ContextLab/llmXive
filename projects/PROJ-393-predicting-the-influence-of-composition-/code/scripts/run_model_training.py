"""
Script to run the Model Training Pipeline.
Trains Linear and Random Forest models and saves metrics.
"""
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.models.training_pipeline import main as run_pipeline
from src.utils.logging_config import setup_logging

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Executing Model Training Pipeline Script...")
    run_pipeline()
    logger.info("Model Training Pipeline Script completed.")

if __name__ == "__main__":
    main()
