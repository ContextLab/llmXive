"""
Logging infrastructure for the neural correlates pipeline.
Provides standardized loggers, formatters, and handlers for all pipeline stages.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Global logger registry to avoid duplicate handlers
_loggers_initialized: Dict[str, bool] = {}

# Log directory path (relative to project root)
LOG_DIR = Path("data/logs")

def get_log_dir() -> Path:
    """Ensure log directory exists and return its path."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    return LOG_DIR

def get_log_filename(stage_name: str) -> Path:
    """Generate a timestamped log filename for a specific stage."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return get_log_dir() / f"{stage_name}_{timestamp}.log"

def configure_logger(
    name: str,
    level: int = logging.INFO,
    stage_name: Optional[str] = None,
    log_to_file: bool = True,
    log_to_console: bool = True
) -> logging.Logger:
    """
    Configure and return a logger with standardized formatting.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level (e.g., logging.DEBUG, logging.INFO)
        stage_name: Optional stage identifier for file naming
        log_to_file: Whether to write logs to file
        log_to_console: Whether to write logs to console
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Prevent duplicate handlers if logger already configured
    if name in _loggers_initialized:
        logger.setLevel(level)
        return logger
    
    logger.setLevel(level)
    logger.propagate = False  # Prevent double logging to root
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        logger.addHandler(console_handler)
    
    # File handler
    if log_to_file:
        if stage_name:
            log_file = get_log_filename(stage_name)
        else:
            log_file = get_log_filename(name.split('.')[-1])
        
        # Ensure log directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)
    
    _loggers_initialized[name] = True
    return logger

def get_pipeline_logger(stage_name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get a logger specifically for a pipeline stage.
    This ensures consistent logging across all pipeline components.
    
    Args:
        stage_name: Name of the pipeline stage (e.g., 'preprocessing', 'classification')
        level: Logging level
    
    Returns:
        Configured logger for the stage
    """
    return configure_logger(
        name=f"pipeline.{stage_name}",
        level=level,
        stage_name=stage_name,
        log_to_file=True,
        log_to_console=True
    )

def log_exception(logger: logging.Logger, message: str, exc: Exception, level: int = logging.ERROR):
    """
    Log an exception with full traceback context.
    
    Args:
        logger: Logger instance to use
        message: Error message to log
        exc: Exception instance
        level: Logging level for the error
    """
    import traceback
    error_details = {
        "message": message,
        "exception_type": type(exc).__name__,
        "exception_message": str(exc),
        "traceback": traceback.format_exc()
    }
    logger.log(level, f"{message} | {json.dumps(error_details)}")

def log_stage_start(logger: logging.Logger, stage_name: str, config: Optional[Dict[str, Any]] = None):
    """Log the start of a pipeline stage."""
    logger.info(f"=" * 60)
    logger.info(f"STARTING STAGE: {stage_name.upper()}")
    if config:
        logger.info(f"Configuration: {json.dumps(config, indent=2, default=str)}")
    logger.info(f"=" * 60)

def log_stage_end(logger: logging.Logger, stage_name: str, success: bool = True, metrics: Optional[Dict[str, Any]] = None):
    """Log the end of a pipeline stage."""
    logger.info(f"=" * 60)
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"ENDING STAGE: {stage_name.upper()} - {status}")
    if metrics:
        logger.info(f"Metrics: {json.dumps(metrics, indent=2, default=str)}")
    logger.info(f"=" * 60)

def log_warning_count(logger: logging.Logger, stage_name: str, warning_count: int):
    """Log a summary of warnings encountered during a stage."""
    if warning_count > 0:
        logger.warning(f"Stage {stage_name} completed with {warning_count} warnings.")
    else:
        logger.info(f"Stage {stage_name} completed with no warnings.")

# Pre-configured loggers for common stages
PREPROCESSING_LOGGER = None
FEATURE_EXTRACTION_LOGGER = None
CLASSIFICATION_LOGGER = None
DATASET_LOGGER = None

def init_stage_loggers():
    """Initialize loggers for all major pipeline stages."""
    global PREPROCESSING_LOGGER, FEATURE_EXTRACTION_LOGGER, CLASSIFICATION_LOGGER, DATASET_LOGGER
    
    if PREPROCESSING_LOGGER is None:
        PREPROCESSING_LOGGER = get_pipeline_logger("preprocessing")
        FEATURE_EXTRACTION_LOGGER = get_pipeline_logger("feature_extraction")
        CLASSIFICATION_LOGGER = get_pipeline_logger("classification")
        DATASET_LOGGER = get_pipeline_logger("dataset_verification")

# Initialize stage loggers on module import
init_stage_loggers()
