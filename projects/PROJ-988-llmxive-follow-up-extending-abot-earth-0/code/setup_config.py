"""
Script to initialize environment configuration files.

Creates the default city_list.txt if it doesn't exist and
demonstrates the configuration loading mechanism.
"""
import os
import sys
from pathlib import Path
import logging

# Add code to path
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

from lib.config import load_environment_config, ConfigError
from lib.logging_config import setup_logging, get_logger

def main():
    """Main entry point for configuration setup."""
    # Setup logging
    log_path = Path("data/results/execution.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    setup_logging(log_file=str(log_path))
    
    logger = get_logger(__name__)
    logger.info("Starting environment configuration setup...")

    try:
        # Initialize config
        config = load_environment_config()
        
        # Ensure data directories exist
        paths = config.paths
        for path_name, path_obj in paths.items():
            path_obj.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {path_obj}")

        # Load cities
        cities = config.load_city_list()
        logger.info(f"Successfully loaded {len(cities)} cities.")

        # Set a default seed for reproducibility
        config.set_random_seed(42)
        logger.info(f"Set random seed to {config.get_random_seed()}")

        # Save configuration to results
        config_output_path = paths["data_results"] / "environment_config.json"
        config.save_config(config_output_path)
        logger.info(f"Configuration saved to {config_output_path}")

        logger.info("Environment configuration setup completed successfully.")
        return 0

    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during setup: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
