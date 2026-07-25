"""
Error handling utilities for the coral resilience pipeline.

This module defines custom exception classes specifically for:
1. NCBI API timeouts and retry logic failures.
2. Checksum mismatches during data integrity verification.
"""

class NCBIError(Exception):
    """Base exception for all NCBI-related errors."""
    pass


class NCBITimeoutError(NCBIError):
    """
    Raised when an NCBI API request times out after exhausting retry attempts.

    Attributes:
        operation (str): The operation that failed (e.g., 'efetch', 'esearch').
        attempts (int): The number of retry attempts made.
        last_error (Exception): The underlying exception that caused the final failure.
    """
    def __init__(self, operation: str, attempts: int, last_error: Exception = None):
        self.operation = operation
        self.attempts = attempts
        self.last_error = last_error
        message = (
            f"NCBI API request for '{operation}' failed after {attempts} attempts. "
            f"Last error: {last_error}" if last_error else f"NCBI API request for '{operation}' failed after {attempts} attempts."
        )
        super().__init__(message)


class NCBIConnectionError(NCBIError):
    """Raised when a connection to NCBI servers cannot be established."""
    pass


class ChecksumError(Exception):
    """
    Base exception for data integrity verification failures.
    """
    pass


class ChecksumMismatchError(ChecksumError):
    """
    Raised when the calculated checksum of a file does not match the expected value.

    This error is fatal to the pipeline to prevent downstream corruption.

    Attributes:
        file_path (str): The path to the file that failed verification.
        expected (str): The expected checksum (e.g., SHA256).
        actual (str): The calculated checksum of the downloaded file.
    """
    def __init__(self, file_path: str, expected: str, actual: str):
        self.file_path = file_path
        self.expected = expected
        self.actual = actual
        message = (
            f"Checksum mismatch for '{file_path}'.\n"
            f"  Expected: {expected}\n"
            f"  Actual:   {actual}"
        )
        super().__init__(message)


class ChecksumFetchError(ChecksumError):
    """
    Raised when the pipeline fails to retrieve the expected checksum from the source.
    """
    pass