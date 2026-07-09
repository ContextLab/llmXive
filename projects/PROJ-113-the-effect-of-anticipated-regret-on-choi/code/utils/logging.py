"""
Logging infrastructure for data hygiene and PII scanning.

This module provides a centralized logging configuration that:
1. Sets up structured logging with timestamps and levels.
2. Integrates PII detection (regex-based) for data hygiene.
3. Ensures logs are written to both console and file.
"""

import logging
import re
import sys
from pathlib import Path
from typing import Optional, Any, Dict

# PII Patterns for detection (email, phone, SSN, IP)
PII_PATTERNS = {
    "email": re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
    "phone": re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "ip": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
}

# Default log file path relative to project root
LOG_FILE_PATH = "data/results/pipeline.log"


def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    project_root: Optional[Path] = None
) -> logging.Logger:
    """
    Configure the root logger for the project.

    Args:
        log_level: Logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Relative path to the log file. Defaults to data/results/pipeline.log.
        project_root: Base path for the project. Defaults to current working directory.

    Returns:
        The configured root logger instance.
    """
    if project_root is None:
        project_root = Path.cwd()

    if log_file is None:
        log_file = LOG_FILE_PATH

    log_path = project_root / log_file
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # File handler
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Avoid duplicate handlers if called multiple times
    if not root_logger.handlers:
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

    return root_logger


def scan_for_pii(text: str, patterns: Optional[Dict[str, re.Pattern]] = None) -> Dict[str, Any]:
    """
    Scan a string for potential PII patterns.

    Args:
        text: The string to scan.
        patterns: Optional dict of regex patterns to use. Defaults to PII_PATTERNS.

    Returns:
        A dictionary mapping pattern names to lists of found matches.
    """
    if patterns is None:
        patterns = PII_PATTERNS

    findings: Dict[str, Any] = {}
    for name, pattern in patterns.items():
        matches = pattern.findall(text)
        if matches:
            findings[name] = list(set(matches))  # Deduplicate

    return findings


def log_pii_scan(logger: logging.Logger, text: str, context: str = "Unknown") -> None:
    """
    Scan text for PII and log findings if any are detected.

    Args:
        logger: The logger instance to use.
        text: The text to scan.
        context: A descriptive string for the log message (e.g., "Row 123, Column 'email'").
    """
    findings = scan_for_pii(text)
    if findings:
        logger.warning(f"PII DETECTED in {context}: {findings}")
    else:
        logger.debug(f"No PII detected in {context}")


# Convenience logger instance for general use
logger = setup_logging()
__all__ = ["setup_logging", "scan_for_pii", "log_pii_scan", "logger", "PII_PATTERNS"]
