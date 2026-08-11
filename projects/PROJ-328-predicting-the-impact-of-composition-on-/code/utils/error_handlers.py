from typing import Optional, Dict, Any
import logging

class SolderPipelineError(Exception):
    """Base exception for the Solder Hardness Prediction Pipeline."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.logger = logging.getLogger(self.__class__.__name__)

class ConfigurationError(SolderPipelineError):
    """Raised when configuration files or environment variables are missing or invalid."""
    pass

class DataValidationError(SolderPipelineError):
    """Raised when data fails validation checks (e.g., composition sum, missing values)."""
    pass

class IngestionError(SolderPipelineError):
    """Raised when data ingestion from external sources fails."""
    pass

class ModelTrainingError(SolderPipelineError):
    """Raised when model training encounters an error."""
    pass
