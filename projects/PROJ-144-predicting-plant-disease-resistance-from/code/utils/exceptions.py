"""
Custom exceptions for the llmXive plant disease resistance pipeline.
"""

class TemporalVerificationError(Exception):
    """
    Raised when temporal metadata verification fails (e.g., no pre-challenge/baseline data found).
    """
    pass

class DataUnavailableError(Exception):
    """
    Raised when required data files or manifests are missing.
    """
    pass
