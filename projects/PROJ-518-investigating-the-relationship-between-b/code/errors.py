from typing import Optional

class DataMissingCreativityError(Exception):
    """
    Exception raised when required creativity data (CAQ) is missing.
    """
    def __init__(self, message: str, missing_field: Optional[str] = None):
        super().__init__(message)
        self.missing_field = missing_field
