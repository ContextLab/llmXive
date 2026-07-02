"""
Custom exceptions for the llmXive plant disease resistance pipeline.

This module defines specific error codes and exception classes used to
enforce data integrity and statistical power requirements as per FR-007
and FR-008.
"""

class PipelineError(Exception):
    """Base exception for all pipeline-specific errors."""
    def __init__(self, message: str, code: int = 0):
        self.code = code
        super().__init__(message)

class EX_DATA_INTEGRITY(PipelineError):
    """
    Raised when data integrity checks fail.

    Error Code: 02
    Triggered when:
    - Source type is not SIMULATED and aligned samples < 100
    - Source type is not SIMULATED and missing modalities are detected
    - Required data fields are missing or malformed
    """
    def __init__(self, message: str):
        super().__init__(message, code=2)

class EX_POWER_INSUFFICIENT(PipelineError):
    """
    Raised when statistical power requirements are not met.

    Error Code: 03
    Triggered when:
    - Source type is not SIMULATED and total samples < 100
    - Sample size is insufficient for the requested statistical analysis
    """
    def __init__(self, message: str):
        super().__init__(message, code=3)