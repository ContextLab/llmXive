import logging
import logging.handlers
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pathlib import Path

from src.models.entities import EvaluationResult, ModelCheckpoint, DatasetSubset


class JsonFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON log records.
    Ensures reproducibility by including timestamps in ISO 8601 format with timezone.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Include extra fields if present
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data

        # Handle exceptions
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logging(
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    console_output: bool = True,
) -> logging.Logger:
    """
    Configure the root logger with structured JSON output.

    Args:
        log_file: Path to the log file. If None, logs only to console.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        console_output: Whether to also output logs to stdout/stderr.

    Returns:
        Configured root logger.
    """
    logger = logging.getLogger()
    logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()

    formatter = JsonFormatter()

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)

    return logger


def log_reproducibility_manifest(
    logger: logging.Logger,
    manifest_data: Dict[str, Any],
    output_path: str = "data/manifest.yaml",
) -> None:
    """
    Log reproducibility manifest data in a structured JSON format.
    This function writes the manifest to a file and logs a summary to the logger.

    Args:
        logger: The configured logger instance.
        manifest_data: Dictionary containing reproducibility data (seeds, versions, etc.).
        output_path: Path to write the manifest file.
    """
    # Ensure directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Write manifest to file (YAML-like structure for readability, but stored as JSON for parsing)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, default=str)

    logger.info(
        "Reproducibility manifest saved",
        extra={"extra_data": {"path": str(output_file), "entries": len(manifest_data)}},
    )


def log_evaluation_result(
    logger: logging.Logger,
    result: EvaluationResult,
) -> None:
    """
    Log an EvaluationResult entity in structured JSON format.

    Args:
        logger: The configured logger instance.
        result: The evaluation result to log.
    """
    logger.info(
        "Evaluation completed",
        extra={
            "extra_data": {
                "subset": result.dataset_subset,
                "model_checkpoint": result.model_checkpoint,
                "success_rate": result.success_rate,
                "trajectory_length": result.trajectory_length,
                "variance": result.variance,
                "ci_lower": result.ci_95_lower,
                "ci_upper": result.ci_95_upper,
            }
        },
    )


def log_model_checkpoint(
    logger: logging.Logger,
    checkpoint: ModelCheckpoint,
) -> None:
    """
    Log a ModelCheckpoint entity in structured JSON format.

    Args:
        logger: The configured logger instance.
        checkpoint: The model checkpoint to log.
    """
    logger.info(
        "Model checkpoint saved",
        extra={
            "extra_data": {
                "path": checkpoint.path,
                "epoch": checkpoint.epoch,
                "size_bytes": checkpoint.size_bytes,
                "checksum": checkpoint.checksum,
                "timestamp": checkpoint.timestamp.isoformat(),
            }
        },
    )


def log_dataset_subset(
    logger: logging.Logger,
    subset: DatasetSubset,
) -> None:
    """
    Log a DatasetSubset entity in structured JSON format.

    Args:
        logger: The configured logger instance.
        subset: The dataset subset to log.
    """
    logger.info(
        "Dataset subset loaded",
        extra={
            "extra_data": {
                "name": subset.name,
                "source": subset.source,
                "num_samples": subset.num_samples,
                "platforms": subset.platforms,
                "checksum": subset.checksum,
            }
        },
    )
