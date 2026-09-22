import logging
import os
import sys
from pathlib import Path
from typing import Optional
import traceback

# Configure root logger
def configure_root_logger(log_level: int = logging.INFO, log_file: Optional[str] = None) -> None:
    """
    Configure the root logger with console and optional file handlers.
    
    Args:
        log_level: Logging level (default: INFO).
        log_file: Optional path to log file.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(console_formatter)
        root_logger.addHandler(file_handler)

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name. Defaults to module name if None.
    
    Returns:
        Configured logger instance.
    """
    if name is None:
        frame = sys._getframe(1)
        name = frame.f_globals.get('__name__', 'root')
    return logging.getLogger(name)

class DataFetchLogger:
    """
    Specialized logger for data fetching operations.
    
    Ensures that data fetch failures are logged with high visibility
    and that the "FAIL LOUDLY" pattern is followed.
    """
    
    def __init__(self, source_name: str):
        """
        Initialize the data fetch logger.
        
        Args:
            source_name: Name of the data source.
        """
        self.logger = get_logger(f"data_fetch.{source_name}")
        self.source_name = source_name
    
    def fetch_start(self) -> None:
        """Log the start of a data fetch operation."""
        self.logger.info(f"Starting data fetch for {self.source_name}")
    
    def fetch_success(self, size_info: Optional[str] = None) -> None:
        """
        Log successful data fetch.
        
        Args:
            size_info: Optional information about data size.
        """
        msg = f"Successfully fetched data for {self.source_name}"
        if size_info:
            msg += f" ({size_info})"
        self.logger.info(msg)
    
    def fetch_retry(self, attempt: int, max_attempts: int, error: Exception) -> None:
        """
        Log a retry attempt.
        
        Args:
            attempt: Current attempt number.
            max_attempts: Maximum number of attempts.
            error: The exception that triggered the retry.
        """
        self.logger.warning(
            f"Attempt {attempt}/{max_attempts} failed for {self.source_name}: {error}. "
            f"Retrying..."
        )
    
    def fetch_failure(self, error: Exception) -> None:
        """
        Log a final fetch failure.
        
        This method logs the failure with maximum severity and ensures
        the error is visible.
        
        Args:
            error: The exception that caused the failure.
        """
        self.logger.critical(
            f"CRITICAL: Failed to fetch data from {self.source_name} after all retries. "
            f"Error: {error}. No synthetic fallback will be attempted."
        )
        self.logger.debug(traceback.format_exc())
    
    def fail_loudly(self, message: str, error: Optional[Exception] = None) -> None:
        """
        Fail loudly with a clear error message.
        
        Args:
            message: The error message.
            error: Optional underlying exception.
        """
        self.logger.critical(f"FAIL LOUDLY: {message}")
        if error:
            self.logger.debug(traceback.format_exc())
            raise RuntimeError(message) from error
        raise RuntimeError(message)

def configure_data_fetch_logger(source_name: str) -> DataFetchLogger:
    """
    Configure and return a data fetch logger for a specific source.
    
    Args:
        source_name: Name of the data source.
    
    Returns:
        Configured DataFetchLogger instance.
    """
    return DataFetchLogger(source_name)

def fail_loudly(message: str, logger_name: Optional[str] = None, error: Optional[Exception] = None) -> None:
    """
    Fail loudly with a clear error message.
    
    This function logs a critical error and raises an exception to ensure
    the failure is immediately visible and stops execution.
    
    Args:
        message: The error message.
        logger_name: Optional logger name. Defaults to 'fail_loudly'.
        error: Optional underlying exception.
    
    Raises:
        RuntimeError: Always raises this exception.
    """
    logger = get_logger(logger_name or 'fail_loudly')
    logger.critical(f"FAIL LOUDLY: {message}")
    if error:
        logger.debug(traceback.format_exc())
        raise RuntimeError(message) from error
    raise RuntimeError(message)

def log_simulation_error(error: Exception, clip_id: str, context: str = "") -> None:
    """
    Log a physics simulation error.
    
    Args:
        error: The exception that occurred.
        clip_id: ID of the clip being processed.
        context: Additional context about the error.
    """
    logger = get_logger('simulation')
    logger.error(f"Simulation failed for clip {clip_id}: {error}. Context: {context}")
    logger.debug(traceback.format_exc())

def log_excluded_sample(clip_id: str, reason: str, confidence_score: float) -> None:
    """
    Log an excluded sample.
    
    Args:
        clip_id: ID of the excluded clip.
        reason: Reason for exclusion.
        confidence_score: Confidence score that led to exclusion.
    """
    logger = get_logger('simulation')
    logger.info(f"Excluding clip {clip_id}: {reason} (confidence: {confidence_score:.3f})")

def log_simulation_batch_stats(total: int, excluded: int, failed: int) -> None:
    """
    Log statistics for a batch of simulation results.
    
    Args:
        total: Total number of samples processed.
        excluded: Number of samples excluded due to low confidence.
        failed: Number of samples that failed simulation.
    """
    logger = get_logger('simulation')
    logger.info(f"Simulation batch stats: total={total}, excluded={excluded}, failed={failed}")
    if total > 0:
        logger.info(f"  Success rate: {(total - excluded - failed) / total * 100:.1f}%")

def log_feature_extraction_progress(clip_id: str, frame_idx: int, total_frames: int, memory_usage_mb: float) -> None:
    """
    Log feature extraction progress.
    
    Args:
        clip_id: ID of the clip being processed.
        frame_idx: Current frame index.
        total_frames: Total number of frames.
        memory_usage_mb: Current memory usage in MB.
    """
    logger = get_logger('feature_extraction')
    progress = (frame_idx + 1) / total_frames * 100
    logger.debug(
        f"Extracting features for {clip_id}: {frame_idx + 1}/{total_frames} frames "
        f"({progress:.1f}%), Memory: {memory_usage_mb:.1f}MB"
    )

def log_label_generation_progress(clip_id: str, step: str, status: str) -> None:
    """
    Log label generation progress.
    
    Args:
        clip_id: ID of the clip being processed.
        step: Current step in the process.
        status: Status of the step (e.g., 'started', 'completed', 'failed').
    """
    logger = get_logger('label_generation')
    logger.info(f"Label generation for {clip_id}: {step} - {status}")

def log_prior_audit_result(audit_passed: bool, correlation: float, threshold: float) -> None:
    """
    Log the result of a prior audit.
    
    Args:
        audit_passed: Whether the audit passed.
        correlation: The calculated correlation value.
        threshold: The threshold used for the audit.
    """
    logger = get_logger('prior_audit')
    status = "PASSED" if audit_passed else "FAILED"
    logger.info(
        f"Prior Audit {status}: correlation={correlation:.4f}, threshold={threshold:.4f}. "
        f"Shared priors detected: {not audit_passed}"
    )
