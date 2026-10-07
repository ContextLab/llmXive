import logging
import os
import json
import tempfile
import platform
import threading
import portalocker
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure the results directory exists at import time or handler initialization
# This satisfies the CRITICAL requirement: "This task MUST ensure the results/ directory exists before writing."
_RESULTS_DIR = Path("results")
_LOCK_FILE = _RESULTS_DIR / ".pipeline.lock"

def _ensure_results_dir():
    """Ensure the results directory exists."""
    _RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    # Create lock file parent if needed (though it's in results/)
    if not _LOCK_FILE.parent.exists():
        _LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)

class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs as JSON lines.
    Format: {"timestamp": "...", "level": "...", "message": "...", "data": {"key": "value"}}
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "data": {}
        }
        
        # Include extra fields if present
        if hasattr(record, 'extra_data') and isinstance(record.extra_data, dict):
            log_data["data"].update(record.extra_data)
        
        # Include exception info if present
        if record.exc_info:
            log_data["data"]["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)

class AtomicFileHandler(logging.FileHandler):
    """
    A logging handler that writes to a file atomically using a temp file + rename.
    Implements file locking using portalocker for cross-platform compatibility.
    Ensures the log directory exists before writing.
    """
    def __init__(self, filename: str, mode: str = 'a', encoding: Optional[str] = None, delay: bool = False):
        # Ensure directory exists immediately upon initialization
        _ensure_results_dir()
        super().__init__(filename, mode, encoding, delay)
        self._lock_file_path = str(_LOCK_FILE)
        self._lock_fd = None
        self._lock = threading.Lock()
    
    def acquire(self) -> None:
        """Acquire the file lock."""
        self._lock.acquire()
        try:
            # Ensure directory exists again in case of race condition
            _ensure_results_dir()
            
            # Open lock file for exclusive locking
            self._lock_fd = open(self._lock_file_path, 'w')
            portalocker.lock(self._lock_fd, portalocker.LOCK_EX | portalocker.LOCK_NB)
        except Exception as e:
            self._lock.release()
            raise RuntimeError(f"Could not acquire file lock: {e}")

    def release(self) -> None:
        """Release the file lock."""
        if self._lock_fd:
            try:
                portalocker.unlock(self._lock_fd)
                self._lock_fd.close()
            except Exception:
                pass
            finally:
                self._lock_fd = None
        self._lock.release()

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a record.
        Writes to a temporary file first, then atomically renames to the target file.
        Uses portalocker for cross-platform locking.
        """
        try:
            self.acquire()
            try:
                # Format the message
                msg = self.format(record)
                stream = self.stream
                
                # Create a temporary file in the same directory for atomic rename
                # This ensures the rename operation is atomic on the same filesystem
                log_dir = os.path.dirname(self.baseFilename)
                if not log_dir:
                    log_dir = "."
                
                # Create temp file in the same directory to ensure atomic rename
                fd, temp_path = tempfile.mkstemp(dir=log_dir, prefix=".tmp_log_", suffix=".json")
                try:
                    with os.fdopen(fd, 'w', encoding=self.encoding) as temp_file:
                        temp_file.write(msg + self.terminator)
                        temp_file.flush()
                        os.fsync(temp_file.fileno())
                    
                    # Atomic rename
                    os.replace(temp_path, self.baseFilename)
                except Exception:
                    # Clean up temp file if something goes wrong
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                    raise
            finally:
                self.release()
        except Exception:
            self.handleError(record)

def setup_pipeline_logger(
    name: str = "pipeline",
    log_file: str = "results/pipeline.log",
    level: int = logging.INFO
) -> logging.Logger:
    """
    Configure and return a logger that writes JSON-formatted logs to the specified file.
    
    Args:
        name: Logger name
        log_file: Path to the log file (relative to project root)
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    # Create handler
    handler = AtomicFileHandler(log_file)
    handler.setFormatter(JSONFormatter())
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger

def get_logger(name: str = "pipeline") -> logging.Logger:
    """
    Get an existing logger or create a new one with default configuration.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_pipeline_logger(name)
    return logger

def log_exclusion(logger: logging.Logger, dataset_id: str, reason: str, details: str) -> None:
    """Log a dataset exclusion event."""
    logger.info(
        "Dataset excluded",
        extra={
            'extra_data': {
                'event': 'exclusion',
                'dataset_id': dataset_id,
                'reason': reason,
                'details': details
            }
        }
    )

def log_imputation_rate(logger: logging.Logger, dataset_id: str, variable: str, rate: float) -> None:
    """Log an imputation rate event."""
    logger.info(
        "Imputation rate recorded",
        extra={
            'extra_data': {
                'event': 'imputation',
                'dataset_id': dataset_id,
                'variable': variable,
                'rate': rate
            }
        }
    )

def log_transformation_intervention(
    logger: logging.Logger, 
    dataset_id: str, 
    transformation: str, 
    reason: str,
    details: Optional[str] = None
) -> None:
    """Log a transformation intervention event."""
    extra_data = {
        'event': 'transformation_intervention',
        'dataset_id': dataset_id,
        'transformation': transformation,
        'reason': reason
    }
    if details:
        extra_data['details'] = details
    
    logger.warning(
        "Transformation intervention applied",
        extra={'extra_data': extra_data}
    )