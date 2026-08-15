import logging
import os
from pathlib import Path
from typing import Optional
import sys
from ..config import get_project_root, ensure_directories

def get_log_path() -> Path:
    """Return the path to the logs directory."""
    root = get_project_root()
    log_dir = root / "logs"
    ensure_directories([log_dir])
    return log_dir

def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure the root logger with console and optional file handlers.
    
    Args:
        level: Logging level (e.g., logging.INFO).
        log_file: Optional filename relative to the logs directory.
    
    Returns:
        The root logger instance.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates in interactive environments
    if root_logger.handlers:
        root_logger.handlers.clear()
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    ch.setFormatter(formatter)
    root_logger.addHandler(ch)
    
    # File handler if specified
    if log_file:
        log_path = get_log_path() / log_file
        ensure_directories([log_path.parent])
        fh = logging.FileHandler(log_path)
        fh.setLevel(level)
        fh.setFormatter(formatter)
        root_logger.addHandler(fh)
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)

def log_counterbalance_strategy(strategy_description: str, output_file: str = "counterbalance_strategy.log") -> None:
    """
    Log the specific counterbalancing assignment strategy to a file.
    
    This function writes a detailed description of the counterbalancing strategy
    used in the experiment (e.g., Latin Square, AB/BA order) to a log file.
    
    Args:
        strategy_description: The text description of the strategy.
        output_file: The filename for the log (relative to logs/).
    """
    log_path = get_log_path() / output_file
    ensure_directories([log_path.parent])
    
    logger = logging.getLogger("counterbalance")
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to ensure clean state if called multiple times
    logger.handlers.clear()
    
    # Create file handler specifically for this log
    fh = logging.FileHandler(log_path, mode='w')
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    # Write the strategy
    logger.info("Counterbalancing Assignment Strategy Log")
    logger.info("=" * 50)
    logger.info("")
    logger.info(strategy_description)
    logger.info("")
    logger.info("=" * 50)
    
    # Close handler to flush
    fh.close()
    logger.info(f"Strategy log saved to: {log_path}")
