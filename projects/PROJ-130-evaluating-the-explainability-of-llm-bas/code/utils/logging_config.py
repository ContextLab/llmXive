"""
Logging infrastructure configuration for the llmXive research pipeline.

This module sets up a centralized logging system to record edge cases such as:
- Invalid patches
- Generation timeouts
- Missing rationales
- Data loading failures

Logs are written to `state/error_log.json` in JSON Lines format for easy parsing,
and also to the console with appropriate levels.
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .config import ResearchConfig

# Ensure the state directory exists
STATE_DIR = Path(__file__).parent.parent.parent / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

ERROR_LOG_PATH = STATE_DIR / "error_log.json"

# Define error codes as constants for consistency
ERROR_CODES = {
    "INVALID_PATCH": "E001",
    "GENERATION_TIMEOUT": "E002",
    "MISSING_RATIONALE": "E003",
    "DATA_LOAD_FAILURE": "E004",
    "TEST_EXECUTION_FAILURE": "E005",
    "MODEL_LOAD_FAILURE": "E006",
    "INVALID_INPUT": "E007",
    "CONFIGURATION_ERROR": "E008",
}

class EdgeCaseLogger:
    """
    A specialized logger for recording edge cases and errors in the research pipeline.
    Writes structured JSON entries to state/error_log.json and logs to console.
    """

    def __init__(self, log_level: int = logging.INFO):
        self.logger = logging.getLogger("llmXive_edge_cases")
        self.logger.setLevel(log_level)

        # Prevent duplicate handlers if re-initialized
        if not self.logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_format = logging.Formatter(
                "%(asctime)s - %(levelname)s - [%(code)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            console_handler.setFormatter(console_format)
            self.logger.addHandler(console_handler)

        # Ensure JSON log file exists (create if missing)
        if not ERROR_LOG_PATH.exists():
            ERROR_LOG_PATH.touch()

    def _log_to_file(self, entry: Dict[str, Any]) -> None:
        """Append a JSON entry to the error log file."""
        try:
            with open(ERROR_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except IOError as e:
            self.logger.error(f"Failed to write to error log file: {e}", extra={"code": "E008"})

    def log_edge_case(
        self,
        error_code: str,
        message: str,
        bug_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "WARNING"
    ) -> None:
        """
        Log an edge case with structured data.

        Args:
            error_code: One of the defined ERROR_CODES (e.g., 'INVALID_PATCH')
            message: Human-readable description of the issue
            bug_id: Optional bug identifier for context
            details: Optional dictionary of additional context data
            severity: Log level string ('WARNING', 'ERROR', 'CRITICAL')
        """
        timestamp = datetime.utcnow().isoformat()

        # Validate error code
        if error_code not in ERROR_CODES.values():
            # Map common names to codes if passed as name instead of code
            mapped_code = None
            for name, code in ERROR_CODES.items():
                if name == error_code:
                    mapped_code = code
                    break
            if mapped_code:
                error_code = mapped_code
            else:
                error_code = ERROR_CODES["CONFIGURATION_ERROR"]

        entry = {
            "timestamp": timestamp,
            "error_code": error_code,
            "severity": severity,
            "message": message,
            "bug_id": bug_id,
            "details": details or {},
        }

        # Log to console
        log_method = getattr(self.logger, severity.lower(), self.logger.warning)
        log_method(message, extra={"code": error_code})

        # Log to file
        self._log_to_file(entry)

    def log_invalid_patch(self, bug_id: str, reason: str, details: Optional[Dict] = None) -> None:
        """Convenience method for logging invalid patch errors."""
        self.log_edge_case(
            error_code=ERROR_CODES["INVALID_PATCH"],
            message=f"Invalid patch for bug {bug_id}: {reason}",
            bug_id=bug_id,
            details={"reason": reason, **(details or {})}
        )

    def log_timeout(self, bug_id: str, operation: str, timeout_seconds: float) -> None:
        """Convenience method for logging timeout errors."""
        self.log_edge_case(
            error_code=ERROR_CODES["GENERATION_TIMEOUT"],
            message=f"Timeout during {operation} for bug {bug_id}",
            bug_id=bug_id,
            details={"operation": operation, "timeout_seconds": timeout_seconds}
        )

    def log_missing_rationale(self, bug_id: str, expected_path: Optional[str] = None) -> None:
        """Convenience method for logging missing rationale errors."""
        self.log_edge_case(
            error_code=ERROR_CODES["MISSING_RATIONALE"],
            message=f"Missing rationale for bug {bug_id}",
            bug_id=bug_id,
            details={"expected_path": expected_path}
        )

    def log_data_load_failure(self, bug_id: str, reason: str) -> None:
        """Convenience method for logging data load failures."""
        self.log_edge_case(
            error_code=ERROR_CODES["DATA_LOAD_FAILURE"],
            message=f"Failed to load data for bug {bug_id}: {reason}",
            bug_id=bug_id,
            details={"reason": reason}
        )

    def log_test_execution_failure(self, bug_id: str, reason: str) -> None:
        """Convenience method for logging test execution failures."""
        self.log_edge_case(
            error_code=ERROR_CODES["TEST_EXECUTION_FAILURE"],
            message=f"Test execution failed for bug {bug_id}: {reason}",
            bug_id=bug_id,
            details={"reason": reason}
        )

    def get_error_counts(self) -> Dict[str, int]:
        """
        Read the error log and return counts per error code.
        Returns an empty dict if the file is empty or unreadable.
        """
        counts: Dict[str, int] = {code: 0 for code in ERROR_CODES.values()}
        if not ERROR_LOG_PATH.exists():
            return counts

        try:
            with open(ERROR_LOG_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        code = entry.get("error_code")
                        if code and code in counts:
                            counts[code] += 1
                    except json.JSONDecodeError:
                        continue
        except IOError:
            pass

        return counts

# Global logger instance
_edge_logger: Optional[EdgeCaseLogger] = None

def get_edge_logger() -> EdgeCaseLogger:
    """Get the singleton edge case logger instance."""
    global _edge_logger
    if _edge_logger is None:
        _edge_logger = EdgeCaseLogger()
    return _edge_logger

# Convenience functions for direct usage
def log_edge_case(*args, **kwargs) -> None:
    """Log an edge case using the global logger."""
    get_edge_logger().log_edge_case(*args, **kwargs)

def log_invalid_patch(*args, **kwargs) -> None:
    """Log an invalid patch using the global logger."""
    get_edge_logger().log_invalid_patch(*args, **kwargs)

def log_timeout(*args, **kwargs) -> None:
    """Log a timeout using the global logger."""
    get_edge_logger().log_timeout(*args, **kwargs)

def log_missing_rationale(*args, **kwargs) -> None:
    """Log a missing rationale using the global logger."""
    get_edge_logger().log_missing_rationale(*args, **kwargs)

def log_data_load_failure(*args, **kwargs) -> None:
    """Log a data load failure using the global logger."""
    get_edge_logger().log_data_load_failure(*args, **kwargs)

def log_test_execution_failure(*args, **kwargs) -> None:
    """Log a test execution failure using the global logger."""
    get_edge_logger().log_test_execution_failure(*args, **kwargs)

def get_error_counts() -> Dict[str, int]:
    """Get error counts from the log file."""
    return get_edge_logger().get_error_counts()
