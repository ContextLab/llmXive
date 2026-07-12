"""
Structured logging utility for the llmXive pipeline.

Provides consistent log formatting, file handlers for pipeline steps,
and JSON-structured output for automated parsing (Constitution Principle IV).
"""
import os
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from config import ensure_directories, PROJECT_ROOT

# Constants
LOG_DIR = PROJECT_ROOT / "logs"
LOG_LEVEL = os.getenv("LLMXIVE_LOG_LEVEL", "INFO").upper()
JSON_LOG_FILE = "pipeline_execution.json"
TEXT_LOG_FILE = "pipeline_execution.log"

# Ensure log directory exists
ensure_directories()
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Global logger instance
_logger: Optional[logging.Logger] = None
_json_handler: Optional[logging.Handler] = None
_text_handler: Optional[logging.Handler] = None


class StructuredFormatter(logging.Formatter):
    """Formats logs as JSON for automated parsing."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "message": record.getMessage(),
        }
        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
        return json.dumps(log_data)


def setup_logging(
    log_level: Optional[str] = None,
    console: bool = True,
    file: bool = True,
    json_format: bool = True,
) -> logging.Logger:
    """
    Configure and return the global pipeline logger.

    Args:
        log_level: Override default log level (e.g., "DEBUG", "INFO").
        console: Whether to log to stdout/stderr.
        file: Whether to log to files in logs/.
        json_format: If True, file logs are JSON; else plain text.

    Returns:
        Configured logger instance.
    """
    global _logger, _json_handler, _text_handler

    if _logger is not None:
        return _logger

    _logger = logging.getLogger("llmXive")
    _logger.setLevel(getattr(logging, log_level or LOG_LEVEL, logging.INFO))
    _logger.propagate = False

    # Clear existing handlers
    _logger.handlers.clear()

    # Console handler
    if console:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        ch.setFormatter(console_formatter)
        _logger.addHandler(ch)

    # File handlers
    if file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        text_path = LOG_DIR / f"{TEXT_LOG_FILE}"
        json_path = LOG_DIR / f"{JSON_LOG_FILE}"

        # Text handler (fallback or readable logs)
        if not json_format or not _text_handler:
            fh_text = logging.FileHandler(text_path, mode='a')
            fh_text.setLevel(logging.DEBUG)
            text_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s"
            )
            fh_text.setFormatter(text_formatter)
            _logger.addHandler(fh_text)

        # JSON handler (for automated parsing)
        if json_format and not _json_handler:
            fh_json = logging.FileHandler(json_path, mode='a')
            fh_json.setLevel(logging.DEBUG)
            fh_json.setFormatter(StructuredFormatter())
            _logger.addHandler(fh_json)

    return _logger


def log_pipeline_step(
    step_name: str,
    status: str,
    details: Optional[Dict[str, Any]] = None,
    level: str = "INFO",
) -> None:
    """
    Log a structured pipeline step event.

    Args:
        step_name: Name of the pipeline step (e.g., "download", "extract").
        status: Status of the step (e.g., "start", "complete", "error").
        details: Optional dictionary of metadata (duration, counts, etc.).
        level: Log level string.
    """
    if _logger is None:
        setup_logging()

    extra = {
        "step": step_name,
        "status": status,
    }
    if details:
        extra.update(details)

    record = _logger.makeRecord(
        _logger.name,
        getattr(logging, level, logging.INFO),
        "",
        0,
        f"Pipeline Step: {step_name} - {status}",
        (),
        None,
        extra={"extra_data": extra}
    )
    _logger.handle(record)


def get_logger() -> logging.Logger:
    """Get the global logger, initializing it if necessary."""
    if _logger is None:
        return setup_logging()
    return _logger


def main():
    """
    Demo entry point to verify logging setup.
    """
    logger = setup_logging(log_level="DEBUG", json_format=True)
    log_pipeline_step("init", "start", {"config": "default"})
    logger.info("This is a standard info message.")
    logger.warning("This is a warning message.")
    log_pipeline_step("init", "complete", {"duration_ms": 150})
    print("Logging demo completed. Check logs/ directory.")


if __name__ == "__main__":
    main()