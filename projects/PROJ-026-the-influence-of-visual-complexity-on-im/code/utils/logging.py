import logging
import os
import sys
from pathlib import Path
from typing import Optional
from config import get_project_root, ensure_directories

def get_log_path(filename: str = "app.log") -> Path:
    """Get the path to the log file."""
    project_root = get_project_root()
    log_dir = project_root / "logs"
    ensure_directories([log_dir])
    return log_dir / filename

def setup_logging(log_level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """Configure the logging infrastructure."""
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_path = get_log_path(log_file)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger

def get_logger(name: str = "llmXive") -> logging.Logger:
    """Get a logger instance with the specified name."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Ensure handlers are set up if this is the first call
        setup_logging()
    return logger

def log_counterbalance_strategy(seed: int, split_ratio: float, output_file: str = "counterbalance_strategy.log") -> None:
    """
    Log the specific counterbalancing assignment strategy used.
    
    Args:
        seed: The random seed used for assignment generation.
        split_ratio: The ratio of participants in each condition (e.g., 0.5 for 50/50).
        output_file: The name of the log file to write the strategy to.
    """
    logger = get_logger("Counterbalance")
    log_path = get_log_path(output_file)
    
    # Ensure the log directory exists
    ensure_directories([log_path.parent])
    
    # Create a file handler specifically for this log
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Add handler if not already present
    if not any(isinstance(h, logging.FileHandler) and h.baseFilename == str(log_path) for h in logger.handlers):
        logger.addHandler(file_handler)
    
    logger.info(f"Counterbalancing Strategy Log")
    logger.info(f"=" * 50)
    logger.info(f"Random Seed: {seed}")
    logger.info(f"Split Ratio: {split_ratio:.4f} (Low-High : High-Low)")
    logger.info(f"Method: Seeded random shuffle (np.random.default_rng(seed))")
    logger.info(f"Assignment File: data/processed/counterbalance_assignment.csv")
    logger.info(f"=" * 50)
    
    # Remove the handler to avoid accumulation
    logger.removeHandler(file_handler)
