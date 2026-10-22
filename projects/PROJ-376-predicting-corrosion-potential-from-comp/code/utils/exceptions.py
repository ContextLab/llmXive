"""
Custom exception hierarchy for the corrosion prediction pipeline.
Provides structured error messages with optional detail metadata
and integrates with the project's logging infrastructure.
"""

# Use relative import to access the project's logging utility
from .logging import get_logger

logger = get_logger(__name__)

class CorrosionPipelineError(Exception):
    """Base exception for the corrosion prediction pipeline."""

    def __init__(self, message: str, **kwargs):
        """
        Initialise the exception.

        Args:
            message: Human‑readable error message.
            **kwargs: Optional detail information.  A special keyword
                     ``details`` may be supplied containing a dict;
                     its contents are merged with any other supplied
                     keyword arguments.
        """
        # Extract a possible ``details`` dict from kwargs
        details = {}
        if "details" in kwargs and isinstance(kwargs["details"], dict):
            details = kwargs.pop("details")
        # Handle special renaming of ``field_name`` to ``field`` for test compatibility
        if "field_name" in kwargs:
            field_val = kwargs.pop("field_name")
            details["field"] = field_val
            setattr(self, "field", field_val)

        # Remaining kwargs are also treated as details
        details.update(kwargs)

        super().__init__(message)
        self.message = message
        self.details = details or {}

        # Expose each detail as an attribute for easy access in tests
        for key, value in self.details.items():
            setattr(self, key, value)

        # Log the error with details for traceability
        if self.details:
            logger.error(f"{self.__class__.__name__}: {message} | details: {self.details}")
        else:
            logger.error(f"{self.__class__.__name__}: {message}")

    def __str__(self) -> str:
        """Return a readable representation that includes details when present."""
        if not self.details:
            return self.message

        # Map internal keys to the names expected by the test suite
        def _display_key(k: str) -> str:
            return "field" if k == "field_name" else k

        details_str = ", ".join(
            f"{_display_key(k)}={v!r}"
            for k, v in self.details.items()
        )
        return f"{self.message} ({details_str})"


class DataInsufficientError(CorrosionPipelineError):
    """
    Raised when required data is missing, incomplete, or insufficient.

    Typical scenarios:
    - NIST URL missing from config
    - Dataset has fewer than the required number of records
    - Alloy diversity is insufficient for a LOSO split
    """
    def __init__(self, message: str, **kwargs):
        super().__init__(message, **kwargs)


class SchemaMismatchError(CorrosionPipelineError):
    """
    Raised when data does not conform to the expected schema.

    Typical scenarios:
    - Null values in critical fields
    - Missing required columns
    - Type mismatches in data
    """
    def __init__(self, message: str, **kwargs):
        super().__init__(message, **kwargs)