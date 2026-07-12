"""
Logging configuration for the LLMXive pipeline.
Provides global logger with file and console handlers.
"""
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Global logger instance
_global_logger: Optional[logging.Logger] = None


def configure_logging_level(
    level: str = "INFO",
    log_file: Optional[str] = None,
    results_dir: Optional[str] = None
) -> logging.Logger:
    """
    Configure the global logger with file and console handlers.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file. If None, logs to results_dir/logs/pipeline.log
        results_dir: Base directory for logs if log_file is not specified
        
    Returns:
        The configured global logger
    """
    global _global_logger
    
    # Create logger
    _global_logger = logging.getLogger("llmxive")
    _global_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Clear existing handlers
    _global_logger.handlers.clear()
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
    console_handler.setFormatter(formatter)
    _global_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_path = Path(log_file)
    elif results_dir:
        log_path = Path(results_dir) / "logs" / "pipeline.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        log_path = Path("logs") / "pipeline.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
    file_handler.setFormatter(formatter)
    _global_logger.addHandler(file_handler)
    
    _global_logger.info(f"Logging configured: level={level}, file={log_path}")
    
    return _global_logger


def get_logger() -> logging.Logger:
    """
    Get the global logger. Must be called after configure_logging_level().
    
    Returns:
        The global logger instance
    """
    if _global_logger is None:
        raise RuntimeError("Logger not configured. Call configure_logging_level() first.")
    return _global_logger


def get_module_logger(name: str) -> logging.Logger:
    """
    Get a module-specific logger that inherits from the global logger.
    
    Args:
        name: Module name (e.g., 'src.data.download')
        
    Returns:
        A logger instance for the specified module
    """
    if _global_logger is None:
        # Fallback to basic config if not initialized
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(name)
        
    return logging.getLogger(f"llmxive.{name}")
