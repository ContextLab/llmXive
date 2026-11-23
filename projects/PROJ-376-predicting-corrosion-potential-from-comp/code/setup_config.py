"""
Script to initialize and save default configuration.

Usage:
    python code/setup_config.py [--config PATH]

This script creates the default configuration file and ensures all
required directories exist.
"""
import sys
from pathlib import Path
import argparse
from utils.config import (
    ProjectConfig,
    ConfigManager,
    get_config,
    set_random_seed,
    save_config,
    get_path
)
from utils.logging import get_logger

logger = get_logger(__name__)


def ensure_directories():
    """Create all required directories."""
    config = get_config()
    
    directories = [
        get_path("data_root"),
        get_path("data_raw"),
        get_path("data_processed"),
        get_path("data_figures"),
        get_path("data_interpretability"),
        get_path("logs_root"),
        get_path("logs_diagnostics"),
        get_path("code_root"),
        get_path("config_root"),
        get_path("state_root"),
        get_path("contracts_root"),
    ]
    
    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory: {dir_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Initialize pipeline configuration"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to save configuration file"
    )
    args = parser.parse_args()
    
    logger.info("Starting configuration initialization...")
    
    # Initialize config
    config_manager = ConfigManager.get_instance()
    config = config_manager.initialize()
    
    logger.info(f"Project root: {config.project_root}")
    logger.info(f"Random seed: {config.random_seed}")
    
    # Set random seed for reproducibility
    set_random_seed(config.random_seed)
    
    # Ensure directories exist
    ensure_directories()
    
    # Save configuration
    if args.config:
        config_path = Path(args.config)
    else:
        config_path = get_path("config_root") / "pipeline_config.yaml"
    
    save_config(config, config_path)
    
    logger.info(f"Configuration initialized and saved to {config_path}")
    logger.info("Configuration management setup complete.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
