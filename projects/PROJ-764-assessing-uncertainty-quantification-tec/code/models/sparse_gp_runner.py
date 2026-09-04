"""
Runner script for T015c: Save the fitted GP model.

This script executes the training and saving process for the Sparse GP model,
ensuring the output artifact `results/models/sparse_gp_model.pt` is generated.

Dependencies:
  - T015a: Verification that input files exist
  - T015b: Fitting the GP model
  - T006b3: Preprocessed PCA features available
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the Sparse GP model saving task."""
    logger.info("Starting T015c: Sparse GP Model Saving")
    
    # Import the training and saving functions
    from models.sparse_gp import main as sparse_gp_main
    
    # Execute the training and saving process
    # This will:
    # 1. Load preprocessed features from data/processed/features_test_20pca.csv
    # 2. Train the Sparse GP model on the training data
    # 3. Save the fitted model to results/models/sparse_gp_model.pt
    try:
        sparse_gp_main()
        logger.info("T015c completed successfully: Model saved to results/models/sparse_gp_model.pt")
    except Exception as e:
        logger.error(f"T015c failed: {str(e)}")
        raise

if __name__ == '__main__':
    main()