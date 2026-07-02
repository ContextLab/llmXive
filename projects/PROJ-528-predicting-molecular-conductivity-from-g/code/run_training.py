"""
Entry point script to run the model training pipeline.
This script ensures data is available and then runs T029.
"""
import os
import sys
import logging
import pandas as pd

from code.logging_config import setup_logging
from code.data_loader import load_smiles

logger = setup_logging()

def ensure_sample_data():
    """Ensure sample data exists for training."""
    sample_path = os.path.join("data", "raw", "sample_molecules.csv")
    
    if os.path.exists(sample_path):
        logger.info(f"Sample data already exists at {sample_path}")
        return True
    
    logger.info("Creating sample data file...")
    os.makedirs("data/raw", exist_ok=True)
    
    # Create a small sample dataset
    data = {
        'smiles': [
            'c1ccccc1', 'C1=CC=CC=C1', 'C1CCCCC1', 'c1ccncc1', 
            'C1=CC=CC=CC=C1', 'C1CCCC1', 'c1ccc2ccccc2c1',
            'C1=CC=C(C=C1)C=CC2=CC=CC=C2', 'C1CCCCC1C', 'c1ccc(cc1)O',
            'c1ccc(cc1)N', 'c1ccc(cc1)C(=O)O', 'C1=CC=C(C=C1)O',
            'C1=CC=C(C=C1)N', 'C1=CC=C(C=C1)C(=O)O', 'c1ccc2c(c1)ccc3c2cccc3',
            'c1ccc2c(c1)ccc3c2cccc3', 'C1=CC=CC=C1C=CC2=CC=CC=C2',
            'C1=CC=CC=C1C', 'C1=CC=CC=C1CC'
        ],
        'conductivity': [
            0.5, 0.6, 0.1, 0.7, 0.8, 0.05, 0.9, 1.2, 0.12, 0.4,
            0.45, 0.35, 0.38, 0.42, 0.32, 1.1, 1.05, 0.95, 0.15, 0.18
        ]
    }
    
    df = pd.DataFrame(data)
    df.to_csv(sample_path, index=False)
    logger.info(f"Created sample data at {sample_path}")
    return True

def main():
    """Main execution function."""
    logger.info("Starting training pipeline setup")
    
    # Ensure sample data exists
    ensure_sample_data()
    
    # Import and run training
    try:
        from code.train_models import main as run_training
        results = run_training()
        logger.info("Training pipeline completed successfully")
        print(f"Training completed. R² (RF): {results['rf_r2']:.4f}, R² (GB): {results['gb_r2']:.4f}")
    except Exception as e:
        logger.error(f"Training pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
