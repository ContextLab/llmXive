"""
Logging infrastructure setup for llmXive pipeline.
Provides centralized logging configuration with support for CI and Research modes.
"""
import logging
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Global logger instance to avoid re-initialization
_project_logger: Optional[logging.Logger] = None
_logger_config: Dict[str, Any] = {}

class LlmXiveFormatter(logging.Formatter):
    """Custom formatter that includes mode (CI/Research) in the log message."""
    
    def format(self, record: logging.LogRecord) -> str:
        # Inject mode info if available in extra
        mode = getattr(record, 'mode', 'Unknown')
        original_msg = record.getMessage()
        record.msg = f"[{mode}] {original_msg}"
        return super().format(record)

def get_logger(name: str, log_file: Optional[str] = None, mode: Optional[str] = None) -> logging.Logger:
    """
    Configure and return a logger instance.
    
    Args:
        name: Logger name (usually __name__ of the calling module)
        log_file: Optional path to log file. If None, only console output is used.
        mode: Optional mode string (e.g., 'CI', 'Research') to inject into logs.
    
    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    
    # Avoid re-configuring if already configured
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Create custom formatter with mode support
    formatter = LlmXiveFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler (always added)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        # Ensure parent directory exists
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        fh = logging.FileHandler(log_path)
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    # Prevent propagation to root logger to avoid duplicate messages
    logger.propagate = False
    
    # Store mode in logger extra for future use
    if mode:
        logger.mode = mode
    
    return logger

def setup_project_logger(log_dir: str = "data/logs", mode: str = "Unknown") -> logging.Logger:
    """
    Initialize the main project logger with file output.
    This should be called once at the start of the application.
    
    Args:
        log_dir: Directory where log files will be stored.
        mode: Operating mode (e.g., 'CI', 'Research') to include in log headers.
    
    Returns:
        The configured project logger.
    """
    global _project_logger, _logger_config
    
    if _project_logger is not None:
        return _project_logger
    
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Generate log file name based on timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = str(log_path / f"pipeline_{timestamp}.log")
    
    _project_logger = get_logger("llmXive", log_file, mode=mode)
    
    # Log initialization with mode
    _project_logger.info(f"Project logger initialized in {mode} mode")
    _project_logger.info(f"Log file: {log_file}")
    
    # Store config for potential retrieval
    _logger_config = {
        "log_dir": log_dir,
        "log_file": log_file,
        "mode": mode,
        "initialized_at": datetime.now().isoformat()
    }
    
    return _project_logger

def get_console_only_logger(name: str, mode: Optional[str] = None) -> logging.Logger:
    """
    Get a logger that outputs only to console (no file).
    
    Args:
        name: Logger name.
        mode: Optional mode string to inject into logs.
    
    Returns:
        Console-only logger instance.
    """
    return get_logger(name, log_file=None, mode=mode)

def get_logger_config() -> Dict[str, Any]:
    """
    Retrieve the current logger configuration.
    
    Returns:
        Dictionary containing logger configuration details.
    """
    return _logger_config.copy()

def log_error(logger: logging.Logger, error: Exception, context: Optional[str] = None) -> None:
    """
    Log an exception with context and traceback.
    
    Args:
        logger: The logger instance to use.
        error: The exception to log.
        context: Optional context string to prepend to the error message.
    """
    import traceback
    msg = str(error)
    if context:
        msg = f"{context}: {msg}"
    
    logger.error(msg, exc_info=True)
    logger.error("Traceback:\n" + traceback.format_exc())

def log_fatal(logger: logging.Logger, message: str, exit_code: int = 1) -> None:
    """
    Log a fatal error and exit the program.
    
    Args:
        logger: The logger instance to use.
        message: The fatal error message.
        exit_code: The exit code to use.
    """
    logger.critical(message)
    sys.exit(exit_code)