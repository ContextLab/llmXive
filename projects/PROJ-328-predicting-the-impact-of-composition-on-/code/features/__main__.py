"""
Main entry point for the features package.
Orchestrates the feature engineering pipeline.
"""
import sys
import logging
from pathlib import Path
from seed import init_reproducibility
from features.transformer import main as run_transformer
from features.descriptor_engine import main as run_descriptor_engine
from features.collinearity import main as run_collinearity
from utils.logging_config import get_logger

logger = get_logger(__name__)

def main():
    """
    Run the full feature engineering pipeline.
    Order:
    1. CLR Transform (T023b)
    2. Descriptor Engine (T023c)
    3. Collinearity Analysis (T024)
    """
    logger.info("Starting Feature Engineering Pipeline")
    init_reproducibility(seed=42)
    
    try:
        # Step 1: CLR Transform
        logger.info("--- Step 1: CLR Transformation ---")
        run_transformer()
        
        # Step 2: Descriptor Engine
        logger.info("--- Step 2: Physical Descriptors ---")
        run_descriptor_engine()
        
        # Step 3: Collinearity
        logger.info("--- Step 3: Collinearity Analysis ---")
        run_collinearity()
        
        logger.info("Feature Engineering Pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()