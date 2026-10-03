"""
Logging configuration for the llmXive pipeline.
Provides JSON-formatted logging with atomic writes and file locking.
"""
import logging
import os
import json
import tempfile
import platform
import threading
from logging.handlers import BaseRotatingHandler
from typing import Any, Dict, Optional
import portalocker

# Thread-local storage for logger instances to ensure thread safety
_thread_local = threading.local()

class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs log records as JSON."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string."""
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "data": {}
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            log_data["data"] = record.extra_data
        
        # Add standard attributes if they exist
        if record.exc_info:
            log_data["data"]["exc_info"] = self.formatException(record.exc_info)
        
        if record.filename:
            log_data["data"]["filename"] = record.filename
        
        if record.lineno:
            log_data["data"]["lineno"] = record.lineno
        
        if record.funcName:
            log_data["data"]["funcName"] = record.funcName
        
        return json.dumps(log_data)

class AtomicFileHandler(logging.FileHandler):
    """
    File handler that performs atomic writes and uses file locking.
    Writes to a temp file first, then renames to the target file.
    Uses portalocker for cross-platform file locking.
    """
    
    def __init__(self, filename: str, mode: str = 'a', encoding: Optional[str] = None, delay: bool = False):
        super().__init__(filename, mode, encoding, delay)
        self._lock = threading.Lock()
        self._portalocker_lock = None
        self._temp_file = None
        
        # Ensure the directory exists
        log_dir = os.path.dirname(filename)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
    
    def emit(self, record: logging.LogRecord) -> None:
        """Emit a record using atomic write and file locking."""
        try:
            with self._lock:
                # Acquire portalocker lock
                if self.stream is None:
                    self.stream = self._open()
                
                # Use portalocker for cross-platform locking
                try:
                    portalocker.lock(self.stream, portalocker.LOCK_EX)
                    
                    # Format the message
                    msg = self.format(record)
                    separator = '\n' if self.stream.tell() > 0 else ''
                    
                    # Write to temp file first
                    temp_fd, temp_path = tempfile.mkstemp(
                        dir=os.path.dirname(self.baseFilename),
                        prefix='.tmp_log_',
                        suffix='.json'
                    )
                    try:
                        with os.fdopen(temp_fd, 'w', encoding=self.encoding) as temp_file:
                            temp_file.write(separator + msg + '\n')
                            temp_file.flush()
                            os.fsync(temp_file.fileno())
                        
                        # Atomic rename
                        os.replace(temp_path, self.baseFilename)
                        
                    except Exception:
                        # Clean up temp file on error
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
                        raise
                    
                finally:
                    try:
                        portalocker.unlock(self.stream)
                    except Exception:
                        pass
                        
        except Exception:
            self.handleError(record)

def setup_pipeline_logger(
    name: str = "pipeline",
    log_file: str = "results/pipeline.log",
    level: int = logging.INFO
) -> logging.Logger:
    """
    Setup and return a logger configured for the pipeline.
    
    Args:
        name: Logger name
        log_file: Path to the log file (relative to project root)
        level: Logging level
    
    Returns:
        Configured logger instance
    """
    # Get or create logger
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Create absolute path for log file
    abs_log_file = os.path.abspath(log_file)
    
    # Create handler with atomic writes and locking
    handler = AtomicFileHandler(abs_log_file)
    handler.setFormatter(JSONFormatter())
    
    # Add handler to logger
    logger.addHandler(handler)
    
    # Prevent propagation to root logger to avoid duplicate logs
    logger.propagate = False
    
    return logger

def log_exclusion(
    logger: logging.Logger,
    dataset_id: str,
    reason: str,
    details: str
) -> None:
    """Log a dataset exclusion event."""
    extra = {
        "event": "exclusion",
        "dataset_id": dataset_id,
        "reason": reason,
        "details": details
    }
    logger.info("Dataset excluded", extra={"extra_data": extra})

def log_imputation_rate(
    logger: logging.Logger,
    dataset_id: str,
    variable: str,
    method: str,
    rate: float
) -> None:
    """Log an imputation event."""
    extra = {
        "event": "imputation",
        "dataset_id": dataset_id,
        "variable": variable,
        "method": method,
        "rate": rate
    }
    logger.info("Imputation performed", extra={"extra_data": extra})

def log_transformation_intervention(
    logger: logging.Logger,
    dataset_id: str,
    transformation: str,
    intervention: str,
    reason: str
) -> None:
    """Log a transformation intervention."""
    extra = {
        "event": "transformation_intervention",
        "dataset_id": dataset_id,
        "transformation": transformation,
        "intervention": intervention,
        "reason": reason
    }
    logger.info("Transformation intervention", extra={"extra_data": extra})