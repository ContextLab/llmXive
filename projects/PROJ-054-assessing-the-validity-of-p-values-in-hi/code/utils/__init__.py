"""
Utilities package for simulation, regularization, and exceptions.
"""
from .exceptions import (
    HighDimensionalInstabilityError,
    SimulationError,
    DataGenerationError,
    HypothesisTestError,
    AnalysisError
)
from .regularization import is_condition_number_acceptable, regularize_covariance
from .simulation import SimulationConfig, SyntheticDataset, SimulationOrchestrator
