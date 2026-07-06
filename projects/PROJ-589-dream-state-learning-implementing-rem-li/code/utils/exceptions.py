"""
Custom exception definitions for the Dream-State Learning pipeline.

This module provides specialized exception classes to enforce data integrity
and handle specific failure modes defined in the project contracts.
"""


class DataIntegrityError(Exception):
    """
    Raised when a data integrity check fails, specifically for checksum
    verification mismatches.

    This exception is used by the data loader to abort execution when
    downloaded data (e.g., GLUE/SuperGLUE subsets) does not match the
    expected SHA-256 hash, preventing the use of corrupted or tampered
    datasets.

    Attributes:
        message (str): Human-readable explanation of the error.
        expected_hash (str, optional): The expected SHA-256 hash.
        actual_hash (str, optional): The computed SHA-256 hash of the file.
    """

    def __init__(self, message: str, expected_hash: str = None, actual_hash: str = None):
        self.message = message
        self.expected_hash = expected_hash
        self.actual_hash = actual_hash

        if expected_hash and actual_hash:
            full_message = (
                f"{message}. "
                f"Expected: {expected_hash}, "
                f"Actual: {actual_hash}"
            )
        else:
            full_message = message

        super().__init__(full_message)