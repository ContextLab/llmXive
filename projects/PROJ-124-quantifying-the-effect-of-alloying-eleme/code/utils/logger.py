"""
Logging utility module for the pipeline.

This module provides centralized logging configuration and error handling
for the entire pipeline.
"""
import logging
import sys
import os
from pathlib import Path
from typing import Optional
from datetime import datetime

class PipelineError(Exception):
    """Custom exception for pipeline-specific errors."""
    pass

_logger: Optional[logging.Logger] = None

def get_logger(name: str = "pipeline") -> logging.Logger:
    """
    Gets or creates a logger with standardized configuration.
    
    Args:
        name: Name of the logger (typically the module name).
        
    Returns:
        Configured logger instance.
    """
    global _logger
    
    if _logger is None:
        _logger = logging.getLogger(name)
        _logger.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        if not _logger.handlers:
            _logger.addHandler(console_handler)
    
    # Return a child logger with the specified name
    return logging.getLogger(name)

def log_pipeline_start(task_id: str, description: str) -> None:
    """
    Logs the start of a pipeline task.
    
    Args:
        task_id: Identifier for the task (e.g., "T012").
        description: Brief description of what the task does.
    """
    logger = get_logger()
    logger.info(f"{'='*60}")
    logger.info(f"Starting Task: {task_id}")
    logger.info(f"Description: {description}")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"{'='*60}")

def log_pipeline_end(task_id: str, success: bool, message: Optional[str] = None) -> None:
    """
    Logs the completion of a pipeline task.
    
    Args:
        task_id: Identifier for the task.
        success: Whether the task completed successfully.
        message: Optional message to include in the log.
    """
    logger = get_logger()
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"{'='*60}")
    logger.info(f"Task {task_id} {status}")
    if message:
        logger.info(f"Message: {message}")
    logger.info(f"{'='*60}")

def handle_pipeline_error(task_id: str, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Handles and logs pipeline errors.
    
    Args:
        task_id: Identifier for the task.
        error: The exception that was raised.
        context: Optional dictionary of contextual information.
    """
    logger = get_logger()
    logger.error(f"Pipeline Error in Task {task_id}: {str(error)}")
    if context:
        logger.error(f"Context: {context}")
    logger.error(f"Traceback: {error.__traceback__}")

def main():
    """Main entry point for standalone execution (for testing)."""
    logger = get_logger("test")
    log_pipeline_start("TEST-001", "Testing logger functionality")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    log_pipeline_end("TEST-001", True, "Logger test completed successfully")

if __name__ == "__main__":
    main()
