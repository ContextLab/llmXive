"""
Custom exception classes for the crystal structure prediction pipeline.
These exceptions are used to explicitly handle specific failure modes
without falling back to synthetic data.
"""

class DownloadError(Exception):
    """
    Raised when a data download operation fails (e.g., network error,
    missing remote file, authentication failure).
    
    This exception is critical for enforcing the 'fail loudly' principle.
    When raised, the pipeline must stop or skip the specific item, but
    must NOT generate synthetic data to replace the missing real data.
    """
    def __init__(self, message: str, source: str = None):
        self.source = source
        self.message = f"Download failed from {source}: {message}" if source else f"Download failed: {message}"
        super().__init__(self.message)


class MemoryErrorHandled(Exception):
    """
    Raised when a MemoryError is caught and handled explicitly.
    
    Unlike the built-in MemoryError, this custom exception indicates
    that the system detected a memory constraint and made a deliberate
    decision (e.g., to skip a large molecule or reduce a batch size)
    rather than crashing. It allows the pipeline to log the event
    and continue processing other items.
    """
    def __init__(self, message: str, context: dict = None):
        self.context = context or {}
        self.message = f"Memory limit handled: {message}"
        super().__init__(self.message)


class ValidationError(Exception):
    """
    Raised when data validation fails (e.g., missing required fields,
    malformed structure, invalid fingerprint).
    
    This ensures that corrupted or invalid data is rejected immediately
    rather than being processed or used to train models.
    """
    def __init__(self, message: str, field: str = None, value: Any = None):
        self.field = field
        self.value = value
        self.message = f"Validation failed on '{field}': {message}" if field else f"Validation failed: {message}"
        super().__init__(self.message)
