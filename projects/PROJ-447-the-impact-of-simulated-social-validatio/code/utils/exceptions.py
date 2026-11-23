"""
Custom exception classes for the research pipeline.

This module defines specific error types to handle various failure modes
in data loading, validation, and analysis.
"""

class DataLoadError(Exception):
    """Raised when real data loading fails."""
    pass


class DataGapError(Exception):
    """Raised when no data is available (N=0)."""
    pass


class InsufficientSampleError(Exception):
    """Raised when sample size is below the minimum threshold."""
    pass


class CausalLanguageViolationError(Exception):
    """Raised when causal language is detected in a report."""
    pass


class StabilityThresholdViolationError(Exception):
    """Raised when coefficient variation exceeds the stability threshold."""
    pass


class LongitudinalMismatchError(Exception):
    """Raised when temporal ordering of events is invalid."""
    pass
