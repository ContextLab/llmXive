"""
llmXive Automated Science Pipeline - Source Package.

This package contains the core logic for the biomarker discovery pipeline,
including data acquisition, preprocessing, differential expression,
meta-analysis, and modeling.
"""

from .config import (
    PROJECT_ROOT,
    DATA_DIR,
    RAW_DIR,
    PROCESSED_DIR,
    RESULTS_DIR,
    META_ANALYSIS_DIR,
    STATE_DIR,
    CONTRACTS_DIR,
    MAX_VARIANCE_GENES,
    RANDOM_SEED,
    FDR_THRESHOLD,
    ensure_directories,
)
from .utils import (
    setup_logging,
    calculate_checksum,
    generate_checksums_for_directory,
    timeout_handler,
    watchdog,
    TimeoutError,
)

__all__ = [
    "PROJECT_ROOT",
    "DATA_DIR",
    "RAW_DIR",
    "PROCESSED_DIR",
    "RESULTS_DIR",
    "META_ANALYSIS_DIR",
    "STATE_DIR",
    "CONTRACTS_DIR",
    "MAX_VARIANCE_GENES",
    "RANDOM_SEED",
    "FDR_THRESHOLD",
    "ensure_directories",
    "setup_logging",
    "calculate_checksum",
    "generate_checksums_for_directory",
    "timeout_handler",
    "watchdog",
    "TimeoutError",
]
