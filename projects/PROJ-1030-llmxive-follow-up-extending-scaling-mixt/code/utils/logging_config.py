import logging
import os
import sys
from pathlib import Path
from typing import Optional
import traceback
import json
import time
from datetime import datetime

# Ensure log directories exist
LOG_DIR = Path("data/processed")
LOG_DIR.mkdir(parents=True, exist_ok=True)

def configure_root_logger(level: int = logging.INFO) -> logging.Logger:
    """Configure the root logger with file and console handlers."""
    logger = logging.getLogger()
    logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # File handler for general logs
    log_file = LOG_DIR / "pipeline.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)

    # Console handler for immediate feedback
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(file_format)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)

class DataFetchLogger:
    """Logger specifically for data fetch operations with loud failure capability."""

    def __init__(self, name: str = "DataFetch"):
        self.logger = logging.getLogger(name)
        self.fetch_log_file = LOG_DIR / "data_fetch.log"

    def log_fetch_start(self, source: str, clip_id: str):
        self.logger.info(f"Starting fetch for {clip_id} from {source}")

    def log_fetch_success(self, clip_id: str, size_bytes: int):
        self.logger.info(f"Successfully fetched {clip_id}, size: {size_bytes} bytes")

    def log_fetch_failure(self, clip_id: str, error: Exception, is_fatal: bool = True):
        if is_fatal:
            msg = f"CRITICAL: Fetch failed for {clip_id}: {str(error)}"
            self.logger.error(msg)
            self.logger.error(traceback.format_exc())
            raise RuntimeError(msg) from error
        else:
            self.logger.warning(f"Fetch failed for {clip_id} (non-fatal): {str(error)}")

    def log_memory_usage(self, clip_id: str, usage_mb: float):
        self.logger.info(f"Memory usage for {clip_id}: {usage_mb:.2f} MB")

def fail_loudly(message: str, context: Optional[dict] = None):
    """
    Log a critical error and raise an exception immediately.
    Used to enforce the 'FAIL LOUDLY' constraint for data fetches and critical errors.
    """
    logger = logging.getLogger("CriticalError")
    logger.critical(f"FATAL ERROR: {message}")
    if context:
        logger.critical(f"Context: {json.dumps(context, indent=2)}")
    logger.critical(traceback.format_stack())
    raise RuntimeError(f"Critical Failure: {message}")

def log_simulation_error(clip_id: str, error: Exception):
    """Log simulation errors."""
    logger = logging.getLogger("Simulation")
    logger.error(f"Simulation failed for {clip_id}: {str(error)}")
    logger.error(traceback.format_exc())

def log_excluded_sample(clip_id: str, reason: str, confidence: float):
    """Log excluded samples to the specific log file."""
    logger = logging.getLogger("ExcludedSamples")
    logger.warning(f"Excluded {clip_id}: {reason} (confidence: {confidence})")
    
    # Also append to the specific excluded_samples.log file as a CSV line if needed
    excluded_log_path = LOG_DIR / "excluded_samples.log"
    with open(excluded_log_path, "a") as f:
        f.write(f"{clip_id},{reason},{confidence}\n")

def log_simulation_batch_stats(stats: dict):
    """Log batch simulation statistics."""
    logger = logging.getLogger("Simulation")
    logger.info(f"Batch stats: {json.dumps(stats)}")

def log_feature_extraction_progress(clip_id: str, chunk_index: int, total_chunks: int, memory_mb: float):
    """Log progress of feature extraction."""
    logger = logging.getLogger("Extraction")
    logger.info(f"Extraction: {clip_id} - Chunk {chunk_index}/{total_chunks} - Memory: {memory_mb:.2f} MB")

def log_label_generation_progress(clip_id: str, status: str, confidence: Optional[float] = None):
    """Log progress of label generation."""
    logger = logging.getLogger("Labeling")
    msg = f"Labeling: {clip_id} - {status}"
    if confidence is not None:
        msg += f" (confidence: {confidence:.4f})"
    logger.info(msg)

def log_prior_audit_result(clip_id: str, independence_score: float, passed: bool):
    """Log prior audit results."""
    logger = logging.getLogger("Audit")
    status = "PASSED" if passed else "FAILED"
    logger.info(f"Audit: {clip_id} - Independence Score: {independence_score:.4f} - {status}")

def configure_data_fetch_logger() -> DataFetchLogger:
    """Configure and return a DataFetchLogger instance."""
    return DataFetchLogger()

# Initialize root logger on import if not already configured
if not logging.getLogger().handlers:
    configure_root_logger()
