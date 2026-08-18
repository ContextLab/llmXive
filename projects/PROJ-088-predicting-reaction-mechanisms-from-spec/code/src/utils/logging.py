"""
Logging utilities for the llmXive research pipeline.

Provides standardized logging functions, edge case flagging, and data quality
monitoring to ensure reproducibility and traceability of research results.
"""

import logging
import sys
from datetime import datetime
from typing import Optional, Any, Dict, List
from pathlib import Path

# Global logger instance
_logger: Optional[logging.Logger] = None
_log_level: int = logging.INFO
_edge_cases: List[Dict[str, Any]] = []
_data_quality_issues: List[Dict[str, Any]] = []
_provenance_mismatches: List[Dict[str, Any]] = []
_label_validation_issues: List[Dict[str, Any]] = []

# Edge case categories for structured tracking
EDGE_CASE_CATEGORIES = {
    "missing_data": "Missing or incomplete data entries",
    "outliers": "Statistical outliers detected",
    "provenance_mismatch": "Provenance metadata inconsistency",
    "label_validation": "Label validation failures",
    "class_imbalance": "Class distribution imbalance",
    "data_quality": "General data quality issues",
    "configuration": "Configuration or setup warnings",
    "performance": "Performance or resource warnings"
}

def get_logger() -> logging.Logger:
    """
    Get or create the global logger instance.
    
    Returns:
        logging.Logger: The configured logger instance
    """
    global _logger
    if _logger is None:
        _logger = logging.getLogger("llmXive")
        _logger.setLevel(_log_level)
        
        # Create console handler if none exists
        if not _logger.handlers:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(_log_level)
            
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            _logger.addHandler(console_handler)
    
    return _logger

def set_log_level(level: int) -> None:
    """
    Set the global logging level.
    
    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO, logging.WARNING)
    """
    global _log_level, _logger
    _log_level = level
    if _logger is not None:
        _logger.setLevel(level)
        for handler in _logger.handlers:
            handler.setLevel(level)

def setup_logger(
    name: str = "llmXive",
    log_file: Optional[Union[str, Path]] = None,
    level: int = logging.INFO
) -> logging.Logger:
    """
    Setup and configure the logger with optional file output.
    
    Args:
        name: Logger name
        log_file: Optional path to log file
        level: Logging level
    
    Returns:
        logging.Logger: Configured logger instance
    """
    global _logger, _log_level
    
    _log_level = level
    _logger = logging.getLogger(name)
    _logger.setLevel(level)
    
    # Clear existing handlers
    _logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    _logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        _logger.addHandler(file_handler)
    
    return _logger

def log_warning(message: str, category: Optional[str] = None, **kwargs: Any) -> None:
    """
    Log a warning message with optional category.
    
    Args:
        message: Warning message
        category: Optional category for categorization
        **kwargs: Additional metadata to include
    """
    logger = get_logger()
    if category:
        message = f"[{category}] {message}"
    logger.warning(message)
    
    # Track in data quality issues if needed
    if category in ["data_quality", "outliers", "class_imbalance"]:
        _data_quality_issues.append({
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "category": category,
            **kwargs
        })

def log_error(message: str, **kwargs: Any) -> None:
    """
    Log an error message.
    
    Args:
        message: Error message
        **kwargs: Additional metadata
    """
    logger = get_logger()
    logger.error(message)

def log_critical(message: str, **kwargs: Any) -> None:
    """
    Log a critical error message.
    
    Args:
        message: Critical error message
        **kwargs: Additional metadata
    """
    logger = get_logger()
    logger.critical(message)

def log_info(message: str, **kwargs: Any) -> None:
    """
    Log an informational message.
    
    Args:
        message: Info message
        **kwargs: Additional metadata
    """
    logger = get_logger()
    logger.info(message)

def flag_edge_case(
    category: str,
    description: str,
    data_context: Optional[Dict[str, Any]] = None,
    severity: str = "warning"
) -> None:
    """
    Flag an edge case for later review and analysis.
    
    Args:
        category: Edge case category (must be in EDGE_CASE_CATEGORIES)
        description: Description of the edge case
        data_context: Optional context about the data where this occurred
        severity: Severity level ("warning", "error", "critical")
    """
    if category not in EDGE_CASE_CATEGORIES:
        raise ValueError(f"Invalid edge case category: {category}. "
                       f"Valid categories: {list(EDGE_CASE_CATEGORIES.keys())}")
    
    edge_case = {
        "timestamp": datetime.now().isoformat(),
        "category": category,
        "category_description": EDGE_CASE_CATEGORIES[category],
        "description": description,
        "data_context": data_context or {},
        "severity": severity
    }
    
    _edge_cases.append(edge_case)
    
    # Log based on severity
    logger = get_logger()
    log_message = f"[EDGE CASE] [{category}] {description}"
    
    if severity == "critical":
        logger.critical(log_message)
    elif severity == "error":
        logger.error(log_message)
    else:
        logger.warning(log_message)

def log_data_quality_issue(
    issue_type: str,
    description: str,
    affected_records: Optional[int] = None,
    severity: str = "warning"
) -> None:
    """
    Log a data quality issue with structured metadata.
    
    Args:
        issue_type: Type of data quality issue
        description: Description of the issue
        affected_records: Number of affected records
        severity: Severity level
    """
    issue = {
        "timestamp": datetime.now().isoformat(),
        "issue_type": issue_type,
        "description": description,
        "affected_records": affected_records,
        "severity": severity
    }
    
    _data_quality_issues.append(issue)
    
    logger = get_logger()
    log_message = f"[DATA QUALITY] [{issue_type}] {description}"
    if affected_records:
        log_message += f" (affecting {affected_records} records)"
    
    if severity == "critical":
        logger.critical(log_message)
    elif severity == "error":
        logger.error(log_message)
    else:
        logger.warning(log_message)

def log_label_validation_issue(
    label: str,
    issue: str,
    sample_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an issue with label validation.
    
    Args:
        label: The problematic label
        issue: Description of the validation issue
        sample_id: Optional sample identifier
        context: Additional context
    """
    issue_record = {
        "timestamp": datetime.now().isoformat(),
        "label": label,
        "issue": issue,
        "sample_id": sample_id,
        "context": context or {}
    }
    
    _label_validation_issues.append(issue_record)
    
    logger = get_logger()
    msg = f"[LABEL VALIDATION] Label '{label}': {issue}"
    if sample_id:
        msg += f" (sample: {sample_id})"
    logger.warning(msg)

def log_provenance_mismatch(
    expected: str,
    actual: str,
    source: str,
    record_id: Optional[str] = None
) -> None:
    """
    Log a provenance metadata mismatch.
    
    Args:
        expected: Expected provenance value
        actual: Actual provenance value found
        source: Data source where mismatch occurred
        record_id: Optional record identifier
    """
    mismatch = {
        "timestamp": datetime.now().isoformat(),
        "expected": expected,
        "actual": actual,
        "source": source,
        "record_id": record_id
    }
    
    _provenance_mismatches.append(mismatch)
    
    logger = get_logger()
    msg = f"[PROVENANCE MISMATCH] Expected '{expected}', got '{actual}' from {source}"
    if record_id:
        msg += f" (record: {record_id})"
    logger.warning(msg)

def get_edge_cases() -> List[Dict[str, Any]]:
    """
    Get all flagged edge cases.
    
    Returns:
        List of edge case dictionaries
    """
    return _edge_cases.copy()

def get_data_quality_issues() -> List[Dict[str, Any]]:
    """
    Get all logged data quality issues.
    
    Returns:
        List of data quality issue dictionaries
    """
    return _data_quality_issues.copy()

def get_provenance_mismatches() -> List[Dict[str, Any]]:
    """
    Get all logged provenance mismatches.
    
    Returns:
        List of provenance mismatch dictionaries
    """
    return _provenance_mismatches.copy()

def get_label_validation_issues() -> List[Dict[str, Any]]:
    """
    Get all label validation issues.
    
    Returns:
        List of label validation issue dictionaries
    """
    return _label_validation_issues.copy()

def clear_edge_cases() -> None:
    """Clear all flagged edge cases."""
    global _edge_cases
    _edge_cases.clear()

def clear_data_quality_issues() -> None:
    """Clear all data quality issues."""
    global _data_quality_issues
    _data_quality_issues.clear()

def clear_provenance_mismatches() -> None:
    """Clear all provenance mismatches."""
    global _provenance_mismatches
    _provenance_mismatches.clear()

def clear_label_validation_issues() -> None:
    """Clear all label validation issues."""
    global _label_validation_issues
    _label_validation_issues.clear()

def generate_edge_case_report() -> Dict[str, Any]:
    """
    Generate a summary report of all edge cases and issues.
    
    Returns:
        Dictionary containing summary statistics and details
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "edge_cases": {
            "total": len(_edge_cases),
            "by_category": {
                cat: sum(1 for ec in _edge_cases if ec["category"] == cat)
                for cat in EDGE_CASE_CATEGORIES.keys()
            },
            "details": _edge_cases
        },
        "data_quality_issues": {
            "total": len(_data_quality_issues),
            "details": _data_quality_issues
        },
        "provenance_mismatches": {
            "total": len(_provenance_mismatches),
            "details": _provenance_mismatches
        },
        "label_validation_issues": {
            "total": len(_label_validation_issues),
            "details": _label_validation_issues
        }
    }

# Initialize logger on module import
get_logger()
