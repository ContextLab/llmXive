"""
Structured logging infrastructure for the A/B Test Validity Audit pipeline.

Provides a centralized logger that outputs structured logs with standardized
error codes (ERR-###) as required by FR-007 and Constitution Principle VII.
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json

# Error code definitions (FR-007)
ERROR_CODES = {
    # Extraction errors (ERR-001 to ERR-099)
    "ERR-001": "Missing required metric field in A/B test summary",
    "ERR-002": "Malformed HTML structure preventing extraction",
    "ERR-003": "Inequality p-value format not supported",
    "ERR-004": "Conflicting sample sizes detected",
    "ERR-005": "Missing baseline conversion rate",
    "ERR-006": "Invalid numerical value in extracted field",
    "ERR-007": "Unsupported test type detected",
    "ERR-008": "Timeout during HTML fetch",
    "ERR-009": "HTTP error during URL fetch",
    "ERR-010": "URL format validation failed",
    
    # Validation errors (ERR-100 to ERR-199)
    "ERR-101": "P-value inconsistency exceeds threshold (|Δp| > 0.05)",
    "ERR-102": "Effect size inconsistency exceeds threshold (> 5%)",
    "ERR-103": "Sample size mismatch detected",
    "ERR-104": "Statistical reconstruction failed",
    "ERR-105": "Invalid audit record schema",
    
    # Export errors (ERR-200 to ERR-299)
    "ERR-201": "Export count mismatch between JSON and CSV",
    "ERR-202": "Manifest generation failed",
    "ERR-203": "Schema validation failed for export",
    
    # Resource errors (ERR-300 to ERR-399)
    "ERR-301": "Resource limit exceeded (RAM/CPU)",
    "ERR-302": "Timeout during pipeline execution",
    
    # Evaluation errors (ERR-800 to ERR-899)
    "ERR-800": "Synthetic validation thresholds not met",
    "ERR-801": "Real-world validation thresholds not met",
    "ERR-802": "Extraction accuracy below threshold",
    
    # Generic errors
    "ERR-950": "Constitution principle violation",
    "ERR-999": "Unknown system error",
}

class AuditLogger:
    """
    Structured logger that outputs logs with error codes and metadata.
    
    This logger ensures all error messages follow the ERR-### format
    as required by FR-007.
    """
    
    def __init__(
        self,
        name: str = "audit",
        log_file: Optional[Path] = None,
        level: int = logging.INFO
    ):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.handlers = []  # Clear existing handlers
        
        # Console handler with structured format
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler if log_file specified
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(name)s | %(error_code)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
        
        self._log_file = log_file
    
    def _format_message(self, message: str, error_code: Optional[str] = None) -> Dict[str, Any]:
        """Format log message with error code if provided."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "INFO",
            "message": message,
        }
        if error_code:
            log_entry["error_code"] = error_code
            log_entry["error_description"] = ERROR_CODES.get(error_code, "Unknown error")
        return log_entry
    
    def info(self, message: str):
        """Log informational message."""
        self.logger.info(message)
    
    def debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)
    
    def warning(self, message: str):
        """Log warning message."""
        self.logger.warning(message)
    
    def error(self, message: str, error_code: str):
        """
        Log error message with standardized error code.
        
        Args:
            message: Error description
            error_code: Standardized error code (ERR-###)
        """
        if error_code not in ERROR_CODES:
            raise ValueError(f"Unknown error code: {error_code}. Use one of: {list(ERROR_CODES.keys())}")
        
        formatted_msg = f"[{error_code}] {message}"
        self.logger.error(formatted_msg, extra={"error_code": error_code})
    
    def critical(self, message: str, error_code: str):
        """
        Log critical error message with standardized error code.
        
        Args:
            message: Error description
            error_code: Standardized error code (ERR-###)
        """
        if error_code not in ERROR_CODES:
            raise ValueError(f"Unknown error code: {error_code}. Use one of: {list(ERROR_CODES.keys())}")
        
        formatted_msg = f"[{error_code}] {message}"
        self.logger.critical(formatted_msg, extra={"error_code": error_code})
    
    def log_validation_error(self, record_id: str, error_code: str, details: str):
        """
        Log a validation error with record context.
        
        Args:
            record_id: The audit record identifier
            error_code: Standardized error code
            details: Additional context about the error
        """
        message = f"Record {record_id}: {details}"
        self.error(message, error_code)
    
    def log_extraction_error(self, url: str, error_code: str, field: str):
        """
        Log an extraction error with URL context.
        
        Args:
            url: The source URL
            error_code: Standardized error code
            field: The field that failed extraction
        """
        message = f"URL {url}: Failed to extract '{field}'"
        self.error(message, error_code)
    
    def log_resource_error(self, resource_type: str, limit: float, current: float, error_code: str):
        """
        Log a resource limit error.
        
        Args:
            resource_type: Type of resource (RAM, CPU, etc.)
            limit: The configured limit
            current: The current usage
            error_code: Standardized error code
        """
        message = f"{resource_type} limit exceeded: {current:.2f} > {limit:.2f}"
        self.critical(message, error_code)
    
    def get_error_message(self, error_code: str) -> str:
        """
        Get the human-readable description for an error code.
        
        Args:
            error_code: Standardized error code
        
        Returns:
            Human-readable error description
        """
        return ERROR_CODES.get(error_code, "Unknown error code")
    
    def get_all_error_codes(self) -> Dict[str, str]:
        """
        Get all registered error codes and their descriptions.
        
        Returns:
            Dictionary mapping error codes to descriptions
        """
        return ERROR_CODES.copy()
    
    def set_level(self, level: int):
        """Set the logging level."""
        self.logger.setLevel(level)
        for handler in self.logger.handlers:
            handler.setLevel(level)


# Global logger instance
_default_logger: Optional[AuditLogger] = None


def get_default_logger(
    log_file: Optional[Path] = None,
    level: int = logging.INFO
) -> AuditLogger:
    """
    Get or create the default audit logger instance.
    
    Args:
        log_file: Optional path to write logs to
        level: Logging level (default: INFO)
    
    Returns:
        AuditLogger instance
    """
    global _default_logger
    if _default_logger is None:
        _default_logger = AuditLogger(log_file=log_file, level=level)
    return _default_logger


def get_error_message(error_code: str) -> str:
    """
    Convenience function to get error message for a code.
    
    Args:
        error_code: Standardized error code
    
    Returns:
        Human-readable error description
    """
    return ERROR_CODES.get(error_code, "Unknown error code")


def validate_error_code(error_code: str) -> bool:
    """
    Validate that an error code is registered.
    
    Args:
        error_code: Error code to validate
    
    Returns:
        True if valid, False otherwise
    """
    return error_code in ERROR_CODES


def main():
    """
    Demonstrate the logger functionality and verify error code format.
    
    This function writes sample logs to data/logs/logger_test.log to verify
    the ERR-### format is correctly applied.
    """
    from pathlib import Path
    
    # Ensure data/logs directory exists
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "logger_test.log"
    
    # Create logger
    logger = get_default_logger(log_file=log_file, level=logging.DEBUG)
    
    # Log various error types with codes
    logger.info("Starting structured logging verification")
    logger.debug("Debug message without error code")
    logger.warning("Warning message")
    
    # Log extraction errors
    logger.log_extraction_error("https://example.com/ab-test", "ERR-001", "p_value")
    logger.log_extraction_error("https://example.com/ab-test", "ERR-002", "html_structure")
    
    # Log validation errors
    logger.log_validation_error("record_123", "ERR-101", "P-value inconsistency detected")
    logger.log_validation_error("record_456", "ERR-103", "Sample size mismatch")
    
    # Log resource error
    logger.log_resource_error("RAM", 2048.0, 2100.5, "ERR-301")
    
    # Log critical error
    logger.critical("Constitution principle violation detected", "ERR-950")
    
    # Verify error codes
    logger.info(f"Total registered error codes: {len(ERROR_CODES)}")
    logger.info(f"Sample error codes: {list(ERROR_CODES.keys())[:5]}")
    
    logger.info("Structured logging verification complete")
    
    # Print summary
    print(f"\nLogs written to: {log_file.absolute()}")
    print(f"Error codes registered: {len(ERROR_CODES)}")
    print("Sample log entries:")
    with open(log_file, 'r') as f:
        for i, line in enumerate(f):
            if i < 5:
                print(f"  {line.strip()}")
            else:
                break
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
