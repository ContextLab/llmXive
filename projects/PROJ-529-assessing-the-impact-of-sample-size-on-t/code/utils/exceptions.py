"""
Custom exceptions for the meta-analysis pipeline.
Implements T008: Error handling for zero-variance, negative variance, etc.
"""

class MetaAnalysisError(Exception):
    """Base exception for meta-analysis related errors."""
    pass

class DataAcquisitionError(MetaAnalysisError):
    """Raised when data acquisition from external sources fails."""
    pass

class ZeroVarianceError(MetaAnalysisError):
    """Raised when a study has zero variance (SE=0), causing division by zero."""
    pass

class NegativeVarianceError(MetaAnalysisError):
    """Raised when a variance estimate is negative, which is invalid."""
    pass

class BoundaryClampError(MetaAnalysisError):
    """Raised when a value is clamped to a boundary due to constraints."""
    pass

class ConvergenceError(MetaAnalysisError):
    """Raised when a model fitting algorithm fails to converge."""
    pass

class SchemaValidationError(MetaAnalysisError):
    """Raised when data validation against schema fails."""
    pass
