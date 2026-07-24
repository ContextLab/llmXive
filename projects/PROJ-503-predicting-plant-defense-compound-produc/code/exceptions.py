"""
Custom exception classes for the plant defense prediction pipeline.
Defines specific error codes and exception types for different failure modes.
"""
import sys
from typing import Optional, Dict, Any


class PipelineError(Exception):
    """Base exception for pipeline errors."""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class E_DATASET(PipelineError):
    """Exception raised when dataset verification fails."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, error_code="E-DATASET", details=details)


class E_PAIRING(PipelineError):
    """Exception raised when sample pairing validation fails."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, error_code="E-PAIRING", details=details)


class E_TIMEOUT(PipelineError):
    """Exception raised when computational time limit is exceeded."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, error_code="E-TIMEOUT", details=details)


class E_POWER(PipelineError):
    """Exception raised when power analysis fails (n < 28)."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, error_code="E-POWER", details=details)


class E_SAMPLESIZE(PipelineError):
    """Exception raised when sample size is insufficient for specific operations."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, error_code="E-SAMPLESIZE", details=details)


def raise_dataset_error(message: str, details: Dict[str, Any] = None):
    """Convenience function to raise E_DATASET exception."""
    raise E_DATASET(message, details)


def raise_pairing_error(message: str, details: Dict[str, Any] = None):
    """Convenience function to raise E_PAIRING exception."""
    raise E_PAIRING(message, details)


def raise_timeout_error(message: str, details: Dict[str, Any] = None):
    """Convenience function to raise E_TIMEOUT exception."""
    raise E_TIMEOUT(message, details)


def raise_power_error(message: str, details: Dict[str, Any] = None):
    """Convenience function to raise E_POWER exception."""
    raise E_POWER(message, details)


def raise_samplesize_error(message: str, details: Dict[str, Any] = None):
    """Convenience function to raise E_SAMPLESIZE exception."""
    raise E_SAMPLESIZE(message, details)
