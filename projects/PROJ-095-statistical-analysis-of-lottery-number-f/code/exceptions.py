"""
Custom exceptions for the Lottery Draw Integrity and Anomaly Detection pipeline.

These exceptions are used to handle specific data errors and validation failures
encountered during ingestion, processing, and analysis.
"""


class LotteryDataError(Exception):
    """Base exception for all lottery data-related errors."""
    pass


class MissingSalesError(LotteryDataError):
    """
    Raised when expected sales data is missing or unavailable for a draw.

    This is distinct from a format error; the row exists but the specific
    'total_sales' field is null, empty, or unparseable.
    """
    pass


class InvalidDrawFormatError(LotteryDataError):
    """
    Raised when a draw record fails structural validation.

    Examples:
    - Incorrect number of balls in a draw.
    - Non-numeric values where integers are expected.
    - Missing required fields (e.g., draw_date).
    """
    pass


class ChecksumVerificationError(LotteryDataError):
    """
    Raised when the checksum of a downloaded or loaded file does not match
    the expected value, indicating potential data corruption or tampering.
    """
    pass


class DataSourceUnavailableError(LotteryDataError):
    """
    Raised when the configured data source URL is unreachable or returns
    a non-success HTTP status code during ingestion.
    """
    pass