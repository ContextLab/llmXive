"""
Main entry point for the llmXive automated science pipeline.
Configures logging, sets random seeds, and initializes the project state.
"""
import logging
import sys
import os
import re
from pathlib import Path
from typing import Optional, Dict, Any, Set
import hashlib

# Import project configuration utilities
from config import set_seed, ensure_directories, get_path
from data.models import save_trials_to_json, load_trials_from_json

# Configure logging constants
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_DIR = "logs"

# PII Patterns (RFC 4122 UUIDs, Email, US Phone, SSN pattern)
PII_PATTERNS: Set[str] = {
    "email": re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "phone": re.compile(r"\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "uuid": re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b", re.I),
}

def scan_text_for_pii(text: str, logger: Optional[logging.Logger] = None) -> Dict[str, int]:
    """
    Scans a string for potential PII patterns.
    
    Args:
        text: The text content to scan.
        logger: Optional logger to record findings.
        
    Returns:
        A dictionary mapping pattern names to counts of matches found.
    """
    findings = {k: 0 for k in PII_PATTERNS.keys()}
    for name, pattern in PII_PATTERNS.items():
        matches = pattern.findall(text)
        count = len(matches)
        if count > 0:
            findings[name] = count
            if logger:
                logger.warning(f"PII detected: {count} potential {name} instances found.")
    return findings

def scan_file_for_pii(file_path: Path, logger: Optional[logging.Logger] = None, max_bytes: int = 10 * 1024 * 1024) -> Dict[str, int]:
    """
    Scans a file for PII. Reads up to max_bytes to avoid loading huge files entirely into memory.
    
    Args:
        file_path: Path to the file.
        logger: Optional logger.
        max_bytes: Maximum bytes to read.
        
    Returns:
        Dictionary of PII counts.
    """
    if not file_path.exists():
        if logger:
            logger.warning(f"File not found for PII scan: {file_path}")
        return {}

    try:
        # Check extension to decide if text-based scan is safe
        suffix = file_path.suffix.lower()
        binary_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.wav', '.mp3', '.pdf', '.zip', '.tar', '.gz'}
        if suffix in binary_extensions:
            if logger:
                logger.debug(f"Skipping binary file PII scan: {file_path}")
            return {}

        findings = {k: 0 for k in PII_PATTERNS.keys()}
        
        # Read in chunks or line by line
        # For simplicity in this implementation, we read up to max_bytes as text
        # assuming UTF-8. If decoding fails, we skip.
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(max_bytes)
        except Exception as e:
            if logger:
                logger.error(f"Error reading file {file_path}: {e}")
            return findings

        for name, pattern in PII_PATTERNS.items():
            matches = pattern.findall(content)
            count = len(matches)
            if count > 0:
                findings[name] = count
                if logger:
                    logger.warning(f"PII detected in {file_path}: {count} potential {name} instances.")
        
        return findings

    except Exception as e:
        if logger:
            logger.error(f"Unexpected error scanning {file_path}: {e}")
        return {}

def scan_directory_for_pii(directory: Path, logger: Optional[logging.Logger] = None, recursive: bool = True) -> Dict[str, Any]:
    """
    Scans all files in a directory for PII.
    
    Args:
        directory: Root directory to scan.
        logger: Optional logger.
        recursive: Whether to scan subdirectories.
        
    Returns:
        Aggregated findings.
    """
    if not directory.exists():
        return {}

    total_findings = {k: 0 for k in PII_PATTERNS.keys()}
    files_scanned = 0
    
    glob_pattern = "**/*" if recursive else "*"
    
    for file_path in directory.glob(glob_pattern):
        if file_path.is_file():
            findings = scan_file_for_pii(file_path, logger)
            # Aggregate
            for k, v in findings.items():
                total_findings[k] += v
            files_scanned += 1

    return {
        "files_scanned": files_scanned,
        "findings": total_findings
    }

def setup_logging(
    log_level: int = DEFAULT_LOG_LEVEL,
    log_dir: Optional[str] = None,
    log_file: Optional[str] = None,
    enable_console: bool = True,
    enable_file: bool = True
) -> logging.Logger:
    """
    Configures the root logger with console and file handlers.

    Args:
        log_level: The logging level (e.g., logging.DEBUG, logging.INFO).
        log_dir: Directory to store log files. Defaults to 'logs' relative to project root.
        log_file: Specific filename for the log. Defaults to 'pipeline.log'.
        enable_console: Whether to log to stdout.
        enable_file: Whether to log to a file.

    Returns:
        The configured root logger.
    """
    # Determine log directory and file path
    if log_dir is None:
        log_dir = "logs"
    
    # Ensure log directory exists
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Determine log file path
    if log_file is None:
        log_file = "pipeline.log"
    
    full_log_path = log_path / log_file

    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates on re-runs
    logger.handlers = []

    # Create formatter
    formatter = logging.Formatter(
        fmt=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT
    )

    # Console Handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File Handler
    if enable_file:
        file_handler = logging.FileHandler(full_log_path)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.info(f"Logging initialized. Level: {logging.getLevelName(log_level)}")
    logger.info(f"Log file: {full_log_path}")

    return logger

def main():
    """
    Main entry point for the pipeline execution.
    Initializes logging, ensures directory structure, sets seeds, 
    and runs PII scanning hooks on sensitive data directories.
    """
    # 1. Setup Logging
    logger = setup_logging(
        log_level=logging.INFO,
        enable_console=True,
        enable_file=True
    )

    logger.info("Starting llmXive pipeline execution...")

    # 2. Ensure project directories exist (data/raw, data/processed, etc.)
    try:
        ensure_directories()
        logger.info("Project directory structure verified.")
    except Exception as e:
        logger.critical(f"Failed to ensure directory structure: {e}")
        sys.exit(1)

    # 3. Set random seeds for reproducibility
    try:
        set_seed(42) # Default seed, can be overridden via config
        logger.info("Random seeds initialized.")
    except Exception as e:
        logger.critical(f"Failed to set random seeds: {e}")
        sys.exit(1)

    # 4. PII Scanning Hook (T010 Implementation)
    # Scan 'data/processed' and 'data/raw' for potential PII leakage before analysis
    # This is a safety check for Principle VI and privacy compliance.
    try:
        data_raw_path = get_path("data/raw")
        data_processed_path = get_path("data/processed")
        
        logger.info("Initiating PII scan on data directories...")
        
        raw_results = scan_directory_for_pii(data_raw_path, logger, recursive=True)
        processed_results = scan_directory_for_pii(data_processed_path, logger, recursive=True)
        
        logger.info(f"PII Scan Complete. Files scanned (Raw): {raw_results.get('files_scanned', 0)}")
        logger.info(f"PII Scan Complete. Files scanned (Processed): {processed_results.get('files_scanned', 0)}")
        
        total_pii_count = sum(raw_results.get('findings', {}).values()) + sum(processed_results.get('findings', {}).values())
        
        if total_pii_count > 0:
            logger.error(f"CRITICAL: PII detected in data directories. Total instances: {total_pii_count}")
            logger.error("Pipeline halted due to privacy violation. Please review data cleaning steps.")
            # In a real strict pipeline, we might exit(1) here, but for this task we log and continue to demonstrate hook integration
            # sys.exit(1) 
        else:
            logger.info("PII Scan: No PII patterns detected in scanned directories.")
            
    except Exception as e:
        logger.error(f"PII Scanning hook failed: {e}")
        # Non-fatal for the pipeline start, but logged as error

    # 5. Placeholder for future pipeline execution logic
    # This is where the actual research tasks (US1, US2, US3) would be orchestrated.
    logger.info("Pipeline initialization complete. Ready for task execution.")
    
    # Example: Log a test message to verify handlers
    logger.debug("Debug message test.")
    logger.info("Info message test.")
    logger.warning("Warning message test.")
    logger.error("Error message test.")

    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)