"""
llmXive Project Core Utilities Package.

This package provides foundational utilities, configuration, and logging
for the research pipeline.
"""

from .config import RANDOM_SEED, DATA_ROOT, RESULTS_ROOT, ensure_directories
from .config import get_data_path, get_results_path, get_logs_path
from .logging_config import setup_logging, get_logger
from .utils import log_setup, checksum_file, causal_language_scanner

__all__ = [
    # Config
    "RANDOM_SEED",
    "DATA_ROOT",
    "RESULTS_ROOT",
    "ensure_directories",
    "get_data_path",
    "get_results_path",
    "get_logs_path",
    # Logging
    "setup_logging",
    "get_logger",
    "log_setup",
    # Utilities
    "checksum_file",
    "causal_language_scanner",
]

class DataGapError(Exception):
    """Raised when a required dataset or variable is missing."""
    pass

class SchemaValidationError(Exception):
    """Raised when data does not match the expected schema."""
    pass

class CausalLanguageError(Exception):
    """Raised when forbidden causal language is detected."""
    pass
