"""
Logging configuration for the llmXive pipeline.

Provides a JSON-formatted logger with file locking and atomic writes
to ensure thread-safe and crash-safe logging to results/pipeline.log.
"""
import logging
import os
import json
import fcntl
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs log records as JSON lines.
    Format: {"timestamp": "...", "level": "...", "message": "...", "data": {...}}
    """
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "data": {}
        }
        
        # Attach extra fields if present
        if hasattr(record, 'data') and isinstance(record.data, dict):
            log_entry["data"] = record.data
        
        # Handle exception info if present
        if record.exc_info:
            log_entry["data"]["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)


class AtomicFileHandler(logging.FileHandler):
    """
    File handler that implements atomic writes and file locking.
    
    Writes are performed by writing to a temporary file in the same directory
    and then renaming it to the target log file. This prevents corruption
    if the process crashes during a write.
    """
    def __init__(self, filename: str, mode: str = 'a', encoding: Optional[str] = None, delay: bool = False):
        super().__init__(filename, mode, encoding, delay)
        self.filename = filename
        self.temp_filename = None
        self.temp_file = None
        self.lock_file = None
        
    def _open_temp(self):
        """Open a temporary file in the same directory for atomic write."""
        dir_path = os.path.dirname(os.path.abspath(self.filename))
        self.temp_file = tempfile.NamedTemporaryFile(
            mode='w', 
            dir=dir_path, 
            prefix='.log_tmp_', 
            delete=False, 
            encoding=self.encoding
        )
        self.temp_filename = self.temp_file.name
        
    def acquire_lock(self):
        """Acquire an exclusive lock on the log file."""
        lock_path = f"{self.filename}.lock"
        self.lock_file = open(lock_path, 'w')
        try:
            fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX)
        except Exception:
            self.lock_file.close()
            raise
        
    def release_lock(self):
        """Release the lock on the log file."""
        if self.lock_file:
            try:
                fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
                self.lock_file.close()
            except Exception:
                pass
            finally:
                self.lock_file = None
        
    def emit(self, record: logging.LogRecord):
        """
        Emit a record with atomic write and locking.
        """
        try:
            # Acquire lock
            self.acquire_lock()
            
            # Open temp file
            self._open_temp()
            
            # Format the message
            msg = self.format(record)
            
            # Write to temp file
            self.temp_file.write(msg + '\n')
            self.temp_file.flush()
            os.fsync(self.temp_file.fileno())
            
            # Close temp file
            self.temp_file.close()
            
            # Atomic rename
            os.replace(self.temp_filename, self.filename)
            
            # Clear temp reference
            self.temp_filename = None
            
        except Exception:
            self.handleError(record)
        finally:
            # Cleanup temp file if it still exists
            if self.temp_filename and os.path.exists(self.temp_filename):
                try:
                    os.unlink(self.temp_filename)
                except Exception:
                    pass
                
            # Release lock
            self.release_lock()


def setup_pipeline_logger(
    name: str = "pipeline",
    log_file: str = "results/pipeline.log",
    level: int = logging.INFO,
    console_output: bool = False
) -> logging.Logger:
    """
    Configure and return a logger with JSON formatting, file locking, and atomic writes.
    
    Args:
        name: Logger name
        log_file: Path to the log file (relative to project root)
        level: Logging level
        console_output: Whether to also output to console
        
    Returns:
        Configured logger instance
    """
    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()
    
    # Create file handler with atomic writes
    file_handler = AtomicFileHandler(str(log_path), mode='a', encoding='utf-8')
    file_handler.setFormatter(JSONFormatter())
    file_handler.setLevel(level)
    
    logger.addHandler(file_handler)
    
    # Optional console handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(JSONFormatter())
        console_handler.setLevel(level)
        logger.addHandler(console_handler)
        
    return logger


def log_exclusion(logger: logging.Logger, dataset_id: str, reason: str, details: str) -> None:
    """
    Log a dataset exclusion event.
    
    Args:
        logger: Logger instance
        dataset_id: ID of the excluded dataset
        reason: Reason for exclusion
        details: Additional details
    """
    logger.info(
        "Dataset excluded",
        extra={
            "data": {
                "dataset_id": dataset_id,
                "reason": reason,
                "details": details
            }
        }
    )


def log_imputation_rate(logger: logging.Logger, dataset_id: str, variable: str, rate: float) -> None:
    """
    Log an imputation event.
    
    Args:
        logger: Logger instance
        dataset_id: ID of the dataset
        variable: Variable name that was imputed
        rate: Imputation rate (0.0 to 1.0)
    """
    logger.info(
        "Imputation performed",
        extra={
            "data": {
                "dataset_id": dataset_id,
                "variable": variable,
                "rate": rate
            }
        }
    )


def log_transformation_intervention(logger: logging.Logger, dataset_id: str, transformation: str, reason: str) -> None:
    """
    Log a transformation intervention (e.g., log-shift applied).
    
    Args:
        logger: Logger instance
        dataset_id: ID of the dataset
        transformation: Transformation applied
        reason: Reason for intervention
    """
    logger.info(
        "Transformation intervention",
        extra={
            "data": {
                "dataset_id": dataset_id,
                "transformation": transformation,
                "reason": reason
            }
        }
    )