import logging
import sys
from pathlib import Path
from typing import Optional
import json
from datetime import datetime

from config import get_project_root, get_log_file_path

# Global logger instance
_logger: Optional[logging.Logger] = None

def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return the project logger.
    
    Sets up a logger that outputs to both console and a log file.
    The log file is located at the path defined in config.
    """
    global _logger
    if _logger is not None:
        return _logger

    logger = logging.getLogger("llmXive_pipeline")
    logger.setLevel(log_level)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        logger.handlers.clear()

    # Create formatter with timestamp, level, and message
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    log_path = get_log_file_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    _logger = logger
    return logger

def get_logger() -> logging.Logger:
    """Return the global logger instance, initializing it if necessary."""
    if _logger is None:
        return setup_logging()
    return _logger

def log_skipped_molecule(cid: int, reason: str, logger: Optional[logging.Logger] = None) -> None:
    """
    Log a skipped molecule event in the specific JSON format required by T008.
    
    Args:
        cid: The molecular ID (CID) of the skipped molecule.
        reason: The reason for skipping, either 'timeout' or 'invalid_smiles'.
        logger: Optional logger instance. If None, uses the global logger.
    
    The log message format is: {"event": "skipped", "reason": "...", "cid": ...}
    """
    if logger is None:
        logger = get_logger()
    
    # Ensure reason is valid
    if reason not in ("timeout", "invalid_smiles"):
        logger.warning(f"Invalid skip reason '{reason}' for CID {cid}. Defaulting to 'invalid_smiles'.")
        reason = "invalid_smiles"
    
    log_entry = {
        "event": "skipped",
        "reason": reason,
        "cid": cid
    }
    
    # Log as JSON string to ensure exact format compliance
    logger.warning(json.dumps(log_entry))

def log_timeout_event(cid: int, logger: Optional[logging.Logger] = None) -> None:
    """
    Convenience wrapper for logging a timeout skip event.
    
    Args:
        cid: The molecular ID.
        logger: Optional logger instance.
    """
    log_skipped_molecule(cid, "timeout", logger)

def log_data_loading_stats(
    total_loaded: int,
    total_sampled: int,
    checksum: str,
    duration_seconds: float,
    logger: Optional[logging.Logger] = None
) -> None:
    """Log statistics about the data loading process."""
    if logger is None:
        logger = get_logger()
    
    stats = {
        "event": "data_loading_stats",
        "total_loaded": total_loaded,
        "total_sampled": total_sampled,
        "checksum": checksum,
        "duration_seconds": round(duration_seconds, 2)
    }
    logger.info(json.dumps(stats))

def main():
    """Simple test to verify logging setup."""
    logger = setup_logging()
    logger.info("Logging setup test initiated.")
    log_skipped_molecule(12345, "invalid_smiles", logger)
    log_skipped_molecule(67890, "timeout", logger)
    logger.info("Logging setup test complete.")

if __name__ == "__main__":
    main()