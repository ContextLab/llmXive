"""
Custom exception classes for the project.
"""
class DataError(Exception):
    """Raised when there is an error with data processing."""
    pass

class TrainingTimeoutError(Exception):
    """Raised when training exceeds the time limit."""
    pass
