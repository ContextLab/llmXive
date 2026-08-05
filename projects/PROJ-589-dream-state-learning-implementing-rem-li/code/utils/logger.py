import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from config import Config


class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs."""

    def format(self, record: logging.LogRecord) -> str:
      log_entry = {
          "timestamp": datetime.utcnow().isoformat(),
          "level": record.levelname,
          "message": record.getMessage(),
          "module": record.module,
          "function": record.funcName,
          "line": record.lineno,
      }
      # Add extra fields if present
      if hasattr(record, "extra_data"):
          log_entry.update(record.extra_data)
      return json.dumps(log_entry)


def get_logger(name: str, log_dir: Optional[Path] = None) -> logging.Logger:
  """
  Get a configured logger instance.

  Args:
      name: Logger name (typically __name__)
      log_dir: Directory for log files (defaults to Config.LOGS_DIR)

  Returns:
      Configured logger instance
  """
  logger = logging.getLogger(name)
  if logger.handlers:
      return logger

  logger.setLevel(logging.DEBUG)

  # Create log directory if it doesn't exist
  if log_dir is None:
      log_dir = Config.LOGS_DIR
  log_dir.mkdir(parents=True, exist_ok=True)

  # File handler with JSON formatting
  log_file = log_dir / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
  file_handler = logging.FileHandler(log_file)
  file_handler.setLevel(logging.DEBUG)
  file_handler.setFormatter(JsonFormatter())

  # Console handler for stdout
  console_handler = logging.StreamHandler(sys.stdout)
  console_handler.setLevel(logging.INFO)
  console_handler.setFormatter(logging.Formatter(
      "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  ))

  logger.addHandler(file_handler)
  logger.addHandler(console_handler)

  return logger


def log_event(
    logger: logging.Logger,
    event_type: str,
    message: str,
    extra_data: Optional[Dict[str, Any]] = None
) -> None:
  """
  Log an event with structured data.

  Args:
      logger: Logger instance
      event_type: Type of event (e.g., "PHASE_TRANSITION", "METRIC", "ERROR")
      message: Human-readable message
      extra_data: Additional structured data to include
  """
  if extra_data is None:
      extra_data = {}
  extra_data["event_type"] = event_type

  # Attach extra data to the log record
  record = logger.makeRecord(
      logger.name, logging.INFO, "", 0, message, (), None
  )
  record.extra_data = extra_data
  logger.handle(record)
