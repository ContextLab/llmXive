"""
Execution logging utility for llmXive pipeline.

Provides structured logging with file and console handlers,
specifically designed to track VLM API calls and execution metrics.
"""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Ensure project structure exists
LOG_DIR = Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Global logger instance
_logger: Optional[logging.Logger] = None


def get_logger(name: str = "llmxive_pipeline") -> logging.Logger:
    """
    Get or create the global project logger.

    Args:
        name: Logger name (default: "llmxive_pipeline")

    Returns:
        Configured logging.Logger instance
    """
    global _logger
    if _logger is None:
        _logger = _setup_logger(name)
    return _logger


def _setup_logger(name: str) -> logging.Logger:
    """
    Configure the logger with file and console handlers.

    Args:
        name: Logger name

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Create formatter with detailed info
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File handler - logs to data/logs/<timestamp>.log
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"{timestamp}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Console handler - logs to stdout with INFO+ level
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Log startup info
    logger.info(f"Logger initialized. Log file: {log_file}")
    logger.info(f"Python version: {sys.version}")

    return logger


def log_vlm_call(
    logger: Optional[logging.Logger] = None,
    model_id: str = "",
    input_tokens: int = 0,
    output_tokens: int = 0,
    duration_ms: float = 0.0,
    success: bool = True,
    **extra: Any
) -> None:
    """
    Log a VLM API call attempt.

    Used to verify zero VLM calls during visual-only labeling (FR-001.1).

    Args:
        logger: Logger instance (uses global if None)
        model_id: VLM model identifier
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        duration_ms: Call duration in milliseconds
        success: Whether the call succeeded
        **extra: Additional context (e.g., prompt_preview, error_message)
    """
    log = logger or get_logger()
    status = "SUCCESS" if success else "FAILED"
    log.info(
        f"VLM_CALL | model={model_id} | status={status} | "
        f"in={input_tokens} | out={output_tokens} | "
        f"duration={duration_ms:.2f}ms | {extra}"
    )


def log_data_generation(
    logger: Optional[logging.Logger] = None,
    event: str = "",
    frame_count: int = 0,
    duration_seconds: float = 0.0,
    output_path: str = "",
    **extra: Any
) -> None:
    """
    Log data generation events.

    Args:
        logger: Logger instance
        event: Event type (e.g., "frame_written", "chunk_completed")
        frame_count: Number of frames processed
        duration_seconds: Duration of the event
        output_path: Path to generated data
        **extra: Additional context
    """
    log = logger or get_logger()
    log.info(
        f"DATA_GEN | event={event} | frames={frame_count} | "
        f"duration={duration_seconds:.2f}s | path={output_path} | {extra}"
    )


def log_feature_extraction(
    logger: Optional[logging.Logger] = None,
    event: str = "",
    feature_count: int = 0,
    dimension: int = 0,
    input_path: str = "",
    output_path: str = "",
    **extra: Any
) -> None:
    """
    Log feature extraction events.

    Args:
        logger: Logger instance
        event: Event type
        feature_count: Number of features extracted
        dimension: Feature dimension
        input_path: Source data path
        output_path: Output path
        **extra: Additional context
    """
    log = logger or get_logger()
    log.info(
        f"FEATURE | event={event} | count={feature_count} | "
        f"dim={dimension} | input={input_path} | output={output_path} | {extra}"
    )


def log_error(
    logger: Optional[logging.Logger] = None,
    error_type: str = "",
    message: str = "",
    context: Optional[Dict[str, Any]] = None,
    **extra: Any
) -> None:
    """
    Log errors with structured context.

    Args:
        logger: Logger instance
        error_type: Type of error (e.g., "ValueError", "RuntimeError")
        message: Error message
        context: Contextual data at error time
        **extra: Additional context
    """
    log = logger or get_logger()
    ctx_str = f" | {context}" if context else ""
    log.error(
        f"ERROR | type={error_type} | message={message}{ctx_str} | {extra}"
    )


def log_metrics(
    logger: Optional[logging.Logger] = None,
    metric_name: str = "",
    value: float = 0.0,
    baseline_value: Optional[float] = None,
    improvement: Optional[float] = None,
    **extra: Any
) -> None:
    """
    Log evaluation metrics.

    Args:
        logger: Logger instance
        metric_name: Name of the metric
        value: Metric value
        baseline_value: Baseline comparison value (optional)
        improvement: Improvement over baseline (optional)
        **extra: Additional context
    """
    log = logger or get_logger()
    baseline_str = f" | baseline={baseline_value}" if baseline_value is not None else ""
    improvement_str = f" | improvement={improvement:.4f}" if improvement is not None else ""
    log.info(
        f"METRIC | name={metric_name} | value={value:.4f}{baseline_str}{improvement_str} | {extra}"
    )


def count_vlm_calls(log_file_path: Optional[Path] = None) -> int:
    """
    Count the number of VLM calls in a log file.

    Used to verify zero VLM calls during visual-only labeling.

    Args:
        log_file_path: Path to log file (uses latest if None)

    Returns:
        Number of VLM calls found
    """
    if log_file_path is None:
        # Find latest log file
        logs = sorted(LOG_DIR.glob("*.log"))
        if not logs:
            return 0
        log_file_path = logs[-1]

    if not log_file_path.exists():
        return 0

    count = 0
    with open(log_file_path, "r", encoding="utf-8") as f:
        for line in f:
            if "VLM_CALL" in line:
                count += 1

    return count


def verify_zero_vlm_calls(log_file_path: Optional[Path] = None) -> bool:
    """
    Verify that no VLM calls were made in the log file.

    Args:
        log_file_path: Path to log file

    Returns:
        True if zero VLM calls found, False otherwise
    """
    return count_vlm_calls(log_file_path) == 0
