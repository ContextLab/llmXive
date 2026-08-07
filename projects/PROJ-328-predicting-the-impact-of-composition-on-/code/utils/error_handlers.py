"""
Custom exception classes for the Solder Hardness Prediction Pipeline.

This module defines a hierarchy of exceptions to provide structured error handling
across the ingestion, feature engineering, and modeling stages.
"""
from typing import Optional, Dict, Any


class SolderPipelineError(Exception):
    """Base exception for all pipeline errors."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        self.message = message
        self.context = context or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} (Context: {context_str})"
        return self.message


class DataValidationError(SolderPipelineError):
    """Raised when data validation checks fail (e.g., composition sum, missing values)."""
    pass


class IngestionError(SolderPipelineError):
    """Raised when data ingestion from external sources fails."""
    pass


class ModelTrainingError(SolderPipelineError):
    """Raised when model training or evaluation fails."""
    pass


class ConfigurationError(SolderPipelineError):
    """Raised when configuration loading or validation fails."""
    pass
