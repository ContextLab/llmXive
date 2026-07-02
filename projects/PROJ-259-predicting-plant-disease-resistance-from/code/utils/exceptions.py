"""
Custom exceptions for the llmXive plant disease resistance pipeline.

This module defines specific exception classes used to signal
data integrity issues and insufficient statistical power,
allowing for precise error handling in the main pipeline.
"""

class PipelineException(Exception):
    """Base class for all pipeline-specific exceptions."""
    def __init__(self, message: str, code: int):
        self.code = code
        super().__init__(f"[Code {code}] {message}")


class EX_DATA_INTEGRITY(PipelineException):
    """
    Raised when data integrity checks fail.
    
    Triggered when:
    - Source type is not SIMULATED but sample count < 100.
    - Missing modalities detected in real data runs.
    - Sample IDs do not match across modalities.
    
    Code: 02
    """
    def __init__(self, message: str):
        super().__init__(message, code=2)


class EX_POWER_INSUFFICIENT(PipelineException):
    """
    Raised when statistical power is insufficient for the analysis.
    
    Triggered when:
    - Real data runs have fewer than 100 aligned samples.
    - Signal-to-noise ratio is too low for reliable detection.
    
    Code: 03
    """
    def __init__(self, message: str):
        super().__init__(message, code=3)