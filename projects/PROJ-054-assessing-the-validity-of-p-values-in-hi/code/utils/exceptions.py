"""
Custom exception classes for the project.
"""

class HighDimensionalInstabilityError(Exception):
    """Raised when condition number exceeds acceptable threshold."""
    pass

class SimulationError(Exception):
    """Base class for simulation-related errors."""
    pass

class DataGenerationError(SimulationError):
    """Raised when data generation fails."""
    pass

class HypothesisTestError(Exception):
    """Raised when a hypothesis test fails."""
    pass

class AnalysisError(Exception):
    """Raised when p-value analysis fails."""
    pass
