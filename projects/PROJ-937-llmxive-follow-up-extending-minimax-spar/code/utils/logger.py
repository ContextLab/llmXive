"""
Structured logging and resource monitoring for llmXive.

Provides:
- StructuredFormatter: JSON-formatted log output.
- ResourceMonitor: Background thread tracking RAM/CPU usage.
- Factory functions for task-specific and global loggers.
"""

import json
import logging
import os
import platform
import sys
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

# Optional import for resource monitoring (Unix/Linux/macOS)
try:
    import resource
    HAS_RESOURCE = True
except ImportError:
    HAS_RESOURCE = False
    resource = None  # type: ignore

# Optional import for psutil (cross-platform, more accurate on Windows)
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    psutil = None  # type: ignore

from utils.config import get_default_config

# Constants
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FILE = "data/logs/run.log"
DEFAULT_MONITOR_INTERVAL = 5.0  # seconds

# Global state for loggers
_global_logger: Optional[logging.Logger] = None
_monitor_thread: Optional[threading.Thread] = None
_monitor_stop_event: Optional[threading.Event] = None


class StructuredFormatter(logging.Formatter):
    """
    A logging formatter that outputs JSON-structured logs.
    Includes timestamp, level, logger name, message, and optional extra fields.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "platform": platform.system(),
            "python_version": platform.python_version(),
        }

        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


class ResourceMonitor:
    """
    Background thread that periodically logs memory and CPU usage.
    Uses psutil if available, otherwise falls back to resource module (Unix only).
    """

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        interval: float = DEFAULT_MONITOR_INTERVAL,
        log_level: int = logging.INFO,
        output_path: Optional[str] = None,
    ):
        self.logger = logger or get_global_logger()
        self.interval = interval
        self.log_level = log_level
        self.output_path = output_path or DEFAULT_LOG_FILE
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._snapshots: List[Dict[str, Any]] = []

    def start(self) -> None:
        """Start the monitoring thread."""
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self.logger.info("ResourceMonitor started", extra={"extra_data": {"interval": self.interval}})

    def stop(self, timeout: float = 2.0) -> None:
        """Stop the monitoring thread."""
        if not self._thread:
            return

        self._stop_event.set()
        self._thread.join(timeout=timeout)
        self.logger.info("ResourceMonitor stopped")
        self._thread = None

    def _run(self) -> None:
        """Main loop for the monitoring thread."""
        while not self._stop_event.is_set():
            try:
                snapshot = self._get_snapshot()
                self._snapshots.append(snapshot)
                self.logger.log(
                    self.log_level,
                    "Resource snapshot",
                    extra={"extra_data": snapshot},
                )
            except Exception as e:
                self.logger.error(f"Error capturing resource snapshot: {e}", exc_info=True)

            self._stop_event.wait(self.interval)

    def _get_snapshot(self) -> Dict[str, Any]:
        """Capture current memory and CPU usage."""
        snapshot: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "pid": os.getpid(),
        }

        if HAS_PSUTIL and psutil:
            process = psutil.Process(os.getpid())
            mem_info = process.memory_info()
            snapshot["memory_rss_mb"] = mem_info.rss / (1024 * 1024)
            snapshot["memory_vms_mb"] = mem_info.vms / (1024 * 1024)
            snapshot["cpu_percent"] = process.cpu_percent(interval=0)
            snapshot["total_memory_mb"] = psutil.virtual_memory().total / (1024 * 1024)
            snapshot["available_memory_mb"] = psutil.virtual_memory().available / (1024 * 1024)
        elif HAS_RESOURCE and resource:
            # Unix fallback
            rusage = resource.getrusage(resource.RUSAGE_SELF)
            snapshot["memory_max_mb"] = rusage.ru_maxrss / 1024  # kB to MB on Linux
            snapshot["user_cpu_time"] = rusage.ru_utime
            snapshot["system_cpu_time"] = rusage.ru_stime
            # Note: resource module doesn't provide current CPU% easily
            snapshot["cpu_percent"] = None
        else:
            snapshot["error"] = "No resource monitoring library available (psutil or resource)"
            snapshot["cpu_percent"] = None

        return snapshot

    def get_snapshots(self) -> List[Dict[str, Any]]:
        """Return all collected snapshots."""
        return self._snapshots.copy()


def setup_logger(
    name: str,
    level: int = DEFAULT_LOG_LEVEL,
    log_file: Optional[str] = None,
    use_json: bool = True,
) -> logging.Logger:
    """
    Set up a logger with optional file handler and structured formatting.

    Args:
        name: Logger name (usually __name__).
        level: Logging level.
        log_file: Path to log file. If None, only console output.
        use_json: If True, use StructuredFormatter; else use standard format.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if logger.handlers:
        logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    if use_json:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )

    logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(StructuredFormatter() if use_json else logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
        logger.addHandler(file_handler)

    return logger


def get_structured_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = DEFAULT_LOG_LEVEL,
) -> logging.Logger:
    """
    Get a structured (JSON) logger for a specific component.

    Args:
        name: Logger name.
        log_file: Optional log file path.
        level: Logging level.

    Returns:
        Configured logger.
    """
    return setup_logger(name, level=level, log_file=log_file, use_json=True)


def get_logger_for_task(
    task_name: str,
    run_id: Optional[str] = None,
    level: int = DEFAULT_LOG_LEVEL,
) -> logging.Logger:
    """
    Get a logger for a specific task run, with file output.

    Args:
        task_name: Name of the task (e.g., "T005").
        run_id: Optional run identifier.
        level: Logging level.

    Returns:
        Configured logger.
    """
    # Build log path
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    if run_id:
        log_file = log_dir / f"{task_name}_{run_id}.log"
    else:
        log_file = log_dir / f"{task_name}.log"

    return setup_logger(
        name=f"llmxive.{task_name}",
        level=level,
        log_file=str(log_file),
        use_json=True,
    )


def get_global_logger() -> logging.Logger:
    """
    Get or create the global project logger.

    Returns:
        Global logger instance.
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = setup_logger(
            name="llmxive.global",
            level=DEFAULT_LOG_LEVEL,
            log_file=DEFAULT_LOG_FILE,
            use_json=True,
        )
    return _global_logger


def get_current_resource_snapshot() -> Dict[str, Any]:
    """
    Get a one-off resource snapshot (synchronous).

    Returns:
        Dictionary with current memory and CPU stats.
    """
    monitor = ResourceMonitor(logger=get_global_logger())
    return monitor._get_snapshot()


def log_resource_usage(
    logger: Optional[logging.Logger] = None,
    message: str = "Resource usage",
) -> Dict[str, Any]:
    """
    Log a one-off resource snapshot.

    Args:
        logger: Logger to use.
        message: Log message.

    Returns:
        Snapshot dictionary.
    """
    logger = logger or get_global_logger()
    snapshot = get_current_resource_snapshot()
    logger.info(message, extra={"extra_data": snapshot})
    return snapshot