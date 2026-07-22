"""
Custom exceptions for the corrosion prediction pipeline.
"""
from utils.logging import get_logger

logger = get_logger(__name__)


class CorrosionPipelineError(Exception):
    """Base exception for all corrosion pipeline errors."""
    def __init__(self, message: str):
        super().__init__(message)
        logger.error(f"CorrosionPipelineError: {message}")


class DataInsufficientError(CorrosionPipelineError):
    """Raised when data is insufficient to proceed (e.g., <500 records, missing alloys)."""
    def __init__(self, message: str):
        super().__init__(message)
        logger.error(f"DataInsufficientError: {message}")


class SchemaMismatchError(CorrosionPipelineError):
    """Raised when data does not conform to expected schema contracts."""
    def __init__(self, message: str, expected_schema: dict = None, actual_schema: dict = None):
        self.expected_schema = expected_schema
        self.actual_schema = actual_schema
        full_message = f"{message}"
        if expected_schema:
            full_message += f"\nExpected: {expected_schema}"
        if actual_schema:
            full_message += f"\nActual: {actual_schema}"
        super().__init__(full_message)
        logger.error(f"SchemaMismatchError: {message}")
