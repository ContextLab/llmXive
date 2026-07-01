"""
Custom exception classes for the llmXive molecular interactions pipeline.

These exceptions provide specific error signaling for data validation
failures and training resource constraints, allowing the main pipeline
to handle critical failures distinctly from general runtime errors.
"""

class DataError(Exception):
    """
    Raised when data validation fails or required data is missing.

    This exception is used to signal critical data issues such as:
    - Missing required fields (e.g., adhesion energy)
    - Insufficient row counts in curated datasets
    - Checksum mismatches during data verification
    - Invalid data formats that prevent processing

    Attributes:
        message (str): Human-readable explanation of the error.
        code (str, optional): Specific error code (e.g., 'E-DATA-001') for
            automated handling and logging.
    """

    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code
        super().__init__(self.message)

    def __str__(self):
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class TrainingTimeoutError(Exception):
    """
    Raised when a training process exceeds the allowed time or resource limits.

    This exception is used to enforce the hard limits defined in the
    implementation plan (e.g., 6-hour maximum runtime, 6GB RAM limit).
    It triggers checkpointing and graceful shutdown procedures.

    Attributes:
        message (str): Human-readable explanation of the timeout.
        current_duration (float, optional): Duration in seconds elapsed so far.
        limit_duration (float, optional): Maximum allowed duration in seconds.
    """

    def __init__(self, message: str, current_duration: float = None, limit_duration: float = None):
        self.message = message
        self.current_duration = current_duration
        self.limit_duration = limit_duration
        super().__init__(self.message)

    def __str__(self):
        if self.current_duration is not None and self.limit_duration is not None:
            return f"{self.message} (Elapsed: {self.current_duration:.2f}s, Limit: {self.limit_duration:.2f}s)"
        return self.message