"""
Logging infrastructure for the llmXive pipeline.
Handles logger setup, file rotation, and quality report initialization.
"""
import logging
import os
import csv
from pathlib import Path
from typing import Optional

# Project root is assumed to be the parent of the 'code' directory
# When running as a module, we resolve relative to this file's location
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
RESULTS_DIR = PROJECT_ROOT / "results"

# Ensure directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE_PATH = LOGS_DIR / "preprocess.log"
QUALITY_REPORT_PATH = RESULTS_DIR / "quality_report.csv"

# Logger name
LOGGER_NAME = "llmXive_pipeline"

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configure the root logger for the pipeline.
    Creates a file handler writing to logs/preprocess.log and a console handler.
    
    Args:
        log_level: Logging level string (e.g., 'DEBUG', 'INFO', 'WARNING').
    
    Returns:
        The configured logger instance.
    """
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Prevent adding handlers multiple times if called repeatedly
    if logger.handlers:
        return logger

    # Clear existing handlers to ensure clean state
    logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File Handler
    file_handler = logging.FileHandler(LOG_FILE_PATH, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

def initialize_quality_report() -> bool:
    """
    Initializes the quality report CSV file at results/quality_report.csv.
    Writes the header row if the file does not exist or is empty.
    
    Returns:
        True if initialization was successful, False otherwise.
    """
    try:
        # Check if file exists and has content
        if QUALITY_REPORT_PATH.exists() and QUALITY_REPORT_PATH.stat().st_size > 0:
            # File exists and has content, verify headers
            with open(QUALITY_REPORT_PATH, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if header == ['exclusion_type', 'count']:
                    return True
                # If headers are wrong, we might want to raise an error or overwrite?
                # Per task: "initialize... with headers". If it exists with wrong headers,
                # it's a state corruption. We'll assume for now we just return True if
                # it looks valid, or overwrite if we want to be strict.
                # Strict interpretation: Initialize means ensure it has the right headers.
                # Let's overwrite to ensure correctness as per "initialize" instruction.
        
        # Create/Overwrite with headers
        with open(QUALITY_REPORT_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['exclusion_type', 'count'])
        
        return True
    except Exception as e:
        logging.getLogger(LOGGER_NAME).error(f"Failed to initialize quality report: {e}")
        return False

def write_quality_entry(exclusion_type: str, count: int) -> bool:
    """
    Appends a row to the quality report CSV.
    
    Args:
        exclusion_type: String describing the type of exclusion (e.g., 'blink', 'noise').
        count: Integer count of excluded items.
    
    Returns:
        True if write was successful, False otherwise.
    """
    try:
        # Ensure file is initialized
        if not QUALITY_REPORT_PATH.exists():
            initialize_quality_report()
        
        with open(QUALITY_REPORT_PATH, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([exclusion_type, count])
        return True
    except Exception as e:
        logging.getLogger(LOGGER_NAME).error(f"Failed to write quality entry: {e}")
        return False

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieves the configured logger.
    
    Args:
        name: Optional sub-logger name. If None, returns the root pipeline logger.
    
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(LOGGER_NAME)
    if name:
        return logger.getChild(name)
    return logger

def main():
    """
    Main entry point for testing the logging configuration.
    Verifies that:
    1. The log file is created.
    2. The quality report CSV is created with correct headers.
    3. Writing to both works correctly.
    """
    logger = setup_logging("DEBUG")
    logger.info("Starting logging infrastructure verification.")

    # Initialize quality report
    success = initialize_quality_report()
    if not success:
        logger.error("Failed to initialize quality report.")
        return 1
    
    logger.info("Quality report initialized successfully.")

    # Verify file existence and headers
    if not QUALITY_REPORT_PATH.exists():
        logger.error("Quality report file was not created.")
        return 1

    with open(QUALITY_REPORT_PATH, 'r') as f:
        content = f.read()
        if not content.startswith("exclusion_type,count"):
            logger.error(f"Quality report has incorrect headers. Content: {content}")
            return 1
    
    logger.info("Quality report headers verified.")

    # Write a test entry
    write_quality_entry("test_exclusion", 1)
    
    # Verify the entry
    with open(QUALITY_REPORT_PATH, 'r') as f:
        lines = f.readlines()
        if len(lines) != 2:
            logger.error("Expected 2 lines in quality report (header + 1 entry).")
            return 1
        
        second_line = lines[1].strip()
        if second_line != "test_exclusion,1":
            logger.error(f"Quality report entry mismatch: {second_line}")
            return 1

    logger.info("Quality report entry verified.")
    
    # Write a log entry to verify log file
    logger.info("Verification complete. All checks passed.")
    
    # Verify log file exists
    if not LOG_FILE_PATH.exists():
        logger.error("Log file was not created.")
        return 1

    logger.info("Log file existence verified.")
    
    print("Logging infrastructure verification PASSED.")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
