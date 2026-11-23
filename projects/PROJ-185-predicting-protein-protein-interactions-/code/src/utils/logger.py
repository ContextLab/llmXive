"""
src.utils.logger
-----------------

Central logging utility for the pipeline.

Provides a JSON‑Line formatter that emits the required fields:
- ``timestamp``: ISO‑8601 UTC timestamp
- ``level``: logging level name (e.g. INFO, ERROR)
- ``message``: the logged message
- ``schema_version``: version identifier for the log schema
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

__all__ = [
    "JSONFormatter",
    "get_logger",
    "log_cli_invocation",
    "log_error",
]


class JSONFormatter(logging.Formatter):
    """
    Formatter that outputs a JSON object per log record (JSON‑Line).

    The output dictionary always contains the four fields required by
    ``contracts/pipeline_log.schema.yaml``:

    - ``timestamp`` – ISO‑8601 string in UTC
    - ``level`` – the logging level name
    - ``message`` – the rendered log message
    - ``schema_version`` – static string (currently ``\"1.0\"``)
    """

    def __init__(self, *, schema_version: str = "1.0"):
        super().__init__()
        self.schema_version = schema_version

    def format(self, record: logging.LogRecord) -> str:
        # Ensure the message is rendered (handles % formatting etc.)
        message = record.getMessage()
        timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()

        log_entry = {
            "timestamp": timestamp,
            "level": record.levelname,
            "message": message,
            "schema_version": self.schema_version,
        }

        # ``json.dumps`` guarantees a single line output.
        return json.dumps(log_entry)


def _ensure_log_directory(log_path: Path) -> None:
    """
    Guarantee that the parent directory of ``log_path`` exists.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)


def get_logger(
    name: str = "pipeline",
    *,
    log_path: Optional[Path] = None,
    level: int = logging.DEBUG,
) -> logging.Logger:
    """
    Return a configured logger instance.

    Parameters
    ----------
    name: str
        Logger name (defaults to ``\"pipeline\"``).
    log_path: pathlib.Path | None
        Destination for the log file.  If ``None`` a default location
        ``results/pipeline.log`` relative to the project root is used.
    level: int
        Logging level for the logger (default: ``logging.DEBUG``).

    The function is idempotent – calling it multiple times with the same
    ``log_path`` will not attach duplicate handlers.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Resolve the log file location.
    if log_path is None:
        # Project‑root relative path.  ``Path(__file__)`` points inside
        # ``src/utils``; we ascend to the repository root.
        project_root = Path(__file__).resolve().parents[3]
        log_path = project_root / "results" / "pipeline.log"

    _ensure_log_directory(log_path)

    # Attach a FileHandler only once.
    if not any(
        isinstance(h, logging.FileHandler) and Path(h.baseFilename) == log_path
        for h in logger.handlers
    ):
        file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)

    return logger


def log_cli_invocation(args: dict) -> None:
    """
    Convenience helper to log the command‑line invocation.

    ``args`` should be a mapping of the CLI arguments (e.g. the result of
    ``vars(parsed_namespace)``).  The function logs at *INFO* level with a
    fixed message prefix.
    """
    logger = get_logger()
    logger.info("CLI invoked", extra={"cli_args": args})


def log_error(message: str) -> None:
    """
    Log an error message at *ERROR* level.

    This helper mirrors the style used throughout the pipeline – a plain
    message is sufficient; additional context can be added via the
    ``extra`` argument if needed.
    """
    logger = get_logger()
    logger.error(message)
