"""
Generate independent test data using Polynomial Surfaces.
T008c requirement: Distinct distribution from training data (Lorenz).
T008b requirement: Verify independence by design (different generator).
"""
import os
import sys
import json
import logging
from pathlib import Path
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.data.benchmarks import generate_polynomial_surface_data, save_generated_data, verify_independence

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    output_dir = project_root / "data" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Starting test data generation (Polynomial Surfaces)...")
    
    # Configuration for reproducibility
    config = {
        "seed": 12345,  # Different from training seed
        "num_samples": 1000,
        "degree": 3,
        "num_features": 5,
        "noise_level": 0.05,
        "output_file": "test_data_polynomial.npy"
    }

    logger.info(f"Generating {config['num_samples']} samples with seed {config['seed']}")
    logger.info("Using Polynomial Surfaces (distinct from Lorenz training data)")
    
    # Generate data
    data = generate_polynomial_surface_data(
        num_samples=config['num_samples'],
        degree=config['degree'],
        num_features=config['num_features'],
        seed=config['seed'],
        noise_level=config['noise_level']
    )

    # Save data
    output_path = output_dir / config['output_file']
    save_generated_data(data, output_path, config)

    logger.info(f"Test data saved to: {output_path}")
    logger.info(f"Data shape: {data.shape}")
    logger.info(f"Data range: [{data.min():.4f}, {data.max():.4f}]")

    # Verify independence from training data if it exists
    training_path = output_dir / "training_data_lorenz.npy"
    if training_path.exists():
        logger.info("Verifying independence from training data...")
        train_data = np.load(training_path)
        is_independent = verify_independence(train_data, data)
        
        if is_independent:
            logger.info("Independence verification PASSED: Generators are distinct by design.")
        else:
            logger.error("Independence verification FAILED: Generators may not be distinct.")
            return 1
    else:
        logger.warning("Training data not found, skipping independence verification.")

    return 0

if __name__ == "__main__":
    sys.exit(main())