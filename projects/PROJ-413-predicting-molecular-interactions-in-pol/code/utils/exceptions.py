"""
Custom exception classes for the llmXive research pipeline.

These exceptions are used to enforce strict data validation and training
constraints as defined in the project plan (e.g., hard abort on missing data).
"""

class DataError(Exception):
    """
    Raised when there is an error with data processing, validation, or availability.

    This exception is used to implement the 'Hard Abort' strategy for data
    pipelines. When raised, the script should terminate immediately without
    attempting to fall back to synthetic data or proxy metrics.

    Attributes:
        message (str): The error message describing the failure.
        code (str): Optional error code (e.g., 'E-DATA-001').
    """
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code
        super().__init__(self.message)

    def __str__(self):
        if self.code:
            return f"{self.code}: {self.message}"
        return self.message


class TrainingTimeoutError(Exception):
    """
    Raised when the model training process exceeds the allowed time limit.

    Per project constraints, training must complete within a specific window
    (e.g., 6 hours). If this limit is exceeded, this exception is raised
    to trigger checkpointing and termination.

    Attributes:
        message (str): The error message describing the timeout.
        elapsed_time (float): Time elapsed in seconds before the timeout.
        limit_time (float): The configured time limit in seconds.
    """
    def __init__(self, message: str, elapsed_time: float = None, limit_time: float = None):
        self.message = message
        self.elapsed_time = elapsed_time
        self.limit_time = limit_time
        super().__init__(self.message)

    def __str__(self):
        base_msg = self.message
        if self.elapsed_time is not None and self.limit_time is not None:
            base_msg += f" (Elapsed: {self.elapsed_time:.2f}s, Limit: {self.limit_time:.2f}s)"
        return base_msg