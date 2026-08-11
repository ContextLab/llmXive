class HighDimensionalInstabilityError(Exception):
    """Raised when high-dimensional instability is detected (e.g., condition number > 10^12)."""
    pass

class SimulationError(Exception):
    """General simulation error."""
    pass

class DataGenerationError(Exception):
    """Error during data generation."""
    pass

class HypothesisTestError(Exception):
    """Error during hypothesis testing."""
    pass

class AnalysisError(Exception):
    """Error during analysis."""
    pass
