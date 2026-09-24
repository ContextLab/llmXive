"""
Core package initialization for the llmXive research pipeline.

This module exports the primary utility classes, functions, and configuration
constants used across the project.
"""
from utils import log_setup, checksum_file, causal_language_scanner
from config import (
    RANDOM_SEED,
    DATA_ROOT,
    RESULTS_ROOT,
    CONTRACTS_ROOT,
    LOGS_ROOT,
    ensure_directories
)

# Explicitly define the public API
__all__ = [
    # Utilities
    "log_setup",
    "checksum_file",
    "causal_language_scanner",
    # Configuration
    "RANDOM_SEED",
    "DATA_ROOT",
    "RESULTS_ROOT",
    "CONTRACTS_ROOT",
    "LOGS_ROOT",
    "ensure_directories",
]

# Custom Exception Classes for the pipeline
class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass

class DataGapError(PipelineError):
    """Raised when a required variable or dataset is missing."""
    pass

class RobustnessError(PipelineError):
    """Raised when robustness checks (e.g., SC-003) fail."""
    pass

class CausalLanguageError(PipelineError):
    """Raised when forbidden causal language is detected."""
    pass

__version__ = "0.1.0"