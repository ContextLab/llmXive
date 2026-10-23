"""
Exception definitions for the llmXive project.

This module centralizes custom exception classes and helper functions
used across the codebase, particularly by the symbolic planner and
exclusion logging components.
"""

class BaseResearchException(Exception):
    """Base class for all custom exceptions in the research code."""
    pass


class ContradictionDetected(BaseResearchException):
    """Raised when contradictory constraints are detected during planning."""
    pass


class ParseFailure(BaseResearchException):
    """Raised when constraint parsing fails."""
    pass


# Exported constants matching the names expected by other modules
CONTRADICTION_DETECTED = ContradictionDetected
PARSE_FAILURE = ParseFailure


def raise_contradiction(message: str) -> None:
    """Helper to raise a CONTRADICTION_DETECTED exception."""
    raise CONTRADICTION_DETECTED(message)


def raise_parse_failure(message: str) -> None:
    """Helper to raise a PARSE_FAILURE exception."""
    raise PARSE_FAILURE(message)
