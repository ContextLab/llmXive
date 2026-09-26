"""
Project package initialization.
Exports core utilities and error handling.
"""
from utils import log_setup, checksum_file, causal_language_scanner
from logging_config import setup_logging, get_logger

__all__ = [
    'log_setup',
    'checksum_file',
    'causal_language_scanner',
    'setup_logging',
    'get_logger'
]

class DataGapError(Exception):
    """Custom exception for data gaps."""
    pass

class SchemaValidationError(Exception):
    """Custom exception for schema validation errors."""
    pass
