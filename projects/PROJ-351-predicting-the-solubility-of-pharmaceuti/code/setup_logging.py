"""
Logging Setup (Task T008)

Configures logging infrastructure for the project.
"""
import os
import sys
import logging
import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "data" / "logs"

def setup_logger(name: str, log_file: str = "pipeline.log", level: int = logging.INFO) -> logging.Logger:
    """
    Sets up a logger with console and file handlers.
    
    Args:
        name: Logger name.
        log_file: Name of the log file (relative to data/logs/).
        level: Logging level.
    
    Returns:
        Configured logger.
    """
    log_dir = Path(LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    full_log_path = log_dir / log_file
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    
    # File Handler
    file_handler = logging.FileHandler(full_log_path)
    file_handler.setLevel(level)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

def log_exclusion_counts(exclusion_counts: dict) -> None:
    """
    Logs exclusion counts to a JSON file.
    
    Args:
        exclusion_counts: Dictionary of exclusion counts.
    """
    log_dir = Path(LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "exclusions.json"
    
    with open(log_file, 'w') as f:
        json.dump(exclusion_counts, f, indent=2)
    logging.info(f"Exclusion counts logged to {log_file}")

def log_training_metrics(metrics: dict) -> None:
    """
    Logs training metrics to a JSON file.
    
    Args:
        metrics: Dictionary of training metrics.
    """
    log_dir = Path(LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "training_metrics.json"
    
    with open(log_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    logging.info(f"Training metrics logged to {log_file}")

def main():
    """
    Main entry point for logging setup (T008).
    """
    logger = setup_logger("setup_logging")
    logger.info("Logging infrastructure configured successfully.")

if __name__ == "__main__":
    main()