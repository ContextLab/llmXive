"""
Custom exception classes for the Solder Hardness Prediction Pipeline.

These exceptions provide specific error types for different failure modes,
allowing for precise error handling and logging throughout the system.
"""
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SolderPipelineError(Exception):
    """Base exception for all pipeline-related errors."""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}
        logger.error(f"SolderPipelineError: {message}", extra={"context": self.context})


class ConfigurationError(SolderPipelineError):
    """Raised when there is an issue with configuration files or settings."""

    def __init__(self, message: str, config_file: Optional[str] = None, key: Optional[str] = None):
        context = {"config_file": config_file, "key": key}
        super().__init__(message, context)


class DataValidationError(SolderPipelineError):
    """Raised when data fails validation checks (schema, thresholds, completeness)."""

    def __init__(self, message: str, record_id: Optional[str] = None, field: Optional[str] = None):
        context = {"record_id": record_id, "field": field}
        super().__init__(message, context)


class IngestionError(SolderPipelineError):
    """Raised when data ingestion from a source fails."""

    def __init__(self, message: str, source: Optional[str] = None, error_code: Optional[int] = None):
        context = {"source": source, "error_code": error_code}
        super().__init__(message, context)


class ModelTrainingError(SolderPipelineError):
    """Raised when model training or evaluation fails."""

    def __init__(self, message: str, model_type: Optional[str] = None, stage: Optional[str] = None):
        context = {"model_type": model_type, "stage": stage}
        super().__init__(message, context)


class DataInsufficientError(SolderPipelineError):
    """Raised when the dataset size is below the minimum required threshold."""

    def __init__(self, message: str, current_count: int, minimum_required: int):
        context = {"current_count": current_count, "minimum_required": minimum_required}
        super().__init__(message, context)


class CompositionSumError(DataValidationError):
    """Raised when elemental composition sums do not meet the threshold."""

    def __init__(self, message: str, actual_sum: float, threshold: float, record_id: Optional[str] = None):
        context = {"actual_sum": actual_sum, "threshold": threshold, "record_id": record_id}
        super().__init__(message, context)
