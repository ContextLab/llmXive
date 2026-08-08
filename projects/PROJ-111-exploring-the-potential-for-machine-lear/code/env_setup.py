"""
Environment setup script.
Initializes logging and validates the configuration environment.
This script should be run at the start of any major pipeline stage.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from logging_config import setup_logging, get_logger
from config import get_config, save_config_to_json

def main():
    # Load .env if it exists
    load_dotenv()
    
    # Initialize logging
    logger = setup_logging()
    logger.info("Starting environment setup...")
    
    # Validate configuration
    cfg = get_config()
    logger.info(f"Project Root: {cfg.project_root}")
    logger.info(f"Data Raw Dir: {cfg.data_raw_dir}")
    logger.info(f"Data Processed Dir: {cfg.data_processed_dir}")
    logger.info(f"Logs Dir: {cfg.logs_dir}")
    
    # Validate required directories exist (created by Config init)
    assert cfg.data_raw_dir.exists(), f"Data raw directory missing: {cfg.data_raw_dir}"
    assert cfg.data_processed_dir.exists(), f"Data processed directory missing: {cfg.data_processed_dir}"
    assert cfg.logs_dir.exists(), f"Logs directory missing: {cfg.logs_dir}"
    
    # Save configuration snapshot
    config_snapshot = save_config_to_json()
    logger.info(f"Configuration saved to: {config_snapshot}")
    
    logger.info("Environment setup completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())