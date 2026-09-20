import logging
import os
import sys
from pathlib import Path
from typing import Optional
from config import get_project_root, ensure_directories

# Global logger instance
_logger: Optional[logging.Logger] = None

def get_log_path(filename: str) -> Path:
    """Construct the full path for a log file under the logs directory."""
    project_root = get_project_root()
    logs_dir = project_root / "logs"
    ensure_directories([logs_dir])
    return logs_dir / filename

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = "app.log"
) -> logging.Logger:
    """
    Configure the global logger.
    
    Args:
        log_level: Logging level (e.g., 'INFO', 'DEBUG').
        log_file: Optional filename to write logs to (relative to logs/).
    """
    global _logger
    if _logger is not None:
        return _logger

    logger = logging.getLogger("llmXive")
    logger.setLevel(getattr(logging, log_level.upper()))

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_path = get_log_path(log_file)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    _logger = logger
    return logger

def get_logger() -> logging.Logger:
    """Get the configured logger instance."""
    if _logger is None:
        # Default setup if not explicitly called
        return setup_logging()
    return _logger

def log_counterbalance_strategy(seed: int, split_ratio: float, log_file: str = "counterbalance_strategy.log") -> None:
    """
    Log the counterbalancing assignment strategy details.
    
    Args:
        seed: The random seed used for assignment generation.
        split_ratio: The ratio of participants assigned to Low-High vs High-Low.
        log_file: The filename for the log (relative to logs/).
    """
    logger = get_logger()
    log_path = get_log_path(log_file)
    
    # Ensure the logs directory exists
    ensure_directories([log_path.parent])
    
    # Create a dedicated handler for the strategy log to ensure it goes to the specific file
    # We append a handler specifically for this file if it doesn't exist yet, 
    # or just log to the main file if the main logger is configured to write there.
    # However, to be precise about the requirement "logs/counterbalance_strategy.log",
    # we will append a FileHandler specifically for this file.
    
    strategy_handler = logging.FileHandler(log_path)
    strategy_handler.setFormatter(logging.Formatter('%(message)s'))
    
    # Avoid adding duplicates if called multiple times
    if not any(isinstance(h, logging.FileHandler) and h.baseFilename == str(log_path) for h in logger.handlers):
        logger.addHandler(strategy_handler)
    
    logger.info(f"Counterbalance Strategy Configuration:")
    logger.info(f"  Random Seed: {seed}")
    logger.info(f"  Split Ratio (Low-High vs High-Low): {split_ratio}")
    logger.info(f"  Assignment Method: Seeded Random Shuffle (NumPy)")
    logger.info(f"  Output File: data/processed/counterbalance_assignment.csv")
    
    # Remove the temporary handler to avoid cluttering the main logger for subsequent calls
    # unless we want to keep it. The requirement is just to log it.
    # We'll keep it simple: log the message and ensure the file is written.
    # The FileHandler above will write the message.
    
    # To ensure the log file is created even if the logger wasn't fully set up with file handlers yet:
    logger.info("--- End of Strategy Log ---")