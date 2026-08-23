"""
Logging utility module for the llmXive research pipeline.

Provides structured logging, edge case flagging, data quality tracking,
and provenance mismatch detection to ensure reproducibility and transparency.
"""

import logging
import sys
from datetime import datetime
from typing import Optional, Any, Dict, List
from pathlib import Path
import json

# Global state for tracking special categories
_edge_cases: List[Dict[str, Any]] = []
_data_quality_issues: List[Dict[str, Any]] = []
_provenance_mismatches: List[Dict[str, Any]] = []
_label_validation_issues: List[Dict[str, Any]] = []

# Default logger configuration
_logger: Optional[logging.Logger] = None
_log_level: int = logging.INFO

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get or create a logger instance.

    Args:
        name: Optional name for the logger. Defaults to 'llmXive'.

    Returns:
        Configured logger instance.
    """
    global _logger
    if _logger is None:
        _logger = logging.getLogger("llmXive")
        _logger.setLevel(_log_level)

        # Remove existing handlers to avoid duplicates
        _logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(_log_level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        _logger.addHandler(console_handler)

    if name:
        return logging.getLogger(f"llmXive.{name}")
    return _logger

def set_log_level(level: int) -> None:
    """
    Set the global log level.

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
    """
    global _log_level, _logger
    _log_level = level
    if _logger:
        _logger.setLevel(level)
        for handler in _logger.handlers:
            handler.setLevel(level)

def setup_logger(log_file: Optional[Path] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Setup logging with optional file output.

    Args:
        log_file: Optional path to write log output.
        level: Logging level.

    Returns:
        Configured logger instance.
    """
    global _logger, _log_level
    _log_level = level
    _logger = logging.getLogger("llmXive")
    _logger.setLevel(level)
    _logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    _logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        _logger.addHandler(file_handler)

    return _logger

def log_info(msg: str, **kwargs) -> None:
    """Log an info message."""
    logger = get_logger(kwargs.get('module'))
    logger.info(msg, **kwargs)

def log_warning(msg: str, **kwargs) -> None:
    """Log a warning message."""
    logger = get_logger(kwargs.get('module'))
    logger.warning(msg, **kwargs)

def log_error(msg: str, **kwargs) -> None:
    """Log an error message."""
    logger = get_logger(kwargs.get('module'))
    logger.error(msg, **kwargs)

def log_critical(msg: str, **kwargs) -> None:
    """Log a critical message."""
    logger = get_logger(kwargs.get('module'))
    logger.critical(msg, **kwargs)

# Edge Case Tracking
def flag_edge_case(category: str, description: str, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Flag an edge case for later reporting.

    Args:
        category: Category of the edge case (e.g., 'missing_label', 'outlier').
        description: Human-readable description of the issue.
        context: Optional dictionary of contextual data.
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "category": category,
        "description": description,
        "context": context or {}
    }
    _edge_cases.append(entry)
    log_warning(f"Edge case flagged [{category}]: {description}")

def get_edge_cases() -> List[Dict[str, Any]]:
    """Get all flagged edge cases."""
    return _edge_cases.copy()

def clear_edge_cases() -> None:
    """Clear all flagged edge cases."""
    _edge_cases.clear()

# Data Quality Tracking
def log_data_quality_issue(issue_type: str, message: str, data_id: Optional[str] = None) -> None:
    """
    Log a data quality issue.

    Args:
        issue_type: Type of quality issue (e.g., 'nan_values', 'missing_provenance').
        message: Description of the issue.
        data_id: Optional identifier for the affected data record.
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "issue_type": issue_type,
        "message": message,
        "data_id": data_id
    }
    _data_quality_issues.append(entry)
    log_warning(f"Data quality issue [{issue_type}]: {message}")

def get_data_quality_issues() -> List[Dict[str, Any]]:
    """Get all logged data quality issues."""
    return _data_quality_issues.copy()

def clear_data_quality_issues() -> None:
    """Clear all logged data quality issues."""
    _data_quality_issues.clear()

# Provenance Mismatch Tracking
def log_provenance_mismatch(record_id: str, expected: str, actual: str, reason: str) -> None:
    """
    Log a provenance mismatch.

    Args:
        record_id: Identifier of the record with mismatched provenance.
        expected: Expected provenance value.
        actual: Actual provenance value found.
        reason: Reason for the mismatch.
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "record_id": record_id,
        "expected": expected,
        "actual": actual,
        "reason": reason
    }
    _provenance_mismatches.append(entry)
    log_warning(f"Provenance mismatch for {record_id}: expected '{expected}', got '{actual}'. Reason: {reason}")

def get_provenance_mismatches() -> List[Dict[str, Any]]:
    """Get all logged provenance mismatches."""
    return _provenance_mismatches.copy()

def clear_provenance_mismatches() -> None:
    """Clear all logged provenance mismatches."""
    _provenance_mismatches.clear()

# Label Validation Tracking
def log_label_validation_issue(record_id: str, label: Any, issue: str) -> None:
    """
    Log a label validation issue.

    Args:
        record_id: Identifier of the record.
        label: The label value that failed validation.
        issue: Description of the validation failure.
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "record_id": record_id,
        "label": str(label),
        "issue": issue
    }
    _label_validation_issues.append(entry)
    log_warning(f"Label validation issue for {record_id}: {issue}")

def get_label_validation_issues() -> List[Dict[str, Any]]:
    """Get all logged label validation issues."""
    return _label_validation_issues.copy()

def clear_label_validation_issues() -> None:
    """Clear all logged label validation issues."""
    _label_validation_issues.clear()

# Report Generation
def generate_edge_case_report(output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Generate a comprehensive report of all tracked issues.

    Args:
        output_path: Optional path to write the JSON report.

    Returns:
        Dictionary containing all tracked issues.
    """
    report = {
        "generated_at": datetime.now().isoformat(),
        "edge_cases": get_edge_cases(),
        "data_quality_issues": get_data_quality_issues(),
        "provenance_mismatches": get_provenance_mismatches(),
        "label_validation_issues": get_label_validation_issues(),
        "summary": {
            "total_edge_cases": len(get_edge_cases()),
            "total_data_quality_issues": len(get_data_quality_issues()),
            "total_provenance_mismatches": len(get_provenance_mismatches()),
            "total_label_validation_issues": len(get_label_validation_issues())
        }
    }

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        log_info(f"Edge case report written to {output_path}")

    return report
