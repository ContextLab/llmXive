"""
Logging infrastructure for the phylogeny-metabolite pipeline.

Provides structured JSON logging for pipeline steps, dual handlers
(file and console), and consistent log formatting across the project.
"""
import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from logging.handlers import RotatingFileHandler
import traceback

# Global logger registry to prevent duplicate handlers
_loggers_initialized: Dict[str, bool] = {}

# Default configuration values
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_DIR = Path("output/logs")
DEFAULT_LOG_FILE = "pipeline.log"
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10MB
DEFAULT_BACKUP_COUNT = 5

class StructuredJsonFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs as structured JSON.
    
    Includes timestamp, level, logger name, message, and optional
    contextual data (species_id, locus, step, etc.).
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_entry["context"] = record.extra_data
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info)
            }
        
        return json.dumps(log_entry, default=str)

class ConsoleFormatter(logging.Formatter):
    """
    Human-readable formatter for console output with colors.
    """
    
    COLORS = {
        logging.DEBUG: "\033[36m",    # Cyan
        logging.INFO: "\033[32m",     # Green
        logging.WARNING: "\033[33m",  # Yellow
        logging.ERROR: "\033[31m",    # Red
        logging.CRITICAL: "\033[35m", # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, self.RESET)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_line = f"{color}[{timestamp}] {record.levelname:8} {record.name}: {record.getMessage()}{self.RESET}"
        
        if hasattr(record, "extra_data"):
            ctx = record.extra_data
            ctx_str = ", ".join(f"{k}={v}" for k, v in ctx.items())
            log_line += f" ({ctx_str})"
        
        return log_line

def setup_logging(
    log_level: int = DEFAULT_LOG_LEVEL,
    log_dir: Optional[Path] = None,
    log_file: Optional[str] = None,
    console_output: bool = True,
    json_format: bool = False,
    project_name: str = "PROJ-408"
) -> logging.Logger:
    """
    Initialize and configure the logging infrastructure.
    
    Args:
        log_level: Minimum log level (e.g., logging.INFO, logging.DEBUG).
        log_dir: Directory for log files. Defaults to output/logs.
        log_file: Log filename. Defaults to pipeline.log.
        console_output: Whether to enable console logging.
        json_format: Whether to use JSON formatting (structured logs).
        project_name: Name of the project for logger identification.
    
    Returns:
        The root logger configured for the project.
    
    Raises:
        ValueError: If log_dir cannot be created.
    """
    # Resolve paths
    if log_dir is None:
        log_dir = DEFAULT_LOG_DIR
    if log_file is None:
        log_file = DEFAULT_LOG_FILE
    
    log_path = Path(log_dir)
    
    # Ensure log directory exists
    try:
        log_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise ValueError(f"Failed to create log directory {log_path}: {e}")
    
    # Get or create the root logger
    logger = logging.getLogger(project_name)
    logger.setLevel(log_level)
    
    # Prevent duplicate handler setup
    if logger.handlers or _loggers_initialized.get(project_name):
        return logger
    
    logger.handlers.clear()
    _loggers_initialized[project_name] = True
    
    # Determine formatter
    if json_format:
        formatter: logging.Formatter = StructuredJsonFormatter()
    else:
        formatter = ConsoleFormatter()
    
    # File handler with rotation
    log_file_path = log_path / log_file
    try:
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=DEFAULT_MAX_BYTES,
            backupCount=DEFAULT_BACKUP_COUNT,
            encoding="utf-8"
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except (OSError, PermissionError) as e:
        # Fallback to basic file handler if rotation fails
        try:
            file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as fallback_error:
            logger.warning(f"Failed to initialize file logging: {fallback_error}")
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger

def get_logger(name: str = "PROJ-408") -> logging.Logger:
    """
    Retrieve a logger instance.
    
    Args:
        name: Logger name (defaults to project name).
    
    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)

def log_pipeline_step(
    step_name: str,
    status: str,
    details: Optional[Dict[str, Any]] = None,
    duration: Optional[float] = None,
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Log a structured pipeline step event.
    
    Args:
        step_name: Name of the pipeline step.
        status: Status of the step (e.g., 'START', 'COMPLETE', 'FAIL').
        details: Optional contextual data (species_id, locus, file paths, etc.).
        duration: Optional duration in seconds.
        logger: Logger instance to use. If None, uses default.
    """
    if logger is None:
        logger = get_logger()
    
    extra_data = {
        "step": step_name,
        "status": status,
    }
    
    if duration is not None:
        extra_data["duration_seconds"] = round(duration, 3)
    
    if details:
        extra_data.update(details)
    
    # Set extra attribute on record for formatter to access
    record = logger.makeRecord(
        logger.name,
        logging.INFO if status == "COMPLETE" else logging.ERROR if status == "FAIL" else logging.INFO,
        "", 0, "", (), None
    )
    record.extra_data = extra_data
    
    if status == "START":
        logger.info(f"Starting step: {step_name}", extra={"extra_data": extra_data})
    elif status == "COMPLETE":
        logger.info(f"Completed step: {step_name}", extra={"extra_data": extra_data})
    elif status == "FAIL":
        logger.error(f"Failed step: {step_name}", extra={"extra_data": extra_data})
    else:
        logger.info(f"Step event: {step_name} - {status}", extra={"extra_data": extra_data})

def log_data_fetch(
    species_id: str,
    locus: str,
    status: str,
    file_path: Optional[str] = None,
    bytes_read: Optional[int] = None,
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Log a data fetch event with species and locus context.
    
    Args:
        species_id: Identifier for the species.
        locus: Genomic locus (e.g., '18S', 'rbcL').
        status: Fetch status (e.g., 'SUCCESS', 'MISSING', 'ERROR').
        file_path: Path to the downloaded file.
        bytes_read: Number of bytes read.
        logger: Logger instance to use.
    """
    if logger is None:
        logger = get_logger()
    
    details = {
        "species_id": species_id,
        "locus": locus,
        "status": status,
    }
    
    if file_path:
        details["file_path"] = file_path
    if bytes_read:
        details["bytes"] = bytes_read
    
    if status == "SUCCESS":
        logger.info(f"Fetched {locus} for {species_id}", extra={"extra_data": details})
    elif status == "MISSING":
        logger.warning(f"Missing {locus} for {species_id}", extra={"extra_data": details})
    elif status == "ERROR":
        logger.error(f"Error fetching {locus} for {species_id}", extra={"extra_data": details})
    else:
        logger.info(f"Fetch event: {species_id}/{locus} - {status}", extra={"extra_data": details})

def log_error_with_traceback(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Log an exception with full traceback and optional context.
    
    Args:
        error: The exception to log.
        context: Optional contextual data.
        logger: Logger instance to use.
    """
    if logger is None:
        logger = get_logger()
    
    extra_data = {"error_type": type(error).__name__, "error_message": str(error)}
    if context:
        extra_data.update(context)
    
    logger.exception(
        "An error occurred",
        extra={"extra_data": extra_data}
    )

# Convenience function to initialize logging with common defaults
def init_pipeline_logging(
    debug: bool = False,
    json_logs: bool = False
) -> logging.Logger:
    """
    Initialize logging with project defaults.
    
    Args:
        debug: If True, set level to DEBUG.
        json_logs: If True, use JSON formatting.
    
    Returns:
        Configured root logger.
    """
    level = logging.DEBUG if debug else logging.INFO
    return setup_logging(
        log_level=level,
        json_format=json_logs,
        project_name="PROJ-408"
    )