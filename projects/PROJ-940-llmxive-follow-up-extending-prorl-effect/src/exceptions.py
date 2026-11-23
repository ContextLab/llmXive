"""
Custom exception classes for the llmXive ProRL pipeline.

These exceptions provide specific error types for different failure modes
encountered during graph construction, data loading, path generation, and evaluation.
"""

class LlmXiveError(Exception):
    """Base exception for all llmXive pipeline errors."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class DataFetchError(LlmXiveError):
    """Raised when fetching or loading real external data fails.

    This exception is raised when:
    - The datasets library cannot connect to Hugging Face Hub
    - A requested dataset ID does not exist or is inaccessible
    - Streaming data fetch encounters a network error
    - Data format validation fails after retrieval

    Per FR-001, this must fail loudly without synthetic fallback.
    """

class GraphDisconnectionError(LlmXiveError):
    """Raised when a graph traversal cannot reach connected components.

    This occurs when:
    - A seed item has no similarity edges above the threshold
    - Path generation cannot extend beyond a disconnected node
    - The similarity graph is fragmented and a required component is missing
    """

class InvalidConfigurationError(LlmXiveError):
    """Raised when configuration parameters are invalid or inconsistent.

    Examples:
    - Path length L < 1
    - Beam width B < 1
    - Alpha <= 0
    - Invalid dataset selection
    """

class ResourceLimitError(LlmXiveError):
    """Raised when resource constraints (RAM, disk) are exceeded.

    This exception is raised by the resource enforcement logic when:
    - Dataset size exceeds available memory without sampling
    - Disk space is insufficient for intermediate results
    - Processing time exceeds configured limits
    """

class PathGenerationError(LlmXiveError):
    """Raised when path generation algorithms fail.

    Causes:
    - Beam search cannot find valid paths of requested length
    - Greedy traversal gets stuck (no valid neighbors)
    - Invalid seed item provided
    """

class EvaluationError(LlmXiveError):
    """Raised during metric calculation or evaluation pipeline failures.

    Causes:
    - Missing ground truth data for test set
    - Invalid metric parameters (e.g., K < 1)
    - Data type mismatches in metric computation
    """

class StatisticalTestError(LlmXiveError):
    """Raised when statistical significance tests cannot be performed.

    Causes:
    - Insufficient samples for Shapiro-Wilk test (n < 3)
    - Paired data mismatch between comparison groups
    - scipy.stats functions raise unexpected errors
    """

class FileIOError(LlmXiveError):
    """Raised when file operations fail.

    Causes:
    - Permission denied
    - File not found
    - Corrupted or invalid format (JSON/Parquet)
    - Checksum verification failure (per T006)
    """