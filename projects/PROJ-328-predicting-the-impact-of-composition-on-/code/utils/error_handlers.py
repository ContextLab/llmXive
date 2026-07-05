"""
Custom exception classes for the solder hardness prediction pipeline.
Provides specific error types for better error handling and debugging.
"""
from typing import Optional, Dict, Any

class SolderPipelineError(Exception):
    """
    Base exception for all pipeline errors.
    """

    def __init__(
        self,
        message: str,
        code: str = "PIPELINE_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def __str__(self) -> str:
        base = f"[{self.code}] {self.message}"
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{base} ({details_str})"
        return base

class DataValidationError(SolderPipelineError):
    """
    Exception raised when data validation fails.
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        expected: Optional[str] = None,
    ):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        if expected:
            details["expected"] = expected

        super().__init__(
            message, code="DATA_VALIDATION_ERROR", details=details
        )

class IngestionError(SolderPipelineError):
    """
    Exception raised when data ingestion fails.
    """

    def __init__(
        self,
        message: str,
        source: Optional[str] = None,
        status_code: Optional[int] = None,
    ):
        details = {}
        if source:
            details["source"] = source
        if status_code is not None:
            details["status_code"] = status_code

        super().__init__(message, code="INGESTION_ERROR", details=details)

class ModelTrainingError(SolderPipelineError):
    """
    Exception raised when model training fails.
    """

    def __init__(
        self,
        message: str,
        model_type: Optional[str] = None,
        fold: Optional[int] = None,
    ):
        details = {}
        if model_type:
            details["model_type"] = model_type
        if fold is not None:
            details["fold"] = fold

        super().__init__(message, code="MODEL_TRAINING_ERROR", details=details)

class ConfigurationError(SolderPipelineError):
    """
    Exception raised when configuration is invalid or missing.
    """

    def __init__(
        self,
        message: str,
        key: Optional[str] = None,
        config_file: Optional[str] = None,
    ):
        details = {}
        if key:
            details["key"] = key
        if config_file:
            details["config_file"] = config_file

        super().__init__(message, code="CONFIGURATION_ERROR", details=details)
