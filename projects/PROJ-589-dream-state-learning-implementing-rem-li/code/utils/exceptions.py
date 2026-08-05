import time

class DataIntegrityError(Exception):
    """Raised when dataset checksum verification fails."""
    pass

class TimeLimitExceeded(Exception):
    """Raised when the wall-clock execution time exceeds the configured limit."""
    def __init__(self, message="Execution time limit exceeded", elapsed_seconds=None, limit_seconds=None):
        self.elapsed_seconds = elapsed_seconds
        self.limit_seconds = limit_seconds
        full_message = f"{message} (Elapsed: {elapsed_seconds:.2f}s, Limit: {limit_seconds}s)" if elapsed_seconds is not None else message
        super().__init__(full_message)
