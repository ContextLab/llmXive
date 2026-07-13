import os
import sys
import logging
import json
from pathlib import Path
from datetime import datetime

# Ensure the log directory exists
LOG_DIR = Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

def setup_logger(name: str, log_file: str = None, level: int = logging.INFO) -> logging.Logger:
    """
    Sets up a logger with console and optional file output.
    
    Args:
        name: The name of the logger.
        log_file: Relative path to the log file within data/logs/. 
                  If None, only console output is used.
        level: Logging level (e.g., logging.INFO).
    
    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times if called repeatedly
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler
    if log_file:
        log_path = LOG_DIR / log_file
        fh = logging.FileHandler(log_path)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

def log_exclusion_counts(logger: logging.Logger, total_count: int, excluded_count: int, reason: str = "Invalid SMILES"):
    """
    Logs the count of excluded items (e.g., invalid SMILES) to the logger.
    
    Args:
        logger: The logger instance.
        total_count: Total number of items processed.
        excluded_count: Number of items excluded.
        reason: The reason for exclusion.
    """
    if excluded_count > 0:
        logger.warning(f"Exclusion Summary: {excluded_count}/{total_count} items excluded due to {reason}.")
    else:
        logger.info(f"Exclusion Summary: {excluded_count}/{total_count} items excluded due to {reason}.")

def log_training_metrics(logger: logging.Logger, metrics: dict, epoch: int = -1):
    """
    Logs training metrics (e.g., RMSE, R2) to the logger and optionally to a JSON file.
    
    Args:
        logger: The logger instance.
        metrics: Dictionary of metric names to values.
        epoch: Current epoch number (optional, -1 if not applicable).
    """
    if epoch >= 0:
        logger.info(f"Epoch {epoch} Metrics: {metrics}")
    else:
        logger.info(f"Final Training Metrics: {metrics}")
    
    # Also save a snapshot of metrics to a JSON file for easy parsing
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    metrics_file = LOG_DIR / f"training_metrics_{timestamp}.json"
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=4)
    logger.info(f"Metrics saved to {metrics_file}")

def main():
    """
    Main function to demonstrate logging setup and usage.
    This script ensures the logging infrastructure is configured
    and logs a sample exclusion count and training metric.
    """
    # Setup logger
    logger = setup_logger("PipelineLogger", "pipeline_run.log")
    
    logger.info("Logging infrastructure initialized.")
    
    # Simulate exclusion logging
    log_exclusion_counts(logger, total_count=1000, excluded_count=42, reason="Invalid SMILES or NaN logS")
    
    # Simulate training metrics logging
    sample_metrics = {
        "rmse": 0.85,
        "r_squared": 0.72,
        "mae": 0.65
    }
    log_training_metrics(logger, sample_metrics)

    logger.info("Logging demonstration complete.")

if __name__ == "__main__":
    main()