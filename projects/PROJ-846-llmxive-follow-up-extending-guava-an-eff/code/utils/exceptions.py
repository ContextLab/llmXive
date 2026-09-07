"""
Custom exception classes for the llmXive project.

This module defines domain-specific exceptions used throughout the pipeline,
particularly for data availability and processing errors.
"""

class DatasetUnavailableError(Exception):
    """
    Raised when a required dataset cannot be fetched, downloaded, or verified.
    
    This exception is used to enforce the 'fail loudly' policy for data loading.
    It must NOT be caught with a fallback to synthetic data generation.
    
    Attributes:
        dataset_name (str): The name or identifier of the missing dataset.
        source (str): The source URL or package where the data was expected.
        reason (str): Detailed explanation of why the fetch failed.
    """
    
    def __init__(self, dataset_name: str, source: str, reason: str):
        self.dataset_name = dataset_name
        self.source = source
        self.reason = reason
        super().__init__(
            f"DatasetUnavailableError: '{dataset_name}' is unavailable. "
            f"Source: {source}. Reason: {reason}. "
            "This is a critical failure; no synthetic fallback is permitted."
        )
    
    def to_dict(self) -> dict:
        """Return the exception details as a dictionary."""
        return {
            "error_type": "DatasetUnavailableError",
            "dataset_name": self.dataset_name,
            "source": self.source,
            "reason": self.reason
        }

class PerceptionInferenceError(Exception):
    """
    Raised when the perception module (YOLO-tiny) fails to process an image.
    
    Attributes:
        frame_id (str): Identifier of the frame that failed.
        reason (str): Description of the inference failure.
    """
    
    def __init__(self, frame_id: str, reason: str):
        self.frame_id = frame_id
        self.reason = reason
        super().__init__(f"PerceptionInferenceError: Frame '{frame_id}' failed: {reason}")

class SymbolicTransformationError(Exception):
    """
    Raised when the transformation from raw pixels to symbolic observations fails.
    
    Attributes:
        trajectory_id (str): The trajectory being processed.
        frame_index (int): The specific frame index that caused the error.
        reason (str): Description of the transformation failure.
    """
    
    def __init__(self, trajectory_id: str, frame_index: int, reason: str):
        self.trajectory_id = trajectory_id
        self.frame_index = frame_index
        self.reason = reason
        super().__init__(
            f"SymbolicTransformationError: Trajectory '{trajectory_id}', "
            f"frame {frame_index} failed: {reason}"
        )

class ValidationThresholdError(Exception):
    """
    Raised when a validation metric (e.g., precision/recall) falls below the required threshold.
    
    Attributes:
        metric_name (str): Name of the metric that failed.
        observed_value (float): The value actually observed.
        threshold_value (float): The minimum required value.
    """
    
    def __init__(self, metric_name: str, observed_value: float, threshold_value: float):
        self.metric_name = metric_name
        self.observed_value = observed_value
        self.threshold_value = threshold_value
        super().__init__(
            f"ValidationThresholdError: {metric_name} ({observed_value:.4f}) "
            f"fell below threshold ({threshold_value:.4f})"
        )
