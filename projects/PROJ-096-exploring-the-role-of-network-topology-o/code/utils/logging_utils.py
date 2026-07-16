import logging
import sys
from pathlib import Path
from typing import Optional
import json
from datetime import datetime

# Global logger instance to be shared across the project
_logger: Optional[logging.Logger] = None
_log_file_path: Optional[Path] = None

def init_logging(log_dir: str = "data/processed", log_level: int = logging.INFO) -> logging.Logger:
    """
    Initialize the global logging infrastructure.
    
    Creates a logger that outputs to both console and a timestamped file in data/processed.
    Ensures the log directory exists.
    
    Args:
        log_dir: Directory to store log files (relative to project root).
        log_level: Logging level (e.g., logging.INFO, logging.DEBUG).
        
    Returns:
        The configured global logger instance.
    """
    global _logger, _log_file_path
    
    if _logger is not None:
        return _logger
    
    # Ensure log directory exists
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Create unique log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"simulation_{timestamp}.log"
    _log_file_path = log_path / log_filename
    
    # Configure root logger
    _logger = logging.getLogger("llmXive")
    _logger.setLevel(log_level)
    
    # Clear any existing handlers to avoid duplicates
    _logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    _logger.addHandler(console_handler)
    
    # File handler
    file_handler = logging.FileHandler(_log_file_path)
    file_handler.setLevel(log_level)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    _logger.addHandler(file_handler)
    
    _logger.info(f"Logging initialized. Log file: {_log_file_path}")
    
    return _logger

def get_logger() -> logging.Logger:
    """
    Get the global logger instance.
    
    Raises:
        RuntimeError: If logging has not been initialized yet.
        
    Returns:
        The global logger instance.
    """
    global _logger
    if _logger is None:
        # Initialize with defaults if not explicitly called
        return init_logging()
    return _logger

def log_simulation_params(params: dict, module_name: str = "simulation") -> None:
    """
    Log simulation parameters in a structured format.
    
    Args:
        params: Dictionary of simulation parameters (e.g., N, K, t_eval, seed).
        module_name: Name of the module or component setting these params.
    """
    logger = get_logger()
    logger.info(f"--- {module_name.upper()} PARAMETERS ---")
    for key, value in sorted(params.items()):
        logger.info(f"  {key}: {value}")
    logger.info(f"-------------------------------------")

def log_warning(message: str, module_name: Optional[str] = None) -> None:
    """
    Log a warning message.
    
    Args:
        message: The warning message.
        module_name: Optional module name prefix.
    """
    logger = get_logger()
    prefix = f"[{module_name}] " if module_name else ""
    logger.warning(f"{prefix}{message}")

def log_error(message: str, module_name: Optional[str] = None) -> None:
    """
    Log an error message.
    
    Args:
        message: The error message.
        module_name: Optional module name prefix.
    """
    logger = get_logger()
    prefix = f"[{module_name}] " if module_name else ""
    logger.error(f"{prefix}{message}")

def log_critical(message: str, module_name: Optional[str] = None) -> None:
    """
    Log a critical message (e.g., SC-003 runtime violation, FR-009 failure).
    
    Args:
        message: The critical message.
        module_name: Optional module name prefix.
    """
    logger = get_logger()
    prefix = f"[{module_name}] " if module_name else ""
    logger.critical(f"{prefix}{message}")

def log_metric(name: str, value: float, unit: Optional[str] = None, module_name: Optional[str] = None) -> None:
    """
    Log a specific metric value (e.g., R, Kc, runtime).
    
    Args:
        name: Name of the metric.
        value: Numerical value of the metric.
        unit: Optional unit string (e.g., 's', 'Hz').
        module_name: Optional module name prefix.
    """
    logger = get_logger()
    prefix = f"[{module_name}] " if module_name else ""
    unit_str = f" ({unit})" if unit else ""
    logger.info(f"{prefix}Metric: {name} = {value}{unit_str}")

def get_log_file_path() -> Optional[Path]:
    """
    Get the path to the current log file.
    
    Returns:
        Path to the log file, or None if not initialized.
    """
    return _log_file_path
