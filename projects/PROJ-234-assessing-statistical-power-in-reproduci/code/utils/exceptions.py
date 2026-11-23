"""
utils/exceptions.py
-------------------

Simple module defining custom exception types used across the utils package.
"""

class DataFetchError(RuntimeError):
    """Raised when a remote data fetch fails after all retries."""
    pass