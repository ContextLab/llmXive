import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Any

from utils.config import get_logs_path

# ----------------------------------------------------------------------
# Internal singleton logger instance
# ----------------------------------------------------------------------
_logger_instance: Optional[logging.Logger] = None
_log_file_path: Optional[Path] = None

def _configure_logger(name: str = "llmXive_pipeline") -> logging.Logger:
    """
    Configure a logger with a file handler (timestamped) and a console handler.
    The logger uses DEBUG level and a pipe‑separated format that matches the
    expectations of the unit tests in ``test_logging.py``.
    """
    global _logger_instance, _log_file_path

    logger = logging.getLogger(name)
    if logger.handlers:
        # Already configured
        return logger

    logger.setLevel(logging.DEBUG)

    # Ensure logs directory exists
    logs_dir = get_logs_path()
    logs_dir.mkdir(parents=True, exist_ok=True)

    # File handler with timestamped filename
    log_file = logs_dir / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    # Pipe‑separated formatter that includes timestamp, logger name, level and message
    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Store references for helper functions
    _logger_instance = logger
    _log_file_path = log_file

    return logger

def get_pipeline_logger(name: str = "llmXive_pipeline") -> logging.Logger:
    """
    Retrieve the singleton pipeline logger, creating it if necessary.
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = _configure_logger(name)
    return _logger_instance

def get_log_file_path(logger: Optional[logging.Logger] = None) -> Optional[Path]:
    """
    Return the Path object of the log file associated with the given logger.
    If ``logger`` is ``None`` the default pipeline logger is used.
    """
    if logger is None:
        logger = get_pipeline_logger()
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            return Path(handler.baseFilename)
    return None

# ----------------------------------------------------------------------
# Logging helper functions matching the test suite API
# ----------------------------------------------------------------------
def log_pipeline_start(config: Optional[dict] = None) -> None:
    """
    Log the start of a pipeline execution.  The test suite checks that the
    message contains the words ``PIPELINE EXECUTION STARTED`` and that any
    configuration dictionary is rendered.
    """
    logger = get_pipeline_logger()
    logger.info("PIPELINE EXECUTION STARTED")
    if config:
        logger.info(f"Configuration: {config}")

def log_pipeline_end(status: Optional[str] = None) -> None:
    """
    Log the termination of a pipeline execution.  The test suite expects the
    phrase ``PIPELINE EXECUTION ENDED`` followed by the status string.
    """
    logger = get_pipeline_logger()
    if status:
        logger.info(f"PIPELINE EXECUTION ENDED: {status}")
    else:
        logger.info("PIPELINE EXECUTION ENDED")

def log_error(task_name: str, error: Exception, context: Optional[dict] = None) -> None:
    """
    Log an error with traceback information.  The test suite looks for the
    pattern ``ERROR in task '<TASK_NAME>'``.
    """
    logger = get_pipeline_logger()
    msg = f"ERROR in task '{task_name}': {error}"
    if context:
        msg += f" | Context: {context}"
    logger.error(msg, exc_info=True)

def log_metric(metric_name: str, value: Any, unit: Optional[str] = None, task: Optional[str] = None) -> None:
    """
    Log a metric.  Expected output format (as asserted by the tests):
    ``METRIC: <name> = <value> [<unit>]`` optionally followed by ``Task: <task>``.
    """
    logger = get_pipeline_logger()
    unit_part = f" [{unit}]" if unit else ""
    base_msg = f"METRIC: {metric_name} = {value}{unit_part}"
    if task:
        base_msg += f" | Task: {task}"
    logger.info(base_msg)

def log_chunk_info(chunk_id: int, total_chunks: int, rows_processed: int, elapsed_time: float) -> None:
    """
    Log information about a processing chunk.  The test suite expects a line
    containing ``CHUNK [<id>/<total>]``, ``Records: <rows>`` and
    ``Elapsed: <time>s`` with two decimal places.
    """
    logger = get_pipeline_logger()
    logger.info(
        f"CHUNK [{chunk_id}/{total_chunks}] | Records: {rows_processed} | Elapsed: {elapsed_time:.2f}s"
    )

def log_task_start(task_id: str, description: Optional[str] = None) -> None:
    """
    Log the start of an individual task.
    """
    logger = get_pipeline_logger()
    msg = f"TASK START: {task_id}"
    if description:
        msg += f" | {description}"
    logger.info(msg)

def log_task_end(task_id: str, status: Optional[str] = None, output_files: Optional[List[str]] = None) -> None:
    """
    Log the completion of a task.  The test suite checks for the pattern
    ``TASK END: <id> -> <status>`` and optionally a list of output files.
    """
    logger = get_pipeline_logger()
    msg = f"TASK END: {task_id}"
    if status:
        msg += f" -> {status}"
    if output_files:
        msg += f" | Output files: {output_files}"
    logger.info(msg)

def log_data_file_created(file_path: str, size_mb: float, rows: int) -> None:
    """
    Log the creation of a data file.  Expected output (as asserted by the tests):
    ``DATA CREATED: <path> | Size: <size> MB | Records: <rows>``
    """
    logger = get_pipeline_logger()
    logger.info(
        f"DATA CREATED: {file_path} | Size: {size_mb:.2f} MB | Records: {rows}"
    )