"""
Structured logging infrastructure for the A/B test audit pipeline.

Provides error-code formatted logging (ERR-###) as required by FR-007.
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json


# Error code registry
ERROR_CODES: Dict[str, str] = {
    "ERR-001": "Missing required metric in A/B test summary",
    "ERR-002": "Invalid p-value format",
    "ERR-003": "Sample size mismatch between variants",
    "ERR-004": "P-value inconsistency exceeds threshold",
    "ERR-005": "Effect size inconsistency exceeds threshold",
    "ERR-006": "Malformed HTML structure",
    "ERR-007": "Failed to extract domain from URL",
    "ERR-008": "Missing baseline conversion rate",
    "ERR-009": "Inequality p-value detected",
    "ERR-010": "Conflicting sample sizes in summary",
    "ERR-099": "Unknown extraction error",
    "ERR-201": "JSON/CSV count mismatch in export validation",
    "ERR-301": "Resource limits exceeded",
    "ERR-800": "Validation thresholds not met",
    "ERR-801": "Monte-Carlo validation failed",
    "ERR-802": "Real-world validation thresholds not met",
    "ERR-950": "Constitution principle compliance check failed",
}


class AuditLogger:
    """
    Structured logger with error-code support for the audit pipeline.
    
    All error messages include an ERR-### code per FR-007 requirements.
    """
    
    def __init__(
        self,
        name: str = "ab_audit",
        log_file: Optional[Path] = None,
        level: int = logging.INFO,
    ):
        """
        Initialize the audit logger.
        
        Args:
            name: Logger name
            log_file: Optional path to write log file
            level: Logging level (default: INFO)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.handlers = []  # Clear existing handlers
        
        # Console handler with structured format
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_format = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(code)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # Optional file handler
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(console_format)
            self.logger.addHandler(file_handler)
        
        # Store metadata
        self._log_file = log_file
        self._error_counts: Dict[str, int] = {}
    
    def _get_error_message(self, error_code: str) -> str:
        """
        Get human-readable error message for a code.
        
        Args:
            error_code: The ERR-### code
        
        Returns:
            Error message string
        """
        return ERROR_CODES.get(error_code, f"Unknown error: {error_code}")
    
    def _add_error_code_filter(self, error_code: str):
        """
        Add custom attribute to log record for error code formatting.
        
        Args:
            error_code: The ERR-### code
        """
        # This is handled via extra parameter in log methods
        pass
    
    def log_error(self, error_code: str, message: str, **extra: Any) -> None:
        """
        Log an error with a specific error code.
        
        Args:
            error_code: The ERR-### code (e.g., "ERR-001")
            message: Error message description
            **extra: Additional context to include in log
        """
        if error_code not in ERROR_CODES:
            # Register new error code dynamically
            ERROR_CODES[error_code] = message
        
        self._error_counts[error_code] = self._error_counts.get(error_code, 0) + 1
        
        full_message = f"[{error_code}] {message}"
        self.logger.error(full_message, extra={"code": error_code, **extra})
    
    def log_warning(self, message: str, **extra: Any) -> None:
        """
        Log a warning message.
        
        Args:
            message: Warning message
            **extra: Additional context
        """
        self.logger.warning(message, extra={"code": "WARN", **extra})
    
    def log_info(self, message: str, **extra: Any) -> None:
        """
        Log an info message.
        
        Args:
            message: Info message
            **extra: Additional context
        """
        self.logger.info(message, extra={"code": "INFO", **extra})
    
    def log_debug(self, message: str, **extra: Any) -> None:
        """
        Log a debug message.
        
        Args:
            message: Debug message
            **extra: Additional context
        """
        self.logger.debug(message, extra={"code": "DEBUG", **extra})
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get summary of all logged errors.
        
        Returns:
            Dictionary with error codes and their counts
        """
        return dict(self._error_counts)
    
    def validate_error_code(self, error_code: str) -> bool:
        """
        Validate that an error code exists in the registry.
        
        Args:
            error_code: The ERR-### code to validate
        
        Returns:
            True if code is valid, False otherwise
        """
        return error_code in ERROR_CODES


def create_logger(
    name: str = "ab_audit",
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
) -> AuditLogger:
    """
    Factory function to create a configured AuditLogger.
    
    Args:
        name: Logger name
        log_file: Optional path to write log file
        level: Logging level
    
    Returns:
        Configured AuditLogger instance
    """
    return AuditLogger(name=name, log_file=log_file, level=level)


def get_error_message(error_code: str) -> str:
    """
    Get human-readable error message for a code.
    
    Args:
        error_code: The ERR-### code
    
    Returns:
        Error message string
    """
    return ERROR_CODES.get(error_code, f"Unknown error: {error_code}")


def validate_error_code(error_code: str) -> bool:
    """
    Validate that an error code exists in the registry.
    
    Args:
        error_code: The ERR-### code to validate
    
    Returns:
        True if code is valid, False otherwise
    """
    return error_code in ERROR_CODES


# Module-level default logger instance
_default_logger: Optional[AuditLogger] = None


def get_default_logger() -> AuditLogger:
    """
    Get or create the default logger instance.
    
    Returns:
        Default AuditLogger instance
    """
    global _default_logger
    if _default_logger is None:
        _default_logger = AuditLogger()
    return _default_logger
