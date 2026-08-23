import os
import sys
import json
import logging
from pathlib import Path
import numpy as np

from src.data.benchmarks import (
    generate_training_data,
    generate_polynomial_test_data,
    generate_fourier_test_data,
    verify_independence
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Main script to generate all benchmark datasets.

    This script:
    1. Generates Lorenz attractor training data
    2. Generates polynomial test data (T008c requirement)
    3. Generates Fourier test data (additional robustness)
    4. Verifies independence between train and test sets
    5. Saves all outputs to data/results/
    """
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data" / "results"
    data_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Starting benchmark data generation...")

    # 1. Generate training data (Lorenz attractor)
    train_path = data_dir / "train_data_lorenz.npy"
    logger.info(f"Generating Lorenz training data: {train_path}")
    train_data = generate_training_data(
        n_samples=10000,
        seed=123,
        output_path=str(train_path)
    )
    logger.info(f"Training data shape: {train_data.shape}")

    # 2. Generate polynomial test data (T008c requirement)
    poly_test_path = data_dir / "test_data_polynomial.npy"
    logger.info(f"Generating polynomial test data: {poly_test_path}")
    poly_test_data = generate_polynomial_test_data(
        n_samples=1000,
        n_features=5,
        degree=3,
        seed=42,
        output_path=str(poly_test_path)
    )
    logger.info(f"Polynomial test data shape: {poly_test_data.shape}")

    # 3. Generate Fourier test data (additional)
    fourier_test_path = data_dir / "test_data_fourier.npy"
    logger.info(f"Generating Fourier test data: {fourier_test_path}")
    fourier_test_data = generate_fourier_test_data(
        n_samples=500,
        n_features=3,
        max_freq=10,
        seed=43,
        output_path=str(fourier_test_path)
    )
    logger.info(f"Fourier test data shape: {fourier_test_data.shape}")

    # 4. Verify independence
    logger.info("Verifying independence between train and test sets...")
    is_independent = verify_independence(train_data, poly_test_data)
    if not is_independent:
        logger.error("Independence verification failed!")
        sys.exit(1)

    # 5. Save metadata
    metadata = {
        "train": {
            "path": str(train_path),
            "shape": list(train_data.shape),
            "generator": "lorenz_attractor",
            "seed": 123
        },
        "test_polynomial": {
            "path": str(poly_test_path),
            "shape": list(poly_test_data.shape),
            "generator": "polynomial_surface",
            "seed": 42
        },
        "test_fourier": {
            "path": str(fourier_test_path),
            "shape": list(fourier_test_data.shape),
            "generator": "fourier_series",
            "seed": 43
        },
        "independence_verified": is_independent
    }

    metadata_path = data_dir / "dataset_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved metadata to {metadata_path}")

    logger.info("Benchmark data generation completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
