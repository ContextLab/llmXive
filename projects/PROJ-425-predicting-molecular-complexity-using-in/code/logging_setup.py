import logging
import sys
from pathlib import Path
from typing import Optional
from config import get_project_root, LOG_FILE_PATH

def setup_logging() -> logging.Logger:
    """Configure and return the project logger."""
    logger = logging.getLogger("llmXive")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        # File handler
        log_file = LOG_FILE_PATH
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)

        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger

def get_logger() -> logging.Logger:
    return setup_logging()

def log_skipped_molecule(batch_id: str, reason: str, details: Optional[dict] = None):
    logger = setup_logging()
    msg = f"Skipped molecule in {batch_id}: {reason}"
    if details:
        msg += f" - Details: {details}"
    logger.warning(msg)

def log_data_loading_stats(total_loaded: int, total_sampled: int, checksum: str, duration_seconds: float):
    logger = setup_logging()
    logger.info(f"Data Loading Stats: Loaded={total_loaded}, Sampled={total_sampled}, Checksum={checksum}, Duration={duration_seconds:.2f}s")

def log_timeout_event(func_name: str, timeout_limit: float):
    logger = setup_logging()
    logger.warning(f"Function {func_name} timed out after {timeout_limit} seconds.")

def main():
    """Entry point for logging setup script (for testing)."""
    logger = setup_logging()
    logger.info("Logging system initialized.")

if __name__ == "__main__":
    main()
