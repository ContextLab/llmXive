"""
Custom exception classes for the llmXive automated science pipeline.

These exceptions are used to signal specific failure conditions during
dataset operations, model training, and validation processes.
"""

class LlmXiveError(Exception):
    """Base exception for all llmXive pipeline errors."""
    pass

class DatasetUnavailableError(LlmXiveError):
    """
    Raised when a required dataset cannot be fetched, downloaded, or accessed.

    This error is raised when:
    - A remote dataset source is unreachable.
    - A local dataset file is missing or corrupted.
    - Ground truth annotations are missing and cannot be derived.

    The pipeline must fail loudly upon this error; no synthetic fallbacks are permitted.
    """
    pass

class ConvergenceTimeoutError(LlmXiveError):
    """
    Raised when a training process fails to converge within the specified time or metric thresholds.

    This error is raised when:
    - Training exceeds the maximum allowed duration (e.g., 4 hours on CPU).
    - The loss reduction is below the required threshold (e.g., <15% decrease).

    Handling this error typically triggers a GPU escape hatch or halts the experiment.
    """
    pass

class PerceptionInferenceError(LlmXiveError):
    """
    Raised when the perception module (e.g., YOLO) fails to process an input frame.

    Causes may include:
    - Corrupted image data.
    - ONNX runtime execution errors.
    - Model file missing or invalid.
    """
    pass

class SymbolicTransformationError(LlmXiveError):
    """
    Raised when the transformation from visual trajectories to symbolic states fails.

    This may occur due to:
    - Missing perception logs.
    - Schema mismatches in the symbolic output.
    - Inability to serialize the trajectory data.
    """
    pass

class ValidationThresholdError(LlmXiveError):
    """
    Raised when a validation metric fails to meet the required threshold.

    Examples:
    - Perception precision/recall below acceptable levels.
    - Transformation time exceeding the 150ms/frame limit.
    """
    pass

class BaselineUnavailableError(LlmXiveError):
    """
    Raised when the required Baseline-Guava (Visual) agent model is missing.

    Per the Spec, if this baseline is unavailable, the primary comparison (T036b)
    cannot be performed, and the project should halt the evaluation phase.
    """
    pass

class GroundTruthSchemaMissingError(LlmXiveError):
    """
    Raised when ground truth annotations are missing required keys (e.g., 'annotations', 'bboxes').

    This indicates the dataset is invalid for training or evaluation purposes.
    """
    pass

class EnvironmentConfigError(LlmXiveError):
    """
    Raised when the execution environment violates constraints (e.g., GPU detected in CPU-only mode).

    This error is raised by `check_cpu_constraints()` if `CUDA_VISIBLE_DEVICES` is set
    and the `--cpu-only` flag is not active.
    """
    pass
