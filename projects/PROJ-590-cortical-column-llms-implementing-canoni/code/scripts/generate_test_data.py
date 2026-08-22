import os
import sys
import json
import logging
from pathlib import Path
import numpy as np

# Add project root to path to allow imports from src
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.data.benchmarks import generate_polynomial_surface_data, save_generated_data

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    """
    Generate independent test data using polynomial surfaces.
    This data is distinct from the Lorenz attractor training data by design.
    
    Output: data/results/test_data_polynomial.npy
    """
    logger.info("Starting test data generation (T008c)...")
    
    # Ensure output directory exists
    output_dir = project_root / "data" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "test_data_polynomial.npy"
    
    logger.info(f"Generating polynomial surface test data...")
    logger.info("Using polynomial surfaces to ensure statistical independence from Lorenz training data.")
    
    # Generate test data using polynomial surfaces (distinct from Lorenz/Fourier training)
    # Parameters chosen to provide a robust test set for generalization
    test_data = generate_polynomial_surface_data(
        n_samples=5000,
        n_features=10,
        max_degree=4,
        noise_std=0.01,
        seed=42
    )
    
    logger.info(f"Generated test data shape: {test_data.shape}")
    
    # Save the data
    logger.info(f"Saving test data to {output_path}")
    save_generated_data(test_data, str(output_path))
    
    # Verify the file was written
    if output_path.exists():
        file_size = output_path.stat().st_size
        logger.info(f"Successfully wrote {file_size} bytes to {output_path}")
        
        # Load and verify integrity
        loaded_data = np.load(output_path)
        assert loaded_data.shape == test_data.shape, "Shape mismatch after save/load"
        assert np.allclose(loaded_data, test_data), "Data integrity check failed"
        logger.info("Data integrity verified.")
    else:
        logger.error("Failed to write output file!")
        sys.exit(1)
    
    logger.info("Test data generation completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
