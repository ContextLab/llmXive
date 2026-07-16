import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import yaml

# Ensure the code directory is in the path for relative imports if run as script
_code_root = Path(__file__).resolve().parent.parent
if str(_code_root) not in sys.path:
    sys.path.insert(0, str(_code_root))

# Constants for log levels and formats
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_DIR = Path("logs")

# Global loggers registry
_loggers: Dict[str, logging.Logger] = {}

def _ensure_log_dir():
    """Create the logs directory if it doesn't exist."""
    if not LOG_DIR.exists():
        LOG_DIR.mkdir(parents=True, exist_ok=True)

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    console_output: bool = True
) -> None:
    """
    Configure the root logger and ensure log directory exists.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional filename to write logs to (relative to project root)
        console_output: Whether to output logs to stdout
    """
    _ensure_log_dir()
    
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers to avoid duplicates on re-call
    if root_logger.handlers:
        root_logger.handlers.clear()
    
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    if log_file:
        log_path = Path(log_file)
        if not log_path.is_absolute():
            log_path = Path(log_file)
        
        # Ensure parent dir exists
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

def get_quality_logger() -> logging.Logger:
    """
    Returns a logger specifically for data quality warnings.
    This logger writes to 'logs/data_quality.log'.
    """
    logger_name = "data_quality"
    if logger_name not in _loggers:
        _ensure_log_dir()
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.WARNING)
        
        if not logger.handlers:
            handler = logging.FileHandler(LOG_DIR / "data_quality.log")
            handler.setFormatter(logging.Formatter(LOG_FORMAT))
            logger.addHandler(handler)
        
        # Prevent propagation to root to avoid double logging if root also has handlers
        logger.propagate = False
        _loggers[logger_name] = logger
    
    return _loggers[logger_name]

def get_exclusion_logger() -> logging.Logger:
    """
    Returns a logger specifically for participant/trial exclusion events.
    This logger writes to 'logs/exclusions.log'.
    """
    logger_name = "exclusions"
    if logger_name not in _loggers:
        _ensure_log_dir()
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.FileHandler(LOG_DIR / "exclusions.log")
            handler.setFormatter(logging.Formatter(LOG_FORMAT))
            logger.addHandler(handler)
        
        logger.propagate = False
        _loggers[logger_name] = logger
    
    return _loggers[logger_name]

def get_pipeline_logger() -> logging.Logger:
    """
    Returns a logger for general pipeline progress and errors.
    This logger writes to 'logs/pipeline.log'.
    """
    logger_name = "pipeline"
    if logger_name not in _loggers:
        _ensure_log_dir()
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.FileHandler(LOG_DIR / "pipeline.log")
            handler.setFormatter(logging.Formatter(LOG_FORMAT))
            logger.addHandler(handler)
        
        logger.propagate = False
        _loggers[logger_name] = logger
    
    return _loggers[logger_name]

def log_data_quality_warning(message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log a data quality warning with optional context.
    
    Args:
        message: The warning message
        context: Optional dictionary of context (e.g., participant_id, column_name)
    """
    logger = get_quality_logger()
    if context:
        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        message = f"{message} [{context_str}]"
    logger.warning(message)

def log_exclusion(reason: str, entity_id: str, entity_type: str = "participant") -> None:
    """
    Log an exclusion event.
    
    Args:
        reason: The reason for exclusion
        entity_id: The ID of the excluded entity
        entity_type: Type of entity ('participant', 'trial', 'headline')
    """
    logger = get_exclusion_logger()
    logger.info(f"EXCLUSION: {entity_type}={entity_id} | Reason: {reason}")

def log_pipeline_progress(step: str, details: Optional[str] = None) -> None:
    """
    Log general pipeline progress.
    
    Args:
        step: The current step name
        details: Optional detailed description
    """
    logger = get_pipeline_logger()
    msg = f"PROGRESS: {step}"
    if details:
        msg += f" | {details}"
    logger.info(msg)

def log_pipeline_error(step: str, error_message: str) -> None:
    """
    Log a pipeline error.
    
    Args:
        step: The step where the error occurred
        error_message: The error description
    """
    logger = get_pipeline_logger()
    logger.error(f"ERROR: {step} | {error_message}")
    # Also log to quality logger for visibility
    get_quality_logger().error(f"PIPELINE_ERROR: {step} - {error_message}")

def load_logging_config(config_path: str = "code/config.yaml") -> None:
    """
    Load logging configuration from a YAML file if it exists.
    
    Args:
        config_path: Path to the config file
    """
    path = Path(config_path)
    if path.exists():
        try:
            with open(path, 'r') as f:
                config = yaml.safe_load(f)
            
            if 'logging' in config:
                log_config = config['logging']
                level = log_config.get('level', 'INFO')
                file_log = log_config.get('file')
                console = log_config.get('console', True)
                setup_logging(level, file_log, console)
        except Exception as e:
            # Fallback to default if config is invalid
            setup_logging()
            get_pipeline_logger().warning(f"Failed to load logging config: {e}")
    else:
        setup_logging()