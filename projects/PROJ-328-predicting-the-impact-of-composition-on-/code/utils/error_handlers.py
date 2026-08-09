"""
Custom exception classes for the Solder Hardness Prediction Pipeline.

This module defines a hierarchy of exceptions to handle specific error scenarios
encountered during data ingestion, model training, and configuration management.
All exceptions inherit from a base SolderPipelineError to allow unified handling.
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
            return f"{self.message} (Context: {self.context})"
        return self.message


class ConfigurationError(SolderPipelineError):
    """Raised when configuration loading or validation fails."""
    pass


class DataValidationError(SolderPipelineError):
    """Raised when data fails validation checks (e.g., missing values, sum constraints)."""
    pass


class IngestionError(SolderPipelineError):
    """Raised when data ingestion from a source fails."""
    pass


class ModelTrainingError(SolderPipelineError):
    """Raised when model training or evaluation fails."""
    pass
