import logging
import os
from pathlib import Path
from typing import Optional
import sys

from ..config import get_project_root, ensure_directories

def get_log_path() -> Path:
    """Get the path to the logs directory."""
    return get_project_root() / "logs"

def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> None:
    """
    Setup logging configuration.
    
    Args:
        level: Logging level.
        log_file: Optional log file path.
    """
    ensure_directories()
    log_dir = get_log_path()
    log_dir.mkdir(parents=True, exist_ok=True)
    
    if log_file is None:
        log_file = str(log_dir / "pipeline.log")
    
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers
    )

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name.
        
    Returns:
        Logger instance.
    """
    return logging.getLogger(name)

def log_counterbalance_strategy(strategy: str) -> None:
    """
    Log the counterbalance strategy used.
    
    Args:
        strategy: Strategy description.
    """
    logger = get_logger(__name__)
    log_file = get_log_path() / "counterbalance_strategy.log"
    
    with open(log_file, "a") as f:
        f.write(f"{strategy}\n")
    
    logger.info(f"Logged counterbalance strategy: {strategy}")

if __name__ == "__main__":
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Logging module initialized.")
