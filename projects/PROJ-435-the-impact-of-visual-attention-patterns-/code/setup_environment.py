"""
Environment setup script for the visual attention study.
Initializes configuration, sets up reproducibility, and creates necessary directories.
"""
import os
import sys
import logging
from pathlib import Path
import yaml
import random
import numpy as np

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.environment_manager import (
    load_config,
    setup_reproducibility,
    get_paths,
    setup_logging
)

def main():
    """
    Main function to set up the project environment.
    """
    # Setup logging
    logger = setup_logging()
    logger.info("Starting environment setup...")

    # Load configuration
    try:
        config = load_config()
        logger.info("Configuration loaded successfully")
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        # Create default config if it doesn't exist
        logger.info("Creating default configuration file...")
        default_config = {
            "random_seed": 42,
            "numpy_seed": 42,
            "python_seed": 42,
            "paths": {
                "raw_data_dir": "data/raw",
                "derived_data_dir": "data/derived",
                "processed_data_dir": "data/processed",
                "state_dir": "state",
                "figures_dir": "figures"
            },
            "fixation_detection": {
                "ivt_duration_threshold": 60,
                "idt_dispersion_threshold": 30,
                "velocity_threshold": 30
            },
            "analysis": {
                "outlier_cap_percentile_low": 1,
                "outlier_cap_percentile_high": 99,
                "regression_confidence_level": 0.95
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "state/pipeline.log"
            }
        }
        
        config_path = Path("code/config.yaml")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            yaml.dump(default_config, f)
        
        logger.info(f"Default configuration created at {config_path}")
        config = load_config()

    # Setup reproducibility
    seed = setup_reproducibility()
    logger.info(f"Random seed set to: {seed}")

    # Create necessary directories
    paths = get_paths()
    logger.info("Creating project directories...")
    
    for name, path in paths.items():
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"  Created: {path}")

    # Write seed information to state file
    state_dir = paths['state']
    seed_file = state_dir / "seed_info.json"
    import json
    seed_info = {
        "random_seed": seed,
        "setup_time": str(Path(__file__).parent.parent / "state" / "seed_info.json"),
        "config_file": str(Path("code/config.yaml").absolute())
    }
    
    with open(seed_file, 'w') as f:
        json.dump(seed_info, f, indent=2)
    
    logger.info(f"Seed information written to {seed_file}")

    logger.info("Environment setup completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())