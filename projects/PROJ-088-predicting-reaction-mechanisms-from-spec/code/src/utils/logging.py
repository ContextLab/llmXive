"""
Logging and edge case handling utilities for the llmXive research pipeline.

Provides structured logging, edge case flagging, and data quality issue tracking
to ensure reproducibility and transparency in scientific computations.
"""
import logging
import sys
from datetime import datetime
from typing import Optional, Any, Dict, List
from pathlib import Path
import json

# Global storage for tracking issues across the pipeline
_edge_cases: List[Dict[str, Any]] = []
_data_quality_issues: List[Dict[str, Any]] = []
_provenance_mismatches: List[Dict[str, Any]] = []
_label_validation_issues: List[Dict[str, Any]] = []

# Default logger configuration
_default_logger: Optional[logging.Logger] = None
_log_level: int = logging.INFO

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Get or create a named logger with standard formatting.
    
    Args:
        name: Logger name (defaults to 'llmXive')
        
    Returns:
        Configured logger instance
    """
    global _default_logger
    if _default_logger is None:
        _default_logger = logging.getLogger(name)
        _default_logger.setLevel(_log_level)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(_log_level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        _default_logger.addHandler(console_handler)
        
    return logging.getLogger(name)

def set_log_level(level: int) -> None:
    """
    Set the global logging level.
    
    Args:
        level: Logging level (e.g., logging.DEBUG, logging.WARNING)
    """
    global _log_level, _default_logger
    _log_level = level
    if _default_logger:
        _default_logger.setLevel(level)
        for handler in _default_logger.handlers:
            handler.setLevel(level)

def setup_logger(
    name: str = "llmXive",
    log_file: Optional[Path] = None,
    level: int = logging.INFO
) -> logging.Logger:
    """
    Set up a logger with optional file output.
    
    Args:
        name: Logger name
        log_file: Optional path to log file
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger

def log_info(logger: logging.Logger, message: str, **kwargs) -> None:
    """Log an informational message."""
    logger.info(f"[INFO] {message}", extra=kwargs)

def log_warning(logger: logging.Logger, message: str, **kwargs) -> None:
    """Log a warning message."""
    logger.warning(f"[WARNING] {message}", extra=kwargs)

def log_error(logger: logging.Logger, message: str, **kwargs) -> None:
    """Log an error message."""
    logger.error(f"[ERROR] {message}", extra=kwargs)

def log_critical(logger: logging.Logger, message: str, **kwargs) -> None:
    """Log a critical message."""
    logger.critical(f"[CRITICAL] {message}", extra=kwargs)

def flag_edge_case(
    category: str,
    description: str,
    context: Optional[Dict[str, Any]] = None,
    severity: str = "medium"
) -> None:
    """
    Flag an edge case encountered during processing.
    
    Args:
        category: Category of edge case (e.g., 'data_missing', 'outlier', 'boundary')
        description: Human-readable description
        context: Additional context data
        severity: Severity level ('low', 'medium', 'high', 'critical')
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "category": category,
        "description": description,
        "severity": severity,
        "context": context or {}
    }
    _edge_cases.append(entry)

def get_edge_cases() -> List[Dict[str, Any]]:
    """Get all recorded edge cases."""
    return _edge_cases.copy()

def clear_edge_cases() -> None:
    """Clear all recorded edge cases."""
    _edge_cases.clear()

def log_data_quality_issue(
    source: str,
    issue_type: str,
    message: str,
    affected_rows: Optional[int] = None,
    recommendation: Optional[str] = None
) -> None:
    """
    Log a data quality issue detected during ingestion or preprocessing.
    
    Args:
        source: Data source where issue was found
        issue_type: Type of issue (e.g., 'missing_values', 'invalid_range', 'inconsistent_format')
        message: Description of the issue
        affected_rows: Number of rows affected
        recommendation: Suggested remediation
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "source": source,
        "issue_type": issue_type,
        "message": message,
        "affected_rows": affected_rows,
        "recommendation": recommendation
    }
    _data_quality_issues.append(entry)
    log_warning(logging.getLogger("llmXive"), f"Data Quality Issue in {source}: {message}")

def get_data_quality_issues() -> List[Dict[str, Any]]:
    """Get all recorded data quality issues."""
    return _data_quality_issues.copy()

def clear_data_quality_issues() -> None:
    """Clear all recorded data quality issues."""
    _data_quality_issues.clear()

def log_provenance_mismatch(
    row_id: Any,
    expected_provenance: str,
    actual_provenance: str,
    action_taken: str
) -> None:
    """
    Log a provenance mismatch where data did not meet inclusion criteria.
    
    Args:
        row_id: Identifier of the row
        expected_provenance: Expected provenance type
        actual_provenance: Actual provenance found
        action_taken: Action taken (e.g., 'excluded', 'flagged')
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "row_id": str(row_id),
        "expected_provenance": expected_provenance,
        "actual_provenance": actual_provenance,
        "action_taken": action_taken
    }
    _provenance_mismatches.append(entry)
    log_warning(
        logging.getLogger("llmXive"),
        f"Provenance mismatch for row {row_id}: expected '{expected_provenance}', "
        f"found '{actual_provenance}'. Action: {action_taken}"
    )

def get_provenance_mismatches() -> List[Dict[str, Any]]:
    """Get all recorded provenance mismatches."""
    return _provenance_mismatches.copy()

def clear_provenance_mismatches() -> None:
    """Clear all recorded provenance mismatches."""
    _provenance_mismatches.clear()

def log_label_validation_issue(
    sample_id: Any,
    label: Optional[str],
    reason: str,
    validation_type: str = "label_check"
) -> None:
    """
    Log an issue with label validation.
    
    Args:
        sample_id: Identifier of the sample
        label: The label value (or None if missing)
        reason: Reason for the validation issue
        validation_type: Type of validation performed
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "sample_id": str(sample_id),
        "label": label,
        "reason": reason,
        "validation_type": validation_type
    }
    _label_validation_issues.append(entry)
    log_warning(
        logging.getLogger("llmXive"),
        f"Label validation issue for sample {sample_id}: {reason}"
    )

def get_label_validation_issues() -> List[Dict[str, Any]]:
    """Get all recorded label validation issues."""
    return _label_validation_issues.copy()

def clear_label_validation_issues() -> None:
    """Clear all recorded label validation issues."""
    _label_validation_issues.clear()

def generate_edge_case_report(output_path: Optional[Path] = None) -> Optional[Path]:
    """
    Generate a comprehensive JSON report of all tracked issues.
    
    Args:
        output_path: Optional path to write the report. If None, returns the dict.
        
    Returns:
        Path to the generated report file, or the report dict if no path provided.
    """
    report = {
        "generated_at": datetime.now().isoformat(),
        "edge_cases": _edge_cases,
        "data_quality_issues": _data_quality_issues,
        "provenance_mismatches": _provenance_mismatches,
        "label_validation_issues": _label_validation_issues,
        "summary": {
            "total_edge_cases": len(_edge_cases),
            "total_data_quality_issues": len(_data_quality_issues),
            "total_provenance_mismatches": len(_provenance_mismatches),
            "total_label_validation_issues": len(_label_validation_issues)
        }
    }
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        return output_path
    
    return report