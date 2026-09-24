"""
Custom exception hierarchy for the llmXive automated science pipeline.

This module defines the core exception types used throughout the project
to ensure consistent error handling and clear failure signaling.

All exceptions inherit from LlmXiveError to allow broad catching of
project-specific errors while preserving standard Python exception behavior.
"""

from typing import Optional


class LlmXiveError(Exception):
    """
    Base exception for all llmXive pipeline errors.
    
    This serves as the root of the exception hierarchy, allowing code to
    catch all llmXive-specific errors with a single handler while still
    being able to distinguish specific error types.
    """
    
    def __init__(self, message: str, context: Optional[dict] = None):
        """
        Initialize the base exception.
        
        Args:
            message: Human-readable error description.
            context: Optional dictionary of contextual data (e.g., file paths,
                     configuration values, or state at the time of error).
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}
    
    def __str__(self) -> str:
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} (Context: {context_str})"
        return self.message


class DatasetUnavailableError(LlmXiveError):
    """
    Raised when a required dataset cannot be fetched or accessed.
    
    This exception is used specifically for data loading failures where
    the dataset is missing, corrupted, or the download source is unreachable.
    
    CRITICAL: This exception must NOT be caught and suppressed with synthetic
    fallbacks. The pipeline must fail loudly to ensure data integrity.
    
    Attributes:
        dataset_name: Name or identifier of the missing dataset.
        source_url: URL or path where the dataset was expected to come from.
        reason: Specific reason for unavailability (e.g., "404 Not Found",
               "Permission denied", "Checksum mismatch").
    """
    
    def __init__(
        self,
        message: str,
        dataset_name: Optional[str] = None,
        source_url: Optional[str] = None,
        reason: Optional[str] = None
    ):
        context = {}
        if dataset_name:
            context["dataset_name"] = dataset_name
        if source_url:
            context["source_url"] = source_url
        if reason:
            context["reason"] = reason
        
        super().__init__(message, context)
        self.dataset_name = dataset_name
        self.source_url = source_url
        self.reason = reason


class PerceptionInferenceError(LlmXiveError):
    """
    Raised when the perception module (YOLO/ONNX) fails during inference.
    
    This covers errors such as model loading failures, invalid input shapes,
    or ONNX runtime execution errors.
    """
    pass


class SymbolicTransformationError(LlmXiveError):
    """
    Raised when transforming raw visual trajectories into symbolic states fails.
    
    This includes schema validation errors, missing fields in raw data, or
    logic errors in the transformation pipeline.
    """
    pass


class ValidationThresholdError(LlmXiveError):
    """
    Raised when validation metrics fail to meet configured thresholds.
    
    Used for quality control checks on perception accuracy, training convergence,
    or evaluation success rates.
    """
    
    def __init__(
        self,
        message: str,
        metric_name: str,
        actual_value: float,
        threshold: float
    ):
        context = {
            "metric_name": metric_name,
            "actual_value": actual_value,
            "threshold": threshold
        }
        super().__init__(message, context)
        self.metric_name = metric_name
        self.actual_value = actual_value
        self.threshold = threshold


class BaselineUnavailableError(LlmXiveError):
    """
    Raised when the required Baseline-Guava (Visual) agent model is missing.
    
    Per the project specification, the visual baseline is the primary comparison
    target. If this model is unavailable, the research question cannot be answered,
    and the pipeline must halt with exit code 1.
    """
    pass


class GroundTruthSchemaMissingError(LlmXiveError):
    """
    Raised when ground truth annotation files exist but lack required schema keys.
    
    This ensures that the pipeline does not proceed with malformed ground truth
    data that would lead to incorrect evaluation metrics.
    """
    pass


class EnvironmentConfigError(LlmXiveError):
    """
    Raised when the execution environment does not meet project constraints.
    
    Examples: GPU detected when CPU-only mode is required, insufficient RAM,
    or missing system dependencies.
    """
    pass