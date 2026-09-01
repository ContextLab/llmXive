"""
Custom exceptions for the glass transition temperature prediction pipeline.

These exceptions are designed to fail loudly when real data operations fail,
preventing silent fallbacks to synthetic data which violates the project's
core research integrity constraints.
"""

class GlassPipelineError(Exception):
    """Base exception for all pipeline-related errors."""
    pass

class DataFetchError(GlassPipelineError):
    """
    Raised when fetching data from a real external source fails.

    This exception must be raised explicitly when:
    - Network requests to Zenodo/NIST fail
    - Data integrity checks (checksums) fail
    - Required data files are missing or corrupted

    DO NOT catch this exception to fall back to synthetic data.
    The pipeline must halt to ensure research validity.
    """
    def __init__(self, message: str, source: str = None, details: dict = None):
        super().__init__(message)
        self.source = source
        self.details = details or {}

class DataValidationError(GlassPipelineError):
    """
    Raised when data fails domain-specific validation checks.

    Examples:
    - Invalid chemical formulas that cannot be parsed
    - Missing target values ($T_g$) in the dataset
    - Compositional fractions that do not sum to 1.0 within tolerance
    """
    def __init__(self, message: str, record_id: str = None, field: str = None):
        super().__init__(message)
        self.record_id = record_id
        self.field = field

class ConfigurationError(GlassPipelineError):
    """
    Raised when environment configuration is invalid or missing.

    Examples:
    - Missing Zenodo DOI
    - Invalid API credentials
    - Missing required environment variables
    """
    def __init__(self, message: str, missing_keys: list = None):
        super().__init__(message)
        self.missing_keys = missing_keys or []

class FeaturizationError(GlassPipelineError):
    """
    Raised when featurization steps fail.

    Examples:
    - pymatgen fails to parse a composition
    - matminer element property lookup fails
    - Dimensionality mismatch in feature matrix
    """
    def __init__(self, message: str, formula: str = None, error_type: str = None):
        super().__init__(message)
        self.formula = formula
        self.error_type = error_type

class ModelTrainingError(GlassPipelineError):
    """
    Raised when model training or evaluation fails.

    Examples:
    - Grid search fails due to invalid hyperparameters
    - Cross-validation split fails
    - Metric calculation raises exception
    """
    def __init__(self, message: str, model_type: str = None, fold: int = None):
        super().__init__(message)
        self.model_type = model_type
        self.fold = fold

def raise_loudly(error_class, message: str, **kwargs):
    """
    Helper function to raise a specific error class with consistent formatting.

    This enforces the "fail loudly" principle by ensuring errors are never
    silently caught and ignored.

    Args:
        error_class: The exception class to raise
        message: The error message
        **kwargs: Additional context to include in the exception
    """
    raise error_class(message, **kwargs)
