"""
Logging configuration and utilities.
"""
import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any

# Project root
project_root = Path(__file__).resolve().parent.parent
logs_dir = project_root / "logs"

# Ensure logs directory exists
logs_dir.mkdir(exist_ok=True)

# Default log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Global logger map to avoid re-initialization
_loggers: Dict[str, logging.Logger] = {}


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    console: bool = True
) -> None:
    """
    Configure the root logger.
    
    Args:
        level: Logging level.
        log_file: Path to log file. If None, defaults to logs/pipeline.log.
        console: Whether to log to console.
    """
    if log_file is None:
        log_file = logs_dir / "pipeline.log"
    else:
        log_file = Path(log_file)

    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # File handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger by name, creating it if necessary.
    
    Args:
        name: Logger name. If None, returns the root logger.
        
    Returns:
        logging.Logger: The requested logger.
    """
    if name is None:
        return logging.getLogger()
        
    if name in _loggers:
        return _loggers[name]
        
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Inherit handlers from root if not configured
        pass
    _loggers[name] = logger
    return logger


def configure_module_logger(
    module_name: str,
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Configure a specific module logger.
    
    Args:
        module_name: Name of the module.
        level: Logging level.
        log_file: Optional log file path.
        
    Returns:
        logging.Logger: The configured logger.
    """
    logger = get_logger(module_name)
    logger.setLevel(level)
    
    if not logger.handlers:
        formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
        
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            handler = RotatingFileHandler(
                log_path, maxBytes=10*1024*1024, backupCount=5
            )
        else:
            handler = RotatingFileHandler(
                logs_dir / f"{module_name}.log", 
                maxBytes=10*1024*1024, 
                backupCount=5
            )
        
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Also add console handler for active development
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
    return logger


def get_module_logger(module_name: str) -> logging.Logger:
    """
    Convenience function to get a logger for a module.
    
    Args:
        module_name: Name of the module.
        
    Returns:
        logging.Logger: The logger for the module.
    """
    return configure_module_logger(module_name)


def log_ingestion_summary(
    logger: logging.Logger,
    source: str,
    total_rows: int,
    excluded_rows: int,
    reasons: Optional[Dict[str, int]] = None
) -> None:
    """
    Log a summary of an ingestion step.
    
    Args:
        logger: Logger instance.
        source: Name of the data source.
        total_rows: Total rows processed.
        excluded_rows: Number of rows excluded.
        reasons: Dictionary of exclusion reasons and counts.
    """
    logger.info(f"Ingestion Summary for {source}:")
    logger.info(f"  Total rows: {total_rows}")
    logger.info(f"  Excluded rows: {excluded_rows}")
    if reasons:
        logger.info("  Exclusion reasons:")
        for reason, count in reasons.items():
            logger.info(f"    - {reason}: {count}")
