"""
Main entry point for features module execution.

Runs the full feature engineering pipeline:
1. CLR transformation
2. Descriptor computation
3. Collinearity analysis
"""

import sys
import logging
from pathlib import Path
from seed import init_reproducibility
from features.transformer import main as run_transformer
from features.descriptor_engine import main as run_descriptor_engine
from features.collinearity import main as run_collinearity

logger = logging.getLogger(__name__)

def main():
    """
    Run all feature engineering components.
    """
    init_reproducibility(seed=42)
    
    logger.info("=" * 60)
    logger.info("Starting Feature Engineering Pipeline")
    logger.info("=" * 60)
    
    try:
        logger.info("\n[1/3] Running CLR Transformer test...")
        run_transformer()
        
        logger.info("\n[2/3] Running Descriptor Engine test...")
        run_descriptor_engine()
        
        logger.info("\n[3/3] Running Collinearity Analysis test...")
        run_collinearity()
        
        logger.info("\n" + "=" * 60)
        logger.info("Feature Engineering Pipeline completed successfully")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error("Feature engineering pipeline failed: %s", str(e), exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()