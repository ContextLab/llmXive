import logging
import sys
from pathlib import Path
from typing import Optional

# Custom formatter to include process info and precise timestamps
class ResearchFormatter(logging.Formatter):
    """Custom formatter for scientific pipeline logs."""
    def format(self, record):
        # Add progress bar indicator if present in extra
        if hasattr(record, 'progress'):
            record.msg = f"[{record.progress}] {record.msg}"
        return super().format(record)

def setup_logging(
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
    console: bool = True
) -> logging.Logger:
    """
    Configure the root logger for the research pipeline.
    
    Args:
        log_file: Optional path to write logs to.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        console: Whether to log to stdout/stderr.
    
    Returns:
        The root logger instance.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates in repeated calls
    root_logger.handlers.clear()
    
    # Formatter with timestamp, level, module, and message
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"
    
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_formatter = ResearchFormatter(fmt=fmt, datefmt=date_fmt)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(level)
        file_formatter = ResearchFormatter(fmt=fmt, datefmt=date_fmt)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger for a specific module/component.
    
    Args:
        name: The name of the logger (usually __name__).
    
    Returns:
        A configured logger instance.
    """
    return logging.getLogger(name)

def log_download_progress(
    logger: logging.Logger,
    current: int,
    total: int,
    operation: str = "Download"
) -> None:
    """
    Log download progress with a percentage indicator.
    
    Args:
        logger: The logger instance.
        current: Current number of items processed.
        total: Total number of items.
        operation: Name of the operation (e.g., "Download", "Extract").
    """
    if total > 0:
        percent = (current / total) * 100
        logger.info(
            "%s Progress: %d/%d (%.2f%%)",
            operation, current, total, percent,
            extra={'progress': f"{percent:.1f}%"}
        )
    else:
        logger.info("%s: Processing item %d...", operation, current)

def log_descriptor_stats(
    logger: logging.Logger,
    property_name: str,
    total_rows: int,
    valid_rows: int,
    missing_features: int = 0
) -> None:
    """
    Log statistics for descriptor generation.
    
    Args:
        logger: The logger instance.
        property_name: Name of the material property being processed.
        total_rows: Total number of entries attempted.
        valid_rows: Number of entries with successful descriptor generation.
        missing_features: Number of entries missing required composition data.
    """
    success_rate = (valid_rows / total_rows * 100) if total_rows > 0 else 0
    logger.info(
        "Descriptor Stats | Property: %s | Total: %d | Valid: %d | Missing: %d | Success: %.2f%%",
        property_name, total_rows, valid_rows, missing_features, success_rate
    )
    
    if missing_features > 0:
        logger.warning(
            "Property %s: %d entries skipped due to missing composition data.",
            property_name, missing_features
        )

def log_error_summary(
    logger: logging.Logger,
    error_count: int,
    operation: str
) -> None:
    """
    Log a summary of errors encountered during an operation.
    
    Args:
        logger: The logger instance.
        error_count: Number of errors encountered.
        operation: Name of the operation that failed.
    """
    if error_count > 0:
        logger.error(
            "%s completed with %d errors. Check previous logs for details.",
            operation, error_count
        )
    else:
        logger.info("%s completed successfully with no errors.", operation)
