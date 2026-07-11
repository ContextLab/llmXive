import logging
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Constants
_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_LOG_LEVEL = logging.INFO

# Cache for logger instances to avoid re-initialization
_logger_cache: Dict[str, logging.Logger] = {}

def get_pipeline_logger(name: str = "halo_pipeline") -> logging.Logger:
    """
    Get or create a configured logger for the pipeline.
    
    Args:
        name: The name of the logger (usually the module name).
        
    Returns:
        A configured logging.Logger instance.
    """
    if name in _logger_cache:
        return _logger_cache[name]

    logger = logging.getLogger(name)
    logger.setLevel(_LOG_LEVEL)

    # Avoid adding handlers multiple times if called repeatedly
    if not logger.handlers:
        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(_LOG_LEVEL)
        console_formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # File Handler (Optional, based on environment)
        # We try to log to a file in the project root if possible
        try:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"pipeline_{timestamp}.log"
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(_LOG_LEVEL)
            file_handler.setFormatter(console_formatter)
            logger.addHandler(file_handler)
            
            # Store the log file path in the logger for later retrieval
            logger.log_file_path = str(log_file)
        except Exception:
            # If we can't write to disk, just use console
            pass

    _logger_cache[name] = logger
    return logger

def get_log_file_path(logger: logging.Logger) -> Optional[str]:
    """
    Retrieve the file path of the log file attached to the logger, if any.
    
    Args:
        logger: The logger instance.
        
    Returns:
        The path to the log file or None if logging to console only.
    """
    return getattr(logger, 'log_file_path', None)

def log_pipeline_start(logger: logging.Logger, config: Optional[Dict[str, Any]] = None) -> None:
    """
    Log the start of the pipeline execution.
    
    Args:
        logger: The logger instance.
        config: Optional configuration dictionary to log.
    """
    logger.info("=" * 60)
    logger.info("PIPELINE START")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    if config:
        logger.info(f"Configuration: {config}")
    logger.info("=" * 60)

def log_pipeline_end(logger: logging.Logger, success: bool = True, duration: Optional[float] = None) -> None:
    """
    Log the end of the pipeline execution.
    
    Args:
        logger: The logger instance.
        success: Whether the pipeline completed successfully.
        duration: Optional duration of the run in seconds.
    """
    logger.info("=" * 60)
    if success:
        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
    else:
        logger.error("PIPELINE FAILED")
    if duration is not None:
        logger.info(f"Total Duration: {duration:.2f} seconds")
    logger.info("=" * 60)

def log_error(logger: logging.Logger, message: str, exception: Optional[Exception] = None) -> None:
    """
    Log an error message, optionally with exception details.
    
    Args:
        logger: The logger instance.
        message: The error message.
        exception: Optional exception object to include in the log.
    """
    if exception:
        logger.error(f"{message}: {str(exception)}", exc_info=True)
    else:
        logger.error(message)

def log_metric(logger: logging.Logger, name: str, value: Any, stage: Optional[str] = None) -> None:
    """
    Log a metric value at a specific stage.
    
    Args:
        logger: The logger instance.
        name: The name of the metric.
        value: The value of the metric.
        stage: Optional stage name (e.g., "ingestion", "processing").
    """
    stage_prefix = f"[{stage}] " if stage else ""
    logger.info(f"{stage_prefix}Metric: {name} = {value}")

def log_chunk_info(logger: logging.Logger, chunk_id: int, total_chunks: int, 
                   records_processed: int, elapsed_seconds: float) -> None:
    """
    Log progress for a specific chunk processing step.
    
    Args:
        logger: The logger instance.
        chunk_id: Current chunk ID.
        total_chunks: Total number of chunks.
        records_processed: Number of records processed in this chunk.
        elapsed_seconds: Time taken for this chunk.
    """
    progress = (chunk_id / total_chunks) * 100 if total_chunks > 0 else 0
    logger.info(f"Chunk {chunk_id}/{total_chunks} ({progress:.1f}%): "
                f"Processed {records_processed} records in {elapsed_seconds:.2f}s")
