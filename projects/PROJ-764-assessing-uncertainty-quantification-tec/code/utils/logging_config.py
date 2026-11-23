import logging
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Any

def setup_logging(log_file: str = "logs/pipeline.log") -> logging.Logger:
    """Configure logging to output to a file and console with timestamps and metric keys.
    
    Args:
        log_file: Path to the log file. Defaults to "logs/pipeline.log".
        
    Returns:
        Configured logger instance.
    """
    log_path = Path(log_file)
    log_dir = log_path.parent
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("pipeline")
    logger.setLevel(logging.INFO)

    # Clear existing handlers to prevent duplicate logs on re-runs
    logger.handlers = []

    # File handler
    fh = logging.FileHandler(log_path)
    fh.setLevel(logging.INFO)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Formatter with timestamp, level, and message
    # Format: 2023-10-27 10:00:00,123 - pipeline - INFO - message
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

def log_metric(logger: logging.Logger, key: str, value: Any, extra: dict = None):
    """Log a specific metric key-value pair with structured formatting.
    
    This function ensures metrics are logged in a parseable format for downstream
    analysis, adhering to the requirement for "metric keys".
    
    Args:
        logger: The logger instance to use.
        key: The metric key (e.g., 'epoch_time', 'loss', 'accuracy').
        value: The metric value (float, int, or string).
        extra: Optional dictionary for additional context (e.g., {'epoch': 5}).
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    
    # Construct a structured log message for metrics
    message_parts = [f"METRIC: {key}={value}"]
    if extra:
        extra_str = ", ".join(f"{k}={v}" for k, v in extra.items())
        message_parts.append(f"[{extra_str}]")
    
    log_message = " ".join(message_parts)
    logger.info(log_message)

def log_pipeline_start(logger: logging.Logger, config: dict = None):
    """Log the start of the pipeline with configuration details.
    
    Args:
        logger: The logger instance.
        config: Optional configuration dictionary to log.
    """
    logger.info("--- PIPELINE START ---")
    if config:
        logger.info(f"CONFIG: {json.dumps(config, indent=2)}")
    else:
        logger.info("CONFIG: (none provided)")

def log_pipeline_end(logger: logging.Logger, success: bool = True, duration: float = None):
    """Log the end of the pipeline.
    
    Args:
        logger: The logger instance.
        success: Whether the pipeline completed successfully.
        duration: Total duration in seconds if available.
    """
    status = "SUCCESS" if success else "FAILURE"
    msg = f"--- PIPELINE END: {status} ---"
    if duration is not None:
        msg += f" (Duration: {duration:.2f}s)"
    logger.info(msg)

def log_training_metrics(
    logger: logging.Logger,
    epoch: int,
    epoch_time: float,
    total_training_time: float,
    loss: float = None,
    val_loss: float = None
):
    """Log training-specific metrics including epoch time and total training time.
    
    This function specifically addresses the requirement to record 'epoch_time' 
    and 'total_training_time' to the pipeline log file in a structured, parseable format.
    
    Args:
        logger: The logger instance to use.
        epoch: Current epoch number.
        epoch_time: Time taken for the current epoch in seconds.
        total_training_time: Cumulative time spent training in seconds.
        loss: Training loss for the current epoch (optional).
        val_loss: Validation loss for the current epoch (optional).
    """
    # Log epoch time metric
    log_metric(logger, "epoch_time", epoch_time, {"epoch": epoch})
    
    # Log total training time metric
    log_metric(logger, "total_training_time", total_training_time, {"epoch": epoch})
    
    # Log loss metrics if provided
    if loss is not None:
        log_metric(logger, "train_loss", loss, {"epoch": epoch})
    
    if val_loss is not None:
        log_metric(logger, "val_loss", val_loss, {"epoch": epoch})