"""
llmXive Research Pipeline - Core Utilities
"""
from .config import ensure_directories, get_data_path, get_results_path, get_logs_path
from .logging_config import setup_logging, get_logger
from .utils import log_setup, checksum_file, causal_language_scanner

__all__ = [
    'ensure_directories',
    'get_data_path',
    'get_results_path',
    'get_logs_path',
    'setup_logging',
    'get_logger',
    'log_setup',
    'checksum_file',
    'causal_language_scanner'
]

class ResearchError(Exception):
    """Base exception for research pipeline errors."""
    pass

class DataGapError(ResearchError):
    """Raised when required data is missing or unavailable."""
    pass

class SchemaValidationError(ResearchError):
    """Raised when data schema validation fails."""
    pass

class CausalLanguageError(ResearchError):
    """Raised when causal language is detected in research output."""
    pass