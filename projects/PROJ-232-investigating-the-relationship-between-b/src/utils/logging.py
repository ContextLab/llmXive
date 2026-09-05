"""
Logging utilities for the brain-music-emotion project.

Provides structured logging, reproducibility context (seeds, versions),
and specialized handlers for download integrity and preprocessing steps.
"""

import logging
import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Ensure consistent formatting
_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the project's standard configuration.

    Args:
        name: The name of the logger (usually __name__).

    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(_LOG_FORMAT, _DATE_FORMAT))
    logger.addHandler(console_handler)

    # File handler (optional, based on environment)
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"run_{timestamp}.log"

    try:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(_LOG_FORMAT, _DATE_FORMAT))
        logger.addHandler(file_handler)
    except Exception:
        # Fallback if file logging fails
        pass

    return logger


# Global logger instance for the utils module
_logger = get_logger(__name__)


def log_reproducibility_context(
    seed: Optional[int] = None,
    version: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log the reproducibility context (seeds, versions, environment).

    Args:
        seed: Random seed used.
        version: Project or software version.
        extra: Additional context dictionary.
    """
    context = {
        "timestamp": datetime.now().isoformat(),
        "seed": seed,
        "version": version,
        "python_version": sys.version,
        "extra": extra or {}
    }
    _logger.info(f"Reproducibility Context: {json.dumps(context)}")


def log_download_start(dataset_id: str, source: str) -> None:
    """
    Log the start of a dataset download.

    Args:
        dataset_id: Identifier of the dataset (e.g., 'ds000233').
        source: Source URL or platform (e.g., 'OpenNeuro').
    """
    _logger.info(f"DOWNLOAD_START | Dataset: {dataset_id} | Source: {source}")


def log_download_integrity(
    file_path: Union[str, Path],
    checksum: str,
    expected_checksum: str,
    algorithm: str = "md5"
) -> None:
    """
    Log the integrity verification result of a downloaded file.

    Args:
        file_path: Path to the downloaded file.
        checksum: Calculated checksum of the file.
        expected_checksum: Expected checksum value.
        algorithm: Hash algorithm used (default: md5).
    """
    file_path = Path(file_path)
    is_valid = checksum == expected_checksum
    status = "PASS" if is_valid else "FAIL"

    _logger.info(
        f"DOWNLOAD_INTEGRITY | File: {file_path.name} | "
        f"Algorithm: {algorithm} | Status: {status} | "
        f"Expected: {expected_checksum} | Actual: {checksum}"
    )

    if not is_valid:
        _logger.error(f"INTEGRITY CHECK FAILED for {file_path}")
        raise ValueError(f"Checksum mismatch for {file_path}: expected {expected_checksum}, got {checksum}")


def log_download_complete(
    dataset_id: str,
    files_downloaded: int,
    total_size_bytes: int
) -> None:
    """
    Log the completion of a dataset download.

    Args:
        dataset_id: Identifier of the dataset.
        files_downloaded: Number of files downloaded.
        total_size_bytes: Total size of downloaded data.
    """
    _logger.info(
        f"DOWNLOAD_COMPLETE | Dataset: {dataset_id} | "
        f"Files: {files_downloaded} | Size: {total_size_bytes / (1024*1024):.2f} MB"
    )


def log_preprocessing_start(
    subject_id: str,
    step: str,
    input_file: Union[str, Path]
) -> None:
    """
    Log the start of a preprocessing step.

    Args:
        subject_id: Identifier of the subject.
        step: Name of the preprocessing step (e.g., 'motion_correction').
        input_file: Path to the input file.
    """
    _logger.info(
        f"PREPROCESS_START | Subject: {subject_id} | Step: {step} | "
        f"Input: {Path(input_file).name}"
    )


def log_preprocessing_step(
    subject_id: str,
    step: str,
    duration_seconds: float,
    status: str = "success",
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log the result of a preprocessing step.

    Args:
        subject_id: Identifier of the subject.
        step: Name of the preprocessing step.
        duration_seconds: Time taken for the step.
        status: Status of the step ('success', 'warning', 'failed').
        details: Additional details (e.g., motion metrics, FD values).
    """
    msg = (
        f"PREPROCESS_STEP | Subject: {subject_id} | Step: {step} | "
        f"Status: {status} | Duration: {duration_seconds:.2f}s"
    )

    if details:
        msg += f" | Details: {json.dumps(details)}"

    if status == "failed":
        _logger.error(msg)
    elif status == "warning":
        _logger.warning(msg)
    else:
        _logger.info(msg)


def log_preprocessing_exclusion(
    subject_id: str,
    reason: str,
    metric_value: Optional[float] = None
) -> None:
    """
    Log the exclusion of a subject during preprocessing.

    Args:
        subject_id: Identifier of the excluded subject.
        reason: Reason for exclusion (e.g., 'high_motion').
        metric_value: Value of the metric that triggered exclusion (e.g., FD value).
    """
    msg = f"PREPROCESS_EXCLUSION | Subject: {subject_id} | Reason: {reason}"
    if metric_value is not None:
        msg += f" | Metric: {metric_value}"

    _logger.warning(msg)


def log_preprocessing_complete(
    subject_id: str,
    output_file: Union[str, Path],
    excluded: bool = False
) -> None:
    """
    Log the completion of preprocessing for a subject.

    Args:
        subject_id: Identifier of the subject.
        output_file: Path to the output file.
        excluded: Whether the subject was excluded from further analysis.
    """
    status = "excluded" if excluded else "complete"
    _logger.info(
        f"PREPROCESS_{status.upper()} | Subject: {subject_id} | "
        f"Output: {Path(output_file).name}"
    )


def log_analysis_start(
    analysis_type: str,
    input_files: list,
    parameters: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log the start of an analysis step.

    Args:
        analysis_type: Type of analysis (e.g., 'connectivity', 'graph_metrics').
        input_files: List of input file paths.
        parameters: Analysis parameters.
    """
    _logger.info(
        f"ANALYSIS_START | Type: {analysis_type} | "
        f"Inputs: {[Path(f).name for f in input_files]}"
    )
    if parameters:
        _logger.debug(f"Parameters: {json.dumps(parameters)}")


def log_analysis_result(
    analysis_type: str,
    metrics: Dict[str, Any],
    output_file: Optional[Union[str, Path]] = None
) -> None:
    """
    Log the results of an analysis step.

    Args:
        analysis_type: Type of analysis.
        metrics: Dictionary of computed metrics.
        output_file: Path to the output file if saved.
    """
    _logger.info(
        f"ANALYSIS_RESULT | Type: {analysis_type} | "
        f"Metrics: {json.dumps(metrics, default=str)}"
    )
    if output_file:
        _logger.info(f"ANALYSIS_OUTPUT | File: {Path(output_file).name}")


def log_error(
    step: str,
    error_message: str,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an error with context.

    Args:
        step: The step where the error occurred.
        error_message: Description of the error.
        context: Additional context about the error.
    """
    msg = f"ERROR | Step: {step} | Message: {error_message}"
    if context:
        msg += f" | Context: {json.dumps(context)}"
    _logger.error(msg)