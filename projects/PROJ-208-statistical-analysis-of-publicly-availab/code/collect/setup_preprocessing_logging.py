"""
Preprocessing logging setup for User Story 1.
Provides a JSON-formatted logger to record excluded issues and preprocessing events.
"""
import logging
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from utils.config import get_config


class JSONFormatter(logging.Formatter):
    """
    Custom logging formatter that outputs records as JSON.
    Includes timestamp, level, message, and optional extra data.
    """
    def format(self, record):
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Include extra fields if present
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)

        return json.dumps(log_data)


def setup_preprocessing_logging(log_path: Optional[Path] = None) -> logging.Logger:
    """
    Configures and returns a logger specifically for preprocessing exclusion logs.
    
    Args:
        log_path: Path to the log file. Defaults to data/logs/preprocessing.log.
    
    Returns:
        A configured logger instance.
    """
    config = get_config()
    if log_path is None:
        log_path = config.get_path("data_logs") / "preprocessing.log"
    
    # Ensure directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger("preprocessing")
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create file handler
    file_handler = logging.FileHandler(log_path, mode='w')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(JSONFormatter())
    
    # Add handler to logger
    logger.addHandler(file_handler)
    
    return logger


def log_excluded_issue(logger: logging.Logger, issue_data: Dict[str, Any], reason: str) -> None:
    """
    Logs a single excluded issue to the preprocessing log.
    
    Args:
        logger: The logger instance.
        issue_data: Dictionary containing issue metadata (id, repo, timestamps, etc.).
        reason: String describing why the issue was excluded (e.g., "negative_resolution_time").
    """
    extra = {
        "issue_id": issue_data.get("id"),
        "repo": issue_data.get("repository"),
        "created_at": issue_data.get("created_at"),
        "closed_at": issue_data.get("closed_at"),
        "exclusion_reason": reason
    }
    logger.info("Issue excluded during preprocessing", extra={"extra_data": extra})


def main() -> None:
    """
    Entry point for testing the logging setup.
    Writes a sample exclusion log entry to verify functionality.
    """
    logger = setup_preprocessing_logging()
    
    # Sample data for testing
    sample_issue = {
        "id": 12345,
        "repository": "test/repo",
        "created_at": "2023-01-01T10:00:00Z",
        "closed_at": "2022-12-31T09:00:00Z"  # Invalid: closed before created
    }
    
    log_excluded_issue(logger, sample_issue, "negative_resolution_time")
    log_excluded_issue(logger, {
        "id": 67890,
        "repository": "test/repo2",
        "created_at": None,
        "closed_at": "2023-01-02T10:00:00Z"
    }, "missing_timestamps")
    
    print(f"Preprocessing log initialized at: {get_config().get_path('data_logs') / 'preprocessing.log'}")


if __name__ == "__main__":
    main()