from utils.logging import get_logger

logger = get_logger(__name__)

class CorrosionPipelineError(Exception):
    """Base exception for the corrosion prediction pipeline."""
    pass

class DataInsufficientError(CorrosionPipelineError):
    """
    Raised when required data is missing, incomplete, or insufficient.
    
    Examples:
    - NIST URL missing from config
    - Dataset has < 500 records
    - ASTM G59 standard does not define a required tolerance value
    - Alloy diversity is insufficient for LOSO split
    """
    def __init__(self, message: str):
        super().__init__(message)
        logger.error(f"DataInsufficientError: {message}")

class SchemaMismatchError(CorrosionPipelineError):
    """
    Raised when data does not conform to the expected schema.
    
    Examples:
    - Null values in critical fields
    - Missing required columns
    - Type mismatches in data
    """
    def __init__(self, message: str):
        super().__init__(message)
        logger.error(f"SchemaMismatchError: {message}")