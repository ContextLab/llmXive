"""
Custom exception classes for the llmXive pipeline.
"""

class LlmXiveError(Exception):
    """Base exception for all llmXive errors."""
    pass

class DatasetUnavailableError(LlmXiveError):
    """Raised when a required dataset cannot be downloaded or accessed."""
    pass

class ConvergenceTimeoutError(LlmXiveError):
    """Raised when training or inference exceeds the allowed time limit."""
    pass

class PerceptionInferenceError(LlmXiveError):
    """Raised when perception inference (e.g., YOLO) fails."""
    pass

class SymbolicTransformationError(LlmXiveError):
    """Raised when transforming visual data to symbolic representation fails."""
    pass

class ValidationThresholdError(LlmXiveError):
    """Raised when a validation metric fails to meet the required threshold."""
    pass

class BaselineUnavailableError(LlmXiveError):
    """Raised when the baseline model (Visual-Guava) is not available."""
    pass

class GroundTruthSchemaMissingError(LlmXiveError):
    """Raised when ground truth data is missing required schema fields."""
    pass

class EnvironmentConfigError(LlmXiveError):
    """Raised when environment configuration constraints are violated."""
    pass
