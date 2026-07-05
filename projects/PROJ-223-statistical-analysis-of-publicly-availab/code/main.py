"""
Main entry point for the pipeline.
"""
import logging
from .ingest import run_ingestion
from .model import run_modeling
from .diagnostics import run_diagnostics
from .config import RANDOM_SEED
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """
    Run the full pipeline.
    """
    logger.info("Starting Traffic-Weather Severity Analysis Pipeline")
    np.random.seed(RANDOM_SEED)

    run_ingestion()
    run_modeling()
    run_diagnostics()

    logger.info("Pipeline completed successfully")

if __name__ == "__main__":
    main()