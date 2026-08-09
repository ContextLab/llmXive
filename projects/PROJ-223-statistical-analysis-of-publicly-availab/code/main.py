"""
Main entry point for the Traffic-Weather Severity Analysis Pipeline.
Orchestrates ingestion, modeling, and diagnostics.
"""
import logging
from .ingest import run_ingestion
from .model import run_modeling
from .diagnostics import run_diagnostics
from .config import RANDOM_SEED
import numpy as np

def main():
    """Run the full pipeline."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Set random seed
    np.random.seed(RANDOM_SEED)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Traffic-Weather Severity Analysis Pipeline...")
    
    try:
        # Step 1: Ingestion
        logger.info("--- Step 1: Data Ingestion ---")
        merged_data = run_ingestion()
        
        # Step 2: Modeling
        logger.info("--- Step 2: Ordinal Logistic Regression ---")
        model_results = run_modeling()
        
        # Step 3: Diagnostics
        logger.info("--- Step 3: Diagnostics ---")
        diag_results = run_diagnostics()
        
        logger.info("Pipeline completed successfully.")
        return {
            'ingestion': merged_data,
            'modeling': model_results,
            'diagnostics': diag_results
        }
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
