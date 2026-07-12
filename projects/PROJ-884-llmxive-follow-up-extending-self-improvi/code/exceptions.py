"""
Custom exception classes for the llmXive research pipeline.

These exceptions handle specific failure modes in the symbolic planning
and verification pipeline, addressing robustness gaps identified in the
research design.
"""

class BaseResearchException(Exception):
    """Base class for all custom research pipeline exceptions."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class PARSE_FAILURE(BaseResearchException):
    """
    Raised when the symbolic parser fails to convert puzzle constraints
    into a formal language parseable by the planner.
    
    This addresses the robustness gap where input constraints may be
    malformed or outside the supported grammar.
    """
    pass

class CONTRADICTION_DETECTED(BaseResearchException):
    """
    Raised when the symbolic planner detects logical contradictions
    within the problem constraints or during sub-goal decomposition.
    
    This indicates that the current set of constraints is unsatisfiable,
    requiring the evolutionary loop to exclude this candidate or backtrack.
    """
    pass

class VERIFIER_ERROR(BaseResearchException):
    """
    Raised when the deterministic verifier encounters an internal error
    that prevents it from validating a solution path.
    
    This is distinct from a solution being invalid; it indicates a
    failure in the verification mechanism itself (e.g., timeout,
    unsupported operation, or state corruption).
    """
    pass

# Factory functions for consistent instantiation (optional but useful)
def raise_parse_failure(message: str, details: dict = None) -> None:
    """Helper to raise PARSE_FAILURE with standardized formatting."""
    raise PARSE_FAILURE(message, details)

def raise_contradiction(message: str, details: dict = None) -> None:
    """Helper to raise CONTRADICTION_DETECTED with standardized formatting."""
    raise CONTRADICTION_DETECTED(message, details)

def raise_verifier_error(message: str, details: dict = None) -> None:
    """Helper to raise VERIFIER_ERROR with standardized formatting."""
    raise VERIFIER_ERROR(message, details)