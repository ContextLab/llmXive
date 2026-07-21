"""
Logging infrastructure for the Hubble Constant Isotropy analysis pipeline.

This module provides a centralized logging configuration that supports:
- Standard console and file output
- Audit trails for data filtering operations
- Structured error logging with timestamps and context
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Global logger instance registry
_loggers: dict[str, logging.Logger] = {}
_initialized: bool = False

# Default log format
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
AUDIT_FORMAT = "%(asctime)s - AUDIT - %(levelname)s - %(message)s"

def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[Path] = None,
    enable_audit: bool = True,
    audit_file: Optional[Path] = None,
) -> None:
    """
    Configure the root logging infrastructure.

    Args:
        log_level: Minimum log level (e.g., logging.DEBUG, logging.INFO)
        log_file: Path to main application log file. If None, only console output.
        enable_audit: If True, enables separate audit logging for data operations.
        audit_file: Path to audit log file. If None and enable_audit=True, uses 'audit.log'
                    in the current working directory.

    This function configures:
    1. Root logger with console handler
    2. Optional file handler for general logs
    3. Optional 'audit' logger for data filtering trails
    """
    global _initialized

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates on re-calls
    root_logger.handlers.clear()

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(DEFAULT_FORMAT)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File Handler (General)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(console_formatter)
        root_logger.addHandler(file_handler)

    # Audit Logger Setup
    if enable_audit:
        audit_logger = logging.getLogger("audit")
        audit_logger.setLevel(log_level)
        # Prevent propagation to root to avoid double logging if desired,
        # but usually we want audit logs in the main file too if configured.
        # Here we add a dedicated file handler for audit trails.
        if audit_file:
            audit_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            audit_file = Path.cwd() / "audit.log"

        # Only add handler if not already present to avoid duplicates
        if not audit_logger.handlers:
            audit_handler = logging.FileHandler(audit_file)
            audit_handler.setLevel(log_level)
            audit_formatter = logging.Formatter(AUDIT_FORMAT)
            audit_handler.setFormatter(audit_formatter)
            audit_logger.addHandler(audit_handler)
            # Ensure audit logs go to console as well for visibility during dev
            audit_logger.addHandler(console_handler)

    _initialized = True
    logging.info("Logging infrastructure initialized.")

def get_logger(name: str) -> logging.Logger:
    """
    Retrieve or create a named logger.

    Args:
        name: Logger name (typically module name).

    Returns:
        Configured logger instance.
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    # If setup_logging hasn't been called yet, basicConfig will handle it,
    # but explicit setup is preferred.
    if not _initialized:
        # Fallback to basic config if not explicitly set up
        logging.basicConfig(level=logging.INFO, format=DEFAULT_FORMAT)

    _loggers[name] = logger
    return logger

def log_data_filtering(
    source: str,
    filter_type: str,
    reason: str,
    count_removed: int,
    count_remaining: int,
    details: Optional[str] = None,
) -> None:
    """
    Log a data filtering event to the audit trail.

    This function is critical for reproducibility, ensuring that every
    data reduction step is recorded with context.

    Args:
        source: Name of the dataset or file being filtered (e.g., 'pantheon_plus.csv')
        filter_type: Type of filter applied (e.g., 'redshift_cut', 'quality_flag', 'coordinate_validation')
        reason: Human-readable explanation of why the filter was applied.
        count_removed: Number of records removed by this operation.
        count_remaining: Number of records remaining after this operation.
        details: Optional additional context (e.g., specific threshold values).
    """
    audit_logger = logging.getLogger("audit")
    if not audit_logger.handlers:
        # Fallback if audit logger wasn't fully initialized
        audit_logger = get_logger("audit")
        audit_logger.setLevel(logging.INFO)
        audit_logger.addHandler(logging.StreamHandler(sys.stdout))

    message_parts = [
        f"SOURCE={source}",
        f"FILTER={filter_type}",
        f"REASON={reason}",
        f"REMOVED={count_removed}",
        f"REMAINING={count_remaining}",
    ]
    if details:
        message_parts.append(f"DETAILS={details}")

    message = " | ".join(message_parts)
    audit_logger.info(message)

def log_error(
    operation: str,
    exception: Exception,
    context: Optional[dict] = None,
    critical: bool = False,
) -> None:
    """
    Log an error with structured context for debugging.

    Args:
        operation: The name of the operation that failed.
        exception: The exception instance that was raised.
        context: Optional dictionary of contextual variables (e.g., input file paths, parameters).
        critical: If True, logs at CRITICAL level; otherwise ERROR.
    """
    logger = get_logger("error_handler")
    level = logging.CRITICAL if critical else logging.ERROR

    log_msg = f"ERROR in {operation}: {type(exception).__name__}: {exception}"
    logger.log(level, log_msg)

    if context:
        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        logger.log(level, f"Context: {context_str}")

    # Log traceback
    import traceback
    tb_str = traceback.format_exc()
    logger.log(level, f"Traceback:\n{tb_str}")