import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Ensure output directories exist
OUTPUT_DIR = Path("output")
LOGS_DIR = OUTPUT_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def get_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Configure and return a logger that writes to both console and a specific log file.

    Args:
        name: The name of the logger (e.g., 'ingestion', 'modeling').
        log_file: Relative path to the log file under output/logs/.
        level: Logging level (default: INFO).

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times if called repeatedly
    if logger.handlers:
        return logger

    # Formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if log_file specified)
    if log_file:
        full_path = LOGS_DIR / log_file
        file_handler = logging.FileHandler(full_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

def setup_ingestion_logger() -> logging.Logger:
    """Setup logger for ingestion tasks writing to output/logs/ingestion.log."""
    return get_logger("ingestion", "ingestion.log")

def setup_modeling_logger() -> logging.Logger:
    """Setup logger for modeling tasks writing to output/logs/modeling.log."""
    return get_logger("modeling", "modeling.log")

def main():
    """
    Main entry point to demonstrate logging setup.
    Creates log entries in both ingestion.log and modeling.log.
    """
    ingestion_log = setup_ingestion_logger()
    modeling_log = setup_modeling_logger()

    ingestion_log.info("Ingestion pipeline started.")
    ingestion_log.debug("Initializing data fetchers.")
    ingestion_log.warning("Sample warning for ingestion process.")

    modeling_log.info("Modeling pipeline started.")
    modeling_log.debug("Loading configuration.")
    modeling_log.error("Sample error for modeling process.")

    print("Logging infrastructure initialized. Check output/logs/ingestion.log and output/logs/modeling.log")

if __name__ == "__main__":
    main()