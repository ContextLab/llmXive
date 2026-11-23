import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Configure log directory
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Global logger instance
_logger = None

def setup_logger(name: str = "research_pipeline", log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Setup a logger with file and console handlers.
    
    Args:
        name: Logger name
        log_file: Optional path to log file
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    global _logger
    
    if _logger is not None:
        return _logger
    
    _logger = logging.getLogger(name)
    _logger.setLevel(level)
    
    # Clear existing handlers
    _logger.handlers.clear()
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    _logger.addHandler(console_handler)
    
    # File handler (if log_file provided)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        _logger.addHandler(file_handler)
    
    return _logger

def get_logger(name: str = "research_pipeline") -> logging.Logger:
    """
    Get a logger instance. Creates one if it doesn't exist.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    global _logger
    if _logger is None:
        _logger = setup_logger(name)
    return logging.getLogger(name)

def log_audit_event(event_type: str, details: Dict[str, Any], logger_name: str = "research_pipeline"):
    """
    Log an audit event for compliance tracking.
    
    Args:
        event_type: Type of event (e.g., "DATA_ACCESS", "ETHICS_CHECK")
        details: Event details
        logger_name: Logger name to use
    """
    log = get_logger(logger_name)
    timestamp = datetime.utcnow().isoformat() + 'Z'
    log.info(f"AUDIT_EVENT: {event_type} | {timestamp} | {details}")

def log_script_start(script_name: str, args: Any = None, logger_name: str = "research_pipeline"):
    """
    Log the start of a script execution.
    
    Args:
        script_name: Name of the script
        args: Command line arguments (optional)
        logger_name: Logger name to use
    """
    log = get_logger(logger_name)
    log.info(f"SCRIPT_START: {script_name} | {datetime.utcnow().isoformat()}")
    if args:
        log.info(f"SCRIPT_ARGS: {vars(args) if hasattr(args, '__dict__') else args}")

def log_script_end(script_name: str, success: bool, error: Optional[str] = None, output: Optional[str] = None, logger_name: str = "research_pipeline"):
    """
    Log the end of a script execution.
    
    Args:
        script_name: Name of the script
        success: Whether the script completed successfully
        error: Error message if failed
        output: Output file path if applicable
        logger_name: Logger name to use
    """
    log = get_logger(logger_name)
    status = "SUCCESS" if success else "FAILURE"
    log.info(f"SCRIPT_END: {script_name} | {status} | {datetime.utcnow().isoformat()}")
    if error:
        log.error(f"ERROR: {error}")
    if output:
        log.info(f"OUTPUT: {output}")

def log_data_operation(operation: str, path: Optional[str] = None, rows: Optional[int] = None, logger_name: str = "research_pipeline"):
    """
    Log a data operation (read, write, transform).
    
    Args:
        operation: Description of the operation
        path: File path if applicable
        rows: Number of rows affected
        logger_name: Logger name to use
    """
    log = get_logger(logger_name)
    details = f"{operation}"
    if path:
        details += f" | PATH: {path}"
    if rows is not None:
        details += f" | ROWS: {rows}"
    log.info(f"DATA_OP: {details}")

def log_analysis_step(step_name: str, metrics: Dict[str, Any], logger_name: str = "research_pipeline"):
    """
    Log an analysis step with its metrics.
    
    Args:
        step_name: Name of the analysis step
        metrics: Dictionary of metrics
        logger_name: Logger name to use
    """
    log = get_logger(logger_name)
    log.info(f"ANALYSIS_STEP: {step_name} | {metrics}")

# Convenience functions
def info(msg: str, logger_name: str = "research_pipeline"):
    get_logger(logger_name).info(msg)

def debug(msg: str, logger_name: str = "research_pipeline"):
    get_logger(logger_name).debug(msg)

def warning(msg: str, logger_name: str = "research_pipeline"):
    get_logger(logger_name).warning(msg)

def error(msg: str, logger_name: str = "research_pipeline"):
    get_logger(logger_name).error(msg)

def critical(msg: str, logger_name: str = "research_pipeline"):
    get_logger(logger_name).critical(msg)

def exception(msg: str, logger_name: str = "research_pipeline"):
    get_logger(logger_name).exception(msg)

def log_exception(exc: Exception, logger_name: str = "research_pipeline"):
    get_logger(logger_name).exception(f"EXCEPTION: {str(exc)}")
