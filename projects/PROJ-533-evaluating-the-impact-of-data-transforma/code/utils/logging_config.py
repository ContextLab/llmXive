"""
Logging configuration for the llmXive pipeline.
Configures a logger that writes to results/pipeline.log.
"""
import logging
import os
from pathlib import Path
from typing import Optional

def setup_pipeline_logger(log_file: str = "results/pipeline.log") -> logging.Logger:
    """
    Configure and return a logger that writes to the specified log file.
    
    The log format includes timestamp, level, and message to record:
    - Dataset exclusions
    - Imputation rates
    - Transformation interventions
    
    Args:
        log_file: Path to the log file (default: results/pipeline.log)
    
    Returns:
        A configured logger instance named "pipeline"
    """
    # Ensure the log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger("pipeline")
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    # Create formatter with specific format for pipeline events
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(file_handler)
    
    # Prevent propagation to root logger to avoid duplicate logs
    logger.propagate = False
    
    return logger

def log_exclusion(logger: logging.Logger, dataset_id: str, reason: str) -> None:
    """
    Log a dataset exclusion event.
    
    Args:
        logger: The pipeline logger instance
        dataset_id: The ID of the excluded dataset
        reason: The reason for exclusion (e.g., "Shapiro p > 0.05", "N < 30")
    """
    logger.info(f"EXCLUSION: dataset_id={dataset_id} reason={reason}")

def log_imputation_rate(logger: logging.Logger, dataset_id: str, rate: float) -> None:
    """
    Log the imputation rate for a dataset.
    
    Args:
        logger: The pipeline logger instance
        dataset_id: The ID of the dataset
        rate: The fraction of missing values imputed (0.0 to 1.0)
    """
    logger.info(f"IMPUTATION: dataset_id={dataset_id} rate={rate:.4f}")

def log_transformation_intervention(logger: logging.Logger, dataset_id: str, 
                                   transformation: str, intervention: str) -> None:
    """
    Log a transformation intervention event.
    
    Args:
        logger: The pipeline logger instance
        dataset_id: The ID of the dataset
        transformation: The transformation type (e.g., "box_cox", "yeo_johnson")
        intervention: The specific intervention applied (e.g., "log_shift applied for negative values")
    """
    logger.info(f"TRANSFORMATION: dataset_id={dataset_id} type={transformation} intervention={intervention}")