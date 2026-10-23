"""
Exception definitions and helper functions for the llmXive project.

This module provides a minimal set of custom exception classes and
utility functions used across the codebase, particularly by the
symbolic planner and related components.
"""

class BaseResearchException(Exception):
    """Base class for all custom research exceptions."""
    pass

# Specific exception classes
class ContradictionDetected(BaseResearchException):
    """Raised when contradictory constraints are detected."""
    pass

class ParseFailure(BaseResearchException):
    """Raised when constraint parsing fails."""
    pass

# Error code constants (used for logging and result objects)
CONTRADICTION_DETECTED = "CONTRADICTION_DETECTED"
PARSE_FAILURE = "PARSE_FAILURE"

# Helper functions to raise the above exceptions with a message
def raise_contradiction(message: str) -> None:
    """Raise a ContradictionDetected exception with the given message."""
    raise ContradictionDetected(message)

def raise_parse_failure(message: str) -> None:
    """Raise a ParseFailure exception with the given message."""
    raise ParseFailure(message)
