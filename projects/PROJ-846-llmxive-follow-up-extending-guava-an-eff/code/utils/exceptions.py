"""
Custom exception hierarchy for the llmXive research pipeline.

This module defines the base error class and specific exceptions used
throughout the project to handle data unavailability, perception failures,
and configuration errors.

All custom exceptions inherit from LlmXiveError to allow unified handling
in the main execution loops.
"""

from typing import Optional


class LlmXiveError(Exception):
    """
    Base exception for all llmXive research pipeline errors.
    
    Attributes:
        message (str): Human-readable error description.
        context (dict, optional): Additional context information (e.g., file paths, task IDs).
    """
    
    def __init__(self, message: str, context: Optional[dict] = None):
        self.message = message
        self.context = context or {}
        full_message = message
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            full_message = f"{message} [{context_str}]"
        super().__init__(full_message)


class DatasetUnavailableError(LlmXiveError):
    """
    Raised when a required dataset cannot be fetched or accessed.
    
    This exception is used to strictly enforce the "fail loudly" policy.
    It must be raised when:
    1. A download URL is unreachable.
    2. A required pip package is missing.
    3. A local data file is missing or corrupted.
    
    NO synthetic data generation or fallback logic should be attempted
    after this exception is raised.
    
    Attributes:
        dataset_name (str): Name of the missing dataset.
        source (str): The attempted source (URL, package name, or path).
        reason (str): Specific reason for unavailability.
    """
    
    def __init__(
        self,
        dataset_name: str,
        source: str,
        reason: str = "Could not access the dataset"
    ):
        message = (
            f"Dataset '{dataset_name}' is unavailable. "
            f"Source: {source}. Reason: {reason}."
        )
        super().__init__(
            message,
            context={
                "dataset_name": dataset_name,
                "source": source,
                "reason": reason
            }
        )


class PerceptionInferenceError(LlmXiveError):
    """
    Raised when the perception module (e.g., YOLO) fails to process an image.
    
    Causes may include:
    - Corrupted image file.
    - ONNX runtime failure.
    - Invalid model weights.
    """
    pass


class SymbolicTransformationError(LlmXiveError):
    """
    Raised when the transformation from raw pixels to symbolic states fails.
    
    This includes schema validation failures, missing fields, or logic errors
    during the symbolic representation generation.
    """
    pass


class ValidationThresholdError(LlmXiveError):
    """
    Raised when a validation metric (e.g., IoU, precision) falls below a required threshold.
    
    Used to halt execution if the perception or transformation quality is insufficient
    for the research requirements.
    """
    pass


class BaselineUnavailableError(LlmXiveError):
    """
    Raised when the Baseline-Guava (Visual) agent model cannot be loaded.
    
    Since the Baseline-Guava is the PRIMARY comparison required by the spec (SC-001),
    this error must halt the entire project if the model is missing.
    """
    pass


class GroundTruthSchemaMissingError(LlmXiveError):
    """
    Raised when expected ground-truth annotations are missing from the raw data.
    
    This prevents the computation of the Perception Ground-Truth Log (FR-007).
    The project must halt if this error is raised.
    """
    pass


class EnvironmentConfigError(LlmXiveError):
    """
    Raised when the execution environment violates project constraints.
    
    Examples:
    - GPU detected when CPU-only mode is enforced.
    - Python version is below 3.11.
    - Insufficient RAM detected.
    """
    pass