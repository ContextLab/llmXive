"""
Custom exceptions for the high-dimensional p-value analysis pipeline.

Defines error codes and exception classes for handling numerical
instabilities and validation failures in high-dimensional statistics.
"""

class HighDimensionalInstabilityError(Exception):
    """
    Exception raised when high-dimensional numerical instability is detected.

    This error occurs when:
    - Condition number of a matrix exceeds 10^12 (FR-009)
    - Matrix is singular or near-singular in high-dimensional settings
    - Numerical precision issues prevent stable computation

    Attributes
    ----------
    error_code : str
        The specific error code associated with this failure.
    condition_number : float, optional
        The computed condition number that triggered the error.
    matrix_shape : tuple, optional
        The shape of the problematic matrix.
    """

    ERR_HIGH_DIMENSIONAL_INSTABILITY = "ERR_HIGH_DIMENSIONAL_INSTABILITY"

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_HIGH_DIMENSIONAL_INSTABILITY",
        condition_number: float = None,
        matrix_shape: tuple = None
    ):
        self.error_code = error_code
        self.condition_number = condition_number
        self.matrix_shape = matrix_shape

        full_message = message
        if condition_number is not None:
            full_message += f" (condition number: {condition_number:.2e})"
        if matrix_shape is not None:
            full_message += f" (matrix shape: {matrix_shape})"

        super().__init__(full_message)

class SimulationError(Exception):
    """Base exception for simulation-related errors."""
    pass

class DataGenerationError(SimulationError):
    """Exception raised during synthetic data generation."""
    pass

class HypothesisTestError(SimulationError):
    """Exception raised during hypothesis testing."""
    pass

class AnalysisError(SimulationError):
    """Exception raised during p-value distribution analysis."""
    pass