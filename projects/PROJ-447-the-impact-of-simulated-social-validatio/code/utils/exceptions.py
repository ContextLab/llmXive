"""
Custom exception classes for the llmXive research pipeline.

These exceptions provide specific error handling for data loading,
validation, causal language violations, and stability checks.
"""

class DataLoadError(Exception):
    """
    Raised when a real dataset fails to load from its source.

    Used by code/data/loader.py to signal that the fetch operation
    failed (e.g., network error, missing URL, API failure).
    """
    pass

class DataGapError(Exception):
    """
    Raised when the dataset contains zero rows (N=0).

    Indicates a complete absence of data after loading, preventing
    any analysis from proceeding.
    """
    pass

class InsufficientSampleError(Exception):
    """
    Raised when the dataset has fewer than the minimum required samples (N < 100).

    Indicates that while data exists, the sample size is too small
    for statistically valid inference.
    """
    pass

class CausalLanguageViolationError(Exception):
    """
    Raised when a report or output contains forbidden causal language.

    Triggered by the scanner in code/utils/cautions.py if terms like
    'causes', 'leads to', or 'determines' are detected in the analysis output.
    """
    pass

class StabilityThresholdViolationError(Exception):
    """
    Raised when the variation in model coefficients exceeds the stability threshold.

    Triggered during sensitivity analysis (code/analysis/sensitivity.py) if
    the primary predictor's coefficient fluctuates beyond the allowed limit
    defined in code/utils/constants.py.
    """
    pass