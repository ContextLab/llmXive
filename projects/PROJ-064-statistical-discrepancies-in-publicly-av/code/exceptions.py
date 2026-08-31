"""
Custom exception classes for the statistical discrepancies analysis pipeline.

Provides a hierarchy of domain-specific exceptions for clear error handling
and debugging across data ingestion, processing, and analysis stages.
"""
from typing import Optional, Dict, Any

class DiscrepancyError(Exception):
    """
    Base exception for all errors in the discrepancy analysis pipeline.
    
    Attributes:
        message: Human-readable error message
        code: Optional error code for programmatic handling
        context: Optional dictionary of contextual information
    """
    
    def __init__(
        self, 
        message: str, 
        code: Optional[str] = None, 
        context: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.context = context or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message
    
    def to_dict(self) -> Dict[str, Any]:
        """Return exception details as a dictionary."""
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "code": self.code,
            "context": self.context
        }

class DataAcquisitionError(DiscrepancyError):
    """
    Raised when data acquisition fails (download, API, file reading).
    
    Attributes:
        source: The data source that failed
        reason: Specific reason for failure
    """
    
    def __init__(
        self, 
        message: str, 
        source: Optional[str] = None, 
        reason: Optional[str] = None,
        code: Optional[str] = "DATA_ACQ_001",
        context: Optional[Dict[str, Any]] = None
    ):
        self.source = source
        self.reason = reason
        full_message = message
        if source:
            full_message += f" (Source: {source})"
        if reason:
            full_message += f" (Reason: {reason})"
        
        super().__init__(full_message, code=code, context=context)

class MissingDataError(DiscrepancyError):
    """
    Raised when required data is missing or incomplete.
    
    Attributes:
        missing_fields: List of missing field names
        expected_count: Expected number of records
        actual_count: Actual number of records found
    """
    
    def __init__(
        self,
        message: str,
        missing_fields: Optional[list] = None,
        expected_count: Optional[int] = None,
        actual_count: Optional[int] = None,
        code: Optional[str] = "DATA_MISSING_001",
        context: Optional[Dict[str, Any]] = None
    ):
        self.missing_fields = missing_fields or []
        self.expected_count = expected_count
        self.actual_count = actual_count
        
        if self.missing_fields:
            message += f" Missing fields: {', '.join(self.missing_fields)}"
        if expected_count is not None and actual_count is not None:
            message += f" (Expected {expected_count}, got {actual_count})"
        
        super().__init__(message, code=code, context=context)

class ValidationFailureError(DiscrepancyError):
    """
    Raised when data validation fails (schema, constraints, business rules).
    
    Attributes:
        validation_type: Type of validation that failed
        failed_rules: List of validation rules that failed
    """
    
    def __init__(
        self,
        message: str,
        validation_type: Optional[str] = None,
        failed_rules: Optional[list] = None,
        code: Optional[str] = "VALIDATION_001",
        context: Optional[Dict[str, Any]] = None
    ):
        self.validation_type = validation_type
        self.failed_rules = failed_rules or []
        
        if self.failed_rules:
            message += f" Failed rules: {', '.join(self.failed_rules)}"
        
        super().__init__(message, code=code, context=context)

class StatisticalModelError(DiscrepancyError):
    """
    Raised when statistical modeling fails (fit errors, convergence issues).
    
    Attributes:
        model_name: Name of the model that failed
        fit_status: Status of the fitting process
        parameters: Parameters that were being fitted
    """
    
    def __init__(
        self,
        message: str,
        model_name: Optional[str] = None,
        fit_status: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        code: Optional[str] = "MODEL_001",
        context: Optional[Dict[str, Any]] = None
    ):
        self.model_name = model_name
        self.fit_status = fit_status
        self.parameters = parameters or {}
        
        if model_name:
            message += f" (Model: {model_name})"
        if fit_status:
            message += f" (Status: {fit_status})"
        
        super().__init__(message, code=code, context=context)

class ConfigurationError(DiscrepancyError):
    """
    Raised when configuration is invalid or missing required settings.
    
    Attributes:
        config_key: The configuration key that caused the error
        expected_type: Expected type for the value
    """
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        expected_type: Optional[str] = None,
        code: Optional[str] = "CONFIG_001",
        context: Optional[Dict[str, Any]] = None
    ):
        self.config_key = config_key
        self.expected_type = expected_type
        
        if config_key:
            message += f" (Key: {config_key})"
        if expected_type:
            message += f" (Expected: {expected_type})"
        
        super().__init__(message, code=code, context=context)

class ReproducibilityError(DiscrepancyError):
    """
    Raised when reproducibility checks fail (hash mismatch, missing artifacts).
    
    Attributes:
        artifact_path: Path to the artifact that failed verification
        expected_hash: Expected hash value
        actual_hash: Actual hash value found
    """
    
    def __init__(
        self,
        message: str,
        artifact_path: Optional[str] = None,
        expected_hash: Optional[str] = None,
        actual_hash: Optional[str] = None,
        code: Optional[str] = "REPRO_001",
        context: Optional[Dict[str, Any]] = None
    ):
        self.artifact_path = artifact_path
        self.expected_hash = expected_hash
        self.actual_hash = actual_hash
        
        if artifact_path:
            message += f" (Artifact: {artifact_path})"
        if expected_hash and actual_hash:
            message += f" (Hash mismatch: expected {expected_hash[:8]}..., got {actual_hash[:8]}...)"
        
        super().__init__(message, code=code, context=context)
