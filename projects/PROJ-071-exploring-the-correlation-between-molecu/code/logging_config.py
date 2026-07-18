import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
import traceback

# Define custom exceptions for pipeline stages
class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass

class DataIngestionError(PipelineError):
    """Error during data ingestion."""
    pass

class DescriptorCalculationError(PipelineError):
    """Error during descriptor calculation."""
    pass

class AnalysisError(PipelineError):
    """Error during analysis."""
    pass

class VisualizationError(PipelineError):
    """Error during visualization."""
    pass

class ConfigurationError(PipelineError):
    """Error during configuration."""
    pass

# Global logger instance
_logger: Optional[logging.Logger] = None

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = "data/pipeline.log") -> None:
    """
    Configures the logging infrastructure for the pipeline.
    Sets up console and file handlers with a consistent format.
    """
    global _logger
    
    if _logger is not None:
        return # Already configured

    _logger = logging.getLogger("llmXive_pipeline")
    _logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers
    _logger.handlers = []

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    _logger.addHandler(console_handler)

    # File Handler (if log_file is provided)
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        _logger.addHandler(file_handler)

    _logger.info("Logging infrastructure configured.")

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieves the configured logger or a child logger.
    """
    if _logger is None:
        setup_logging()
    
    if name:
        return _logger.getChild(name)
    return _logger

def log_error(message: str, error: Optional[Exception] = None, level: str = "ERROR") -> None:
    """
    Logs an error message with optional exception details.
    """
    logger = get_logger()
    log_method = getattr(logger, level.lower(), logger.error)
    
    if error:
        log_method(f"{message}: {str(error)}")
        log_method(traceback.format_exc())
    else:
        log_method(message)

def handle_pipeline_exception(exception: Exception, stage: str) -> None:
    """
    Handles a pipeline exception by logging it and raising a specific pipeline error.
    """
    logger = get_logger()
    logger.error(f"Pipeline failed at stage '{stage}' with exception: {exception}")
    logger.error(traceback.format_exc())
    
    # Map to specific exception if possible
    if isinstance(exception, DataIngestionError):
        raise exception
    elif isinstance(exception, DescriptorCalculationError):
        raise exception
    elif isinstance(exception, AnalysisError):
        raise exception
    elif isinstance(exception, VisualizationError):
        raise exception
    else:
        raise PipelineError(f"Unhandled pipeline error at {stage}: {exception}") from exception

def log_pipeline_start(stage: str) -> None:
    """Logs the start of a pipeline stage."""
    get_logger().info(f"--- Starting Stage: {stage} ---")

def log_pipeline_complete(stage: str) -> None:
    """Logs the completion of a pipeline stage."""
    get_logger().info(f"--- Completed Stage: {stage} ---")

def log_pipeline_failure(stage: str, reason: str) -> None:
    """Logs the failure of a pipeline stage."""
    get_logger().error(f"--- Failed Stage: {stage} --- Reason: {reason}")