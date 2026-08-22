"""
Generate training data using Lorenz Attractor dynamics.
T008a requirement: Deterministic seeding, distinct from test data.
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

from src.data.benchmarks import generate_lorenz_attractor, save_generated_data

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    output_dir = project_root / "data" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Starting training data generation (Lorenz Attractor)...")
    
    # Configuration for reproducibility
    config = {
        "seed": 42,
        "num_samples": 5000,
        "sequence_length": 100,
        "dt": 0.01,
        "params": {
            "sigma": 10.0,
            "rho": 28.0,
            "beta": 8.0/3.0
        },
        "noise_level": 0.01,
        "output_file": "training_data_lorenz.npy"
    }

    logger.info(f"Generating {config['num_samples']} samples with seed {config['seed']}")
    
    # Generate data
    data = generate_lorenz_attractor(
        num_samples=config['num_samples'],
        sequence_length=config['sequence_length'],
        dt=config['dt'],
        params=config['params'],
        seed=config['seed'],
        noise_level=config['noise_level']
    )

    # Save data
    output_path = output_dir / config['output_file']
    save_generated_data(data, output_path, config)

    logger.info(f"Training data saved to: {output_path}")
    logger.info(f"Data shape: {data.shape}")
    logger.info(f"Data range: [{data.min():.4f}, {data.max():.4f}]")

    return 0

if __name__ == "__main__":
    sys.exit(main())