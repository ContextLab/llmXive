"""
Script to initialize the logging infrastructure for the project.

This script can be run to ensure the log directory exists and to
demonstrate the logger setup.
"""

import os
import sys
from pathlib import Path

# Add code directory to path if running as script
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from logging_config import setup_logger
from config import load_config, set_global_seed


def main():
    """Initialize logging and configuration."""
    # Load configuration
    config = load_config()
    set_global_seed(config=config)

    # Setup logger
    log_level_str = config.logging_config.get("level", "INFO")
    log_level = getattr(logging, log_level_str, logging.INFO)
    deterministic = config.logging_config.get("deterministic_console", True)

    logger = setup_logger(
        name="diffusion_pipeline",
        log_level=log_level,
        log_file=str(config.get_path("logs") / "pipeline.log"),
        deterministic=deterministic
    )

    logger.info("Logging infrastructure initialized successfully.")
    logger.info(f"Configuration: {config}")
    logger.info(f"Random seed set to: {config.random_seed}")

    # Ensure log directory exists
    log_dir = config.get_path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Log directory ensured at: {log_dir}")

    return logger


if __name__ == "__main__":
    main()