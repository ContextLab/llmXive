"""
Custom exceptions for the llmXive research pipeline.

This module defines custom exception classes for handling specific
failure modes in the symbolic and evolutionary search components.
"""

class BaseResearchException(Exception):
    """Base class for all research pipeline exceptions."""
    def __init__(self, message: str, code: str = "UNKNOWN"):
        super().__init__(message)
        self.message = message
        self.code = code

class PARSE_FAILURE(BaseResearchException):
    """Raised when parsing of constraints or data fails."""
    def __init__(self, message: str):
        super().__init__(message, code="PARSE_FAILURE")

class CONTRADICTION_DETECTED(BaseResearchException):
    """Raised when a logical contradiction is detected in constraints."""
    def __init__(self, message: str):
        super().__init__(message, code="CONTRADICTION_DETECTED")

class VERIFIER_ERROR(BaseResearchException):
    """Raised when the deterministic verifier encounters an error."""
    def __init__(self, message: str):
        super().__init__(message, code="VERIFIER_ERROR")

def raise_parse_failure(message: str):
    """
    Helper function to raise a PARSE_FAILURE exception.
    
    Args:
        message: Description of the parsing failure.
        
    Raises:
        PARSE_FAILURE: Always raised with the provided message.
    """
    raise PARSE_FAILURE(message)

def raise_contradiction(message: str):
    """
    Helper function to raise a CONTRADICTION_DETECTED exception.
    
    Args:
        message: Description of the contradiction.
        
    Raises:
        CONTRADICTION_DETECTED: Always raised with the provided message.
    """
    raise CONTRADICTION_DETECTED(message)

def raise_verifier_error(message: str):
    """
    Helper function to raise a VERIFIER_ERROR exception.
    
    Args:
        message: Description of the verifier error.
        
    Raises:
        VERIFIER_ERROR: Always raised with the provided message.
    """
    raise VERIFIER_ERROR(message)
