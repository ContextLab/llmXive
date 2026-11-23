"""
Enhanced logging utilities for the llmXive automated science pipeline.

This module provides structured logging for download integrity checks,
preprocessing steps, and general pipeline execution. It ensures reproducibility
by logging seeds, timestamps, versions, and specific operational outcomes.

Key features:
- Download integrity logging (checksums, file sizes, verification status)
- Preprocessing step logging (motion correction, bandpass filtering, FD calculation)
- Structured log formats for machine parsing (JSON)
- Reproducibility metadata (seeds, software versions)
"""

import os
import sys
import json
import logging
import hashlib
import platform
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Ensure the parent directory is in the path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Constants for log levels and formats
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

# Standard log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
JSON_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s"

# Global logger instance
_logger: Optional[logging.Logger] = None

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Get or create a configured logger instance.
    
    Args:
        name: The name of the logger (usually __name__ of the calling module)
        
    Returns:
        Configured logging.Logger instance
    """
    global _logger
    
    if _logger is None:
        _logger = logging.getLogger(name)
        if not _logger.handlers:
            # Set default level
            log_level = os.getenv("LOG_LEVEL", "INFO")
            _logger.setLevel(LOG_LEVELS.get(log_level, logging.INFO))
            
            # Create console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(LOG_LEVELS.get(log_level, logging.INFO))
            console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
            _logger.addHandler(console_handler)
            
            # Create file handler if LOG_FILE is set
            log_file = os.getenv("LOG_FILE")
            if log_file:
                log_path = Path(log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(LOG_LEVELS.get(log_level, logging.INFO))
                file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
                _logger.addHandler(file_handler)
                
    return logging.getLogger(name)

def log_reproducibility_metadata(logger: logging.Logger, seed: Optional[int] = None) -> None:
    """
    Log reproducibility metadata including seed, timestamps, and environment info.
    
    Args:
        logger: The logger instance to use
        seed: Optional random seed used for reproducibility
    """
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "hostname": platform.node(),
        "seed": seed
    }
    
    logger.info(f"Reproducibility Metadata: {json.dumps(metadata)}")

def log_download_integrity(
    logger: logging.Logger,
    file_path: Union[str, Path],
    expected_checksum: Optional[str] = None,
    actual_checksum: Optional[str] = None,
    file_size: Optional[int] = None,
    status: str = "pending"
) -> Dict[str, Any]:
    """
    Log download integrity verification details.
    
    Args:
        logger: The logger instance to use
        file_path: Path to the downloaded file
        expected_checksum: Expected MD5/SHA checksum (optional)
        actual_checksum: Actual calculated checksum (optional)
        file_size: File size in bytes (optional)
        status: One of "pending", "success", "failed", "mismatch"
        
    Returns:
        Dictionary containing the logged integrity details
    """
    file_path = Path(file_path)
    log_entry = {
        "file_path": str(file_path),
        "file_exists": file_path.exists(),
        "status": status,
        "timestamp": datetime.now().isoformat()
    }
    
    if file_path.exists():
        if file_size is None:
            file_size = file_path.stat().st_size
        log_entry["file_size_bytes"] = file_size
        
        if actual_checksum is None:
            # Calculate checksum if not provided
            try:
                actual_checksum = calculate_file_checksum(file_path)
                log_entry["actual_checksum"] = actual_checksum
            except Exception as e:
                log_entry["checksum_error"] = str(e)
        
        if expected_checksum and actual_checksum:
            if expected_checksum == actual_checksum:
                log_entry["checksum_match"] = True
                log_entry["status"] = "success"
            else:
                log_entry["checksum_match"] = False
                log_entry["status"] = "mismatch"
        
        if status == "failed" and file_path.exists():
            log_entry["status"] = "unexpected_exists"
    
    # Log the entry
    if status == "success":
        logger.info(f"Download integrity verified: {json.dumps(log_entry)}")
    elif status == "mismatch":
        logger.error(f"Download integrity check FAILED (checksum mismatch): {json.dumps(log_entry)}")
    elif status == "failed":
        logger.error(f"Download integrity check FAILED: {json.dumps(log_entry)}")
    else:
        logger.info(f"Download integrity check: {json.dumps(log_entry)}")
    
    return log_entry

def calculate_file_checksum(file_path: Union[str, Path], algorithm: str = "md5") -> str:
    """
    Calculate the checksum of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (md5, sha256, etc.)
        
    Returns:
        Hexadecimal string of the checksum
    """
    file_path = Path(file_path)
    hash_func = hashlib.new(algorithm)
    
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()

def log_preprocessing_step(
    logger: logging.Logger,
    step_name: str,
    subject_id: str,
    status: str,
    details: Optional[Dict[str, Any]] = None,
    duration_seconds: Optional[float] = None
) -> Dict[str, Any]:
    """
    Log a preprocessing step execution.
    
    Args:
        logger: The logger instance to use
        step_name: Name of the preprocessing step (e.g., "motion_correction", "bandpass_filtering")
        subject_id: ID of the subject being processed
        status: One of "started", "completed", "failed", "skipped"
        details: Optional dictionary of step-specific details
        duration_seconds: Optional duration of the step in seconds
        
    Returns:
        Dictionary containing the logged step details
    """
    log_entry = {
        "step_name": step_name,
        "subject_id": subject_id,
        "status": status,
        "timestamp": datetime.now().isoformat()
    }
    
    if details:
        log_entry["details"] = details
    
    if duration_seconds is not None:
        log_entry["duration_seconds"] = duration_seconds
    
    # Log based on status
    if status == "completed":
        logger.info(f"Preprocessing step '{step_name}' completed for subject {subject_id}: {json.dumps(log_entry)}")
    elif status == "failed":
        logger.error(f"Preprocessing step '{step_name}' FAILED for subject {subject_id}: {json.dumps(log_entry)}")
    elif status == "started":
        logger.info(f"Preprocessing step '{step_name}' started for subject {subject_id}")
    elif status == "skipped":
        logger.warning(f"Preprocessing step '{step_name}' skipped for subject {subject_id}")
    
    return log_entry

def log_fmriprep_execution(
    logger: logging.Logger,
    subject_id: str,
    status: str,
    output_dir: Optional[Union[str, Path]] = None,
    version: Optional[str] = None,
    flags: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Log fMRIPrep execution details.
    
    Args:
        logger: The logger instance to use
        subject_id: ID of the subject processed
        status: One of "completed", "failed", "dry_run"
        output_dir: Path to the output directory
        version: fMRIPrep version used
        flags: Dictionary of flags/arguments used
        error_message: Error message if status is "failed"
        
    Returns:
        Dictionary containing the logged execution details
    """
    log_entry = {
        "subject_id": subject_id,
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "tool": "fMRIPrep"
    }
    
    if output_dir:
        log_entry["output_dir"] = str(Path(output_dir))
    
    if version:
        log_entry["version"] = version
    
    if flags:
        log_entry["flags"] = flags
    
    if error_message:
        log_entry["error_message"] = error_message
    
    if status == "completed":
        logger.info(f"fMRIPrep execution completed for subject {subject_id}: {json.dumps(log_entry)}")
    elif status == "failed":
        logger.error(f"fMRIPrep execution FAILED for subject {subject_id}: {json.dumps(log_entry)}")
    elif status == "dry_run":
        logger.info(f"fMRIPrep dry-run completed for subject {subject_id}: {json.dumps(log_entry)}")
    
    return log_entry

def log_framewise_displacement(
    logger: logging.Logger,
    subject_id: str,
    fd_value: float,
    threshold: float,
    excluded: bool
) -> Dict[str, Any]:
    """
    Log Framewise Displacement (FD) calculation and exclusion decision.
    
    Args:
        logger: The logger instance to use
        subject_id: ID of the subject
        fd_value: Calculated FD value
        threshold: FD threshold used for exclusion
        excluded: Whether the subject was excluded based on FD
        
    Returns:
        Dictionary containing the logged FD details
    """
    log_entry = {
        "subject_id": subject_id,
        "fd_value": fd_value,
        "threshold": threshold,
        "excluded": excluded,
        "timestamp": datetime.now().isoformat()
    }
    
    if excluded:
        logger.warning(f"Subject {subject_id} excluded due to high motion (FD={fd_value:.4f} > {threshold}): {json.dumps(log_entry)}")
    else:
        logger.info(f"Subject {subject_id} motion check passed (FD={fd_value:.4f}): {json.dumps(log_entry)}")
    
    return log_entry

def log_connectivity_computation(
    logger: logging.Logger,
    subject_id: str,
    matrix_shape: tuple,
    validation_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Log connectivity matrix computation and validation results.
    
    Args:
        logger: The logger instance to use
        subject_id: ID of the subject
        matrix_shape: Shape of the computed matrix (rows, cols)
        validation_results: Dictionary of validation checks (symmetry, range, diagonal)
        
    Returns:
        Dictionary containing the logged computation details
    """
    log_entry = {
        "subject_id": subject_id,
        "matrix_shape": matrix_shape,
        "validation_results": validation_results,
        "timestamp": datetime.now().isoformat()
    }
    
    # Check if all validations passed
    all_valid = all(validation_results.values())
    
    if all_valid:
        logger.info(f"Connectivity matrix computed and validated for subject {subject_id}: {json.dumps(log_entry)}")
    else:
        logger.error(f"Connectivity matrix validation FAILED for subject {subject_id}: {json.dumps(log_entry)}")
    
    return log_entry

def log_gap_report_generation(
    logger: logging.Logger,
    report_path: Union[str, Path],
    missing_variables: list,
    total_variables: int
) -> Dict[str, Any]:
    """
    Log the generation of a data gap report.
    
    Args:
        logger: The logger instance to use
        report_path: Path to the generated report
        missing_variables: List of missing variable names
        total_variables: Total number of variables checked
        
    Returns:
        Dictionary containing the logged report details
    """
    report_path = Path(report_path)
    log_entry = {
        "report_path": str(report_path),
        "missing_variables": missing_variables,
        "missing_count": len(missing_variables),
        "total_variables": total_variables,
        "timestamp": datetime.now().isoformat()
    }
    
    logger.error(f"Data gap report generated: {json.dumps(log_entry)}")
    
    return log_entry

# Utility function to get project version
def get_project_version() -> str:
    """
    Attempt to get the project version from git or fallback.
    
    Returns:
        Version string
    """
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--always"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    
    return "unknown"