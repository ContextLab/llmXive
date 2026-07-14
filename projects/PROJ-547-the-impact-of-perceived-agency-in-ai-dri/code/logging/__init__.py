"""
Logging Module.

This module provides centralized logging utilities for the pipeline.
"""

from .pipeline_logger import get_logger, log_dict
from .run_dummy_log import main as dummy_main
from .store_consent import (
    download_consent,
    compute_sha256 as consent_sha256,
    update_metadata as consent_metadata,
    log_consent_association,
    main as consent_main,
)
from .verify_logging import (
    compute_log_completeness,
    aggregate_completeness,
    write_metric_file,
    main as verify_main,
)

__all__ = [
    "get_logger",
    "log_dict",
    "compute_log_completeness",
    "aggregate_completeness",
    "write_metric_file",
    "download_consent",
    "log_consent_association",
    "dummy_main",
    "consent_sha256",
    "consent_metadata",
    "consent_main",
    "verify_main",
]
