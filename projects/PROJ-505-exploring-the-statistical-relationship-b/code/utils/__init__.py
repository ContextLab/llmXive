# -*- coding: utf-8 -*-
"""
Utility functions for the llmXive solar wind analysis pipeline.

This package provides shared utilities for I/O operations, logging,
directory management, and data validation.
"""

from .io import compute_md5, verify_md5, load_parquet, save_parquet
from .logging import (
    PipelineError,
    DataIngestionError,
    AlignmentError,
    AnalysisError,
    ConfigError,
    ValidationError,
    get_logger,
    setup_logging,
    log_duration,
    check_memory_usage,
    log_error_and_raise,
    safe_execute,
)
from .mkdirs import ensure_dirs

__all__ = [
    # I/O utilities
    "compute_md5",
    "verify_md5",
    "load_parquet",
    "save_parquet",
    # Logging and error handling
    "PipelineError",
    "DataIngestionError",
    "AlignmentError",
    "AnalysisError",
    "ConfigError",
    "ValidationError",
    "get_logger",
    "setup_logging",
    "log_duration",
    "check_memory_usage",
    "log_error_and_raise",
    "safe_execute",
    # Directory management
    "ensure_dirs",
]