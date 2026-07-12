"""
Logging configuration for the Neural Entropy and Cognitive Flexibility project.

This module provides centralized logging infrastructure to track:
- Data flow transitions (raw -> processed -> analyzed)
- Exclusion reasons (participant filtering)
- Resource usage (RAM/Disk monitoring)
- General operational logs

All loggers use a consistent format and write to both console and 
project-specific log files under the `logs/` directory.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Project root directory (assumed to be the parent of 'code')
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure logs directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Log format with timestamp, level, logger name, and message
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Dictionary to cache logger instances
_loggers: dict = {}

def _get_formatter() -> logging.Formatter:
    """Return the standard log formatter."""
    return logging.Formatter(LOG_FORMAT, DATE_FORMAT)

def _ensure_file_handler(filepath: Path, level: int = logging.DEBUG) -> logging.FileHandler:
    """Create or retrieve a file handler for the given path."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    handler = logging.FileHandler(filepath, mode='a', encoding='utf-8')
    handler.setLevel(level)
    handler.setFormatter(_get_formatter())
    return handler

def setup_general_logger(name: str = "general") -> logging.Logger:
    """
    Set up a general-purpose logger for operational messages.
    
    Args:
        name: Logger name (e.g., "general", "pipeline")
    
    Returns:
        Configured logger instance
    """
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(_get_formatter())
    logger.addHandler(console_handler)
    
    # File handler
    log_file = LOGS_DIR / f"{name}.log"
    file_handler = _ensure_file_handler(log_file, logging.DEBUG)
    logger.addHandler(file_handler)
    
    logger.propagate = False
    _loggers[name] = logger
    
    return logger

def setup_data_flow_logger() -> logging.Logger:
    """
    Set up a dedicated logger for tracking data flow transitions.
    
    Logs data movement between stages (raw -> processed -> analyzed)
    and records checksums, file paths, and transformation details.
    
    Returns:
        Configured logger instance
    """
    logger_name = "data_flow"
    if logger_name in _loggers:
        return _loggers[logger_name]
    
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(_get_formatter())
    logger.addHandler(console_handler)
    
    # File handler
    log_file = LOGS_DIR / "data_flow.log"
    file_handler = _ensure_file_handler(log_file, logging.DEBUG)
    logger.addHandler(file_handler)
    
    logger.propagate = False
    _loggers[logger_name] = logger
    
    return logger

def setup_exclusion_logger() -> logging.Logger:
    """
    Set up a dedicated logger for tracking participant exclusion reasons.
    
    Logs reasons for excluding participants from analysis, including:
    - Insufficient data duration
    - High artifact corruption
    - Low SNR
    - Missing behavioral scores
    - Other quality control failures
    
    Returns:
        Configured logger instance
    """
    logger_name = "exclusions"
    if logger_name in _loggers:
        return _loggers[logger_name]
    
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(_get_formatter())
    logger.addHandler(console_handler)
    
    # File handler
    log_file = LOGS_DIR / "exclusions.log"
    file_handler = _ensure_file_handler(log_file, logging.DEBUG)
    logger.addHandler(file_handler)
    
    logger.propagate = False
    _loggers[logger_name] = logger
    
    return logger

def setup_resource_logger() -> logging.Logger:
    """
    Set up a dedicated logger for resource usage monitoring.
    
    Logs RAM and disk usage snapshots to track compliance with
    project resource limits (<7GB RAM, <14GB Disk).
    
    Returns:
        Configured logger instance
    """
    logger_name = "resources"
    if logger_name in _loggers:
        return _loggers[logger_name]
    
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Console handler (only warnings/errors)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(_get_formatter())
    logger.addHandler(console_handler)
    
    # File handler
    log_file = LOGS_DIR / "resource_usage.log"
    file_handler = _ensure_file_handler(log_file, logging.DEBUG)
    logger.addHandler(file_handler)
    
    logger.propagate = False
    _loggers[logger_name] = logger
    
    return logger

def get_logger(name: str = "general") -> logging.Logger:
    """
    Get or create a logger with the specified name.
    
    Args:
        name: Logger name
    
    Returns:
        Configured logger instance
    """
    if name == "data_flow":
        return setup_data_flow_logger()
    elif name == "exclusions":
        return setup_exclusion_logger()
    elif name == "resources":
        return setup_resource_logger()
    else:
        return setup_general_logger(name)

def log_data_transition(
    stage_from: str,
    stage_to: str,
    input_files: list,
    output_files: list,
    checksums: Optional[dict] = None,
    notes: Optional[str] = None
) -> None:
    """
    Log a data flow transition between processing stages.
    
    Args:
        stage_from: Source stage (e.g., "raw", "processed")
        stage_to: Target stage (e.g., "processed", "analyzed")
        input_files: List of input file paths
        output_files: List of output file paths
        checksums: Optional dict mapping files to their checksums
        notes: Optional notes about the transition
    """
    logger = setup_data_flow_logger()
    
    msg_parts = [
        f"DATA TRANSITION: {stage_from} -> {stage_to}",
        f"Inputs: {len(input_files)} files",
        f"Outputs: {len(output_files)} files"
    ]
    
    if checksums:
        msg_parts.append(f"Checksums verified: {len(checksums)} files")
    
    if notes:
        msg_parts.append(f"Notes: {notes}")
    
    logger.info(" | ".join(msg_parts))
    
    # Log individual file transitions at DEBUG level
    for f_in in input_files:
        logger.debug(f"  Input: {f_in}")
    for f_out in output_files:
        logger.debug(f"  Output: {f_out}")
    if checksums:
        for f, checksum in checksums.items():
            logger.debug(f"  Checksum({f}): {checksum}")

def log_exclusion_reason(
    participant_id: str,
    reason_code: str,
    reason_description: str,
    details: Optional[dict] = None
) -> None:
    """
    Log a participant exclusion reason.
    
    Args:
        participant_id: Unique identifier for the participant
        reason_code: Short code for the reason (e.g., "LOW_SNR", "MISSING_DATA")
        reason_description: Human-readable description
        details: Optional dict with additional details (e.g., actual SNR value)
    """
    logger = setup_exclusion_logger()
    
    msg = f"EXCLUSION: Participant {participant_id} - {reason_code}: {reason_description}"
    
    if details:
        detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
        msg += f" | Details: {detail_str}"
    
    logger.warning(msg)

def log_resource_usage(
    memory_gb: float,
    disk_gb: float,
    threshold_memory_gb: float = 7.0,
    threshold_disk_gb: float = 14.0,
    stage: Optional[str] = None
) -> None:
    """
    Log resource usage metrics.
    
    Args:
        memory_gb: Current memory usage in GB
        disk_gb: Current disk usage in GB
        threshold_memory_gb: Memory threshold (default 7.0 GB)
        threshold_disk_gb: Disk threshold (default 14.0 GB)
        stage: Optional processing stage name
    """
    logger = setup_resource_logger()
    
    msg_parts = [
        f"RESOURCE SNAPSHOT",
        f"Memory: {memory_gb:.2f}GB / {threshold_memory_gb}GB",
        f"Disk: {disk_gb:.2f}GB / {threshold_disk_gb}GB"
    ]
    
    if stage:
        msg_parts.insert(1, f"Stage: {stage}")
    
    # Check thresholds
    if memory_gb >= threshold_memory_gb or disk_gb >= threshold_disk_gb:
        msg = " | ".join(msg_parts) + " [WARNING: LIMIT APPROACHED]"
        logger.warning(msg)
    else:
        msg = " | ".join(msg_parts)
        logger.info(msg)

def initialize_project_logging() -> None:
    """
    Initialize all project loggers and create the logs directory.
    
    This should be called once at the start of any script that
    requires logging infrastructure.
    """
    # Ensure logs directory exists
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialize all loggers to populate cache
    setup_general_logger()
    setup_data_flow_logger()
    setup_exclusion_logger()
    setup_resource_logger()
    
    # Log initialization
    logger = setup_general_logger()
    logger.info(f"Logging infrastructure initialized. Logs directory: {LOGS_DIR}")