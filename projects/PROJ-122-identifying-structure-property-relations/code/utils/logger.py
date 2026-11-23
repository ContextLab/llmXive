"""
Base logging infrastructure for the llmXive automated science pipeline.

Provides centralized logging configuration, pipeline-specific loggers,
and artifact checksum logging capabilities.
"""
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Union
from datetime import datetime
import json
import hashlib

# Constants
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_DIR = Path("state/logs")
LOG_FILE_PREFIX = "pipeline_"
LOG_EXTENSION = ".log"

# Global logger instance cache
_loggers: dict = {}
_logging_configured = False


def _ensure_log_dir() -> Path:
    """Ensure the log directory exists."""
    if not LOG_DIR.exists():
        LOG_DIR.mkdir(parents=True, exist_ok=True)
    return LOG_DIR


def _get_log_file_path() -> Path:
    """Generate a unique log file path based on current timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return _ensure_log_dir() / f"{LOG_FILE_PREFIX}{timestamp}{LOG_EXTENSION}"


def setup_logging(
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_console: bool = True,
    log_file_path: Optional[Union[str, Path]] = None,
    format_str: Optional[str] = None,
    date_format: Optional[str] = None
) -> None:
    """
    Configure the root logging infrastructure.
    
    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO)
        log_to_file: Whether to write logs to a file
        log_to_console: Whether to print logs to stdout
        log_file_path: Optional custom path for the log file
        format_str: Optional custom log format string
        date_format: Optional custom date format string
    
    Raises:
        ValueError: If both log_to_file and log_to_console are False
    """
    global _logging_configured
    
    if not log_to_file and not log_to_console:
        raise ValueError("At least one of log_to_file or log_to_console must be True")
    
    if _logging_configured:
        # If already configured, just update the level
        logging.getLogger().setLevel(level)
        return
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Custom format
    fmt = format_str or DEFAULT_LOG_FORMAT
    date_fmt = date_format or DEFAULT_DATE_FORMAT
    formatter = logging.Formatter(fmt, date_fmt)
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if log_to_file:
        file_path = Path(log_file_path) if log_file_path else _get_log_file_path()
        file_handler = logging.FileHandler(file_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # Log the file path to console for easy reference
        if log_to_console:
            root_logger.info(f"Logs being written to: {file_path.absolute()}")
    
    _logging_configured = True
    root_logger.info("Logging infrastructure initialized successfully")


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance, optionally named for a specific module/component.
    
    Args:
        name: Optional name for the logger (e.g., 'ingest', 'features', 'train')
    
    Returns:
        A configured logging.Logger instance
    """
    if name is None:
        name = "pipeline"
    
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
    
    # Ensure logging is configured if not already
    if not _logging_configured:
        setup_logging()
    
    _loggers[name] = logger
    return logger


def log_artifact_checksum(
    artifact_path: Union[str, Path],
    logger: Optional[logging.Logger] = None,
    algorithm: str = "sha256"
) -> str:
    """
    Compute and log the checksum of an artifact file.
    
    Args:
        artifact_path: Path to the artifact file
        logger: Optional logger instance (uses default if None)
        algorithm: Hash algorithm to use (default: sha256)
    
    Returns:
        The computed checksum string (hex digest)
    
    Raises:
        FileNotFoundError: If the artifact file does not exist
        ValueError: If the algorithm is not supported
    """
    path = Path(artifact_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Artifact not found: {path}")
    
    if logger is None:
        logger = get_logger()
    
    # Compute checksum
    hasher = hashlib.new(algorithm)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    
    checksum = hasher.hexdigest()
    
    # Log the checksum
    logger.info(
        f"Artifact checksum computed: path={path}, algorithm={algorithm}, "
        f"checksum={checksum}"
    )
    
    return checksum


class PipelineLogger:
    """
    Context-aware logger for pipeline stages with artifact tracking.
    
    Provides methods for logging stage start/end, artifacts, and metrics
    in a structured format.
    """
    
    def __init__(self, stage_name: str, parent_logger: Optional[logging.Logger] = None):
        """
        Initialize the pipeline logger for a specific stage.
        
        Args:
            stage_name: Name of the pipeline stage (e.g., 'ingest', 'features')
            parent_logger: Optional parent logger instance
        """
        self.stage_name = stage_name
        self.logger = parent_logger or get_logger(f"pipeline.{stage_name}")
        self._start_time: Optional[datetime] = None
        self._artifacts_logged: list = []
    
    def start(self, message: Optional[str] = None) -> None:
        """Log the start of a pipeline stage."""
        self._start_time = datetime.now()
        msg = message or f"Starting stage: {self.stage_name}"
        self.logger.info(f"[{self.stage_name.upper()}] {msg}")
    
    def end(self, message: Optional[str] = None, success: bool = True) -> None:
        """Log the end of a pipeline stage."""
        if self._start_time is None:
            self.logger.warning(f"[{self.stage_name.upper()}] End called without start")
            return
        
        duration = (datetime.now() - self._start_time).total_seconds()
        status = "SUCCESS" if success else "FAILED"
        msg = message or f"Stage {self.stage_name} completed in {duration:.2f}s"
        self.logger.info(f"[{self.stage_name.upper()}] {status}: {msg}")
    
    def log_artifact(
        self,
        name: str,
        path: Union[str, Path],
        checksum: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> None:
        """
        Log an artifact produced by this stage.
        
        Args:
            name: Human-readable name for the artifact
            path: Path to the artifact file
            checksum: Optional pre-computed checksum
            metadata: Optional additional metadata dict
        """
        path = Path(path)
        if not path.exists():
            self.logger.warning(f"Artifact logged but not found: {path}")
        
        artifact_info = {
            "name": name,
            "path": str(path),
            "timestamp": datetime.now().isoformat(),
            "stage": self.stage_name
        }
        
        if checksum:
            artifact_info["checksum"] = checksum
        elif path.exists():
            try:
                artifact_info["checksum"] = log_artifact_checksum(path, self.logger)
            except Exception as e:
                self.logger.warning(f"Could not compute checksum for {path}: {e}")
        
        if metadata:
            artifact_info["metadata"] = metadata
        
        self._artifacts_logged.append(artifact_info)
        self.logger.info(f"[{self.stage_name.upper()}] Artifact logged: {name} -> {path}")
    
    def log_metric(self, name: str, value: Union[int, float, str], unit: Optional[str] = None) -> None:
        """
        Log a performance metric.
        
        Args:
            name: Name of the metric
            value: Value of the metric
            unit: Optional unit of measurement
        """
        msg = f"{name}={value}" + (f" ({unit})" if unit else "")
        self.logger.info(f"[{self.stage_name.upper()}] Metric: {msg}")
    
    def log_error(self, error: Exception, context: Optional[str] = None) -> None:
        """
        Log an error with optional context.
        
        Args:
            error: The exception that occurred
            context: Optional context description
        """
        msg = context if context else str(error)
        self.logger.error(f"[{self.stage_name.upper()}] Error: {msg}", exc_info=True)
    
    def get_artifact_summary(self) -> dict:
        """
        Get a summary of all artifacts logged in this stage.
        
        Returns:
            Dict containing list of artifact info dicts
        """
        return {
            "stage": self.stage_name,
            "artifact_count": len(self._artifacts_logged),
            "artifacts": self._artifacts_logged
        }
    
    def __enter__(self) -> "PipelineLogger":
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        success = exc_type is None
        self.end(success=success)
        if exc_val:
            self.log_error(exc_val)