from dataclasses import dataclass, field
from typing import List, Optional
import numpy as np


@dataclass
class SimulationConfig:
    """
    Configuration for the RD simulation study.
    Corresponds to the 'simulation' section in config/simulation.yaml.
    """
    sample_size: int
    true_effect: float
    seed: int
    exclusion_restriction: float  # Coefficient for Z* in the DGP for missingness


@dataclass
class MissingnessPattern:
    """
    Represents the generated missingness mask.
    The 'mask' attribute is a boolean indicating the status of the pattern generation
    logic (e.g., True if a valid mask was successfully generated, False otherwise),
    as strictly required by the task specification.
    """
    mask: bool
    mechanism: Optional[str] = None  # 'MCAR', 'MAR', 'MNAR'
    rate: Optional[float] = None
    seed: Optional[int] = None


@dataclass
class EstimationResult:
    """
    Results from a single estimation run (one replication, one estimator).
    """
    estimate: float
    se: float
    ci_lower: Optional[float] = None
    ci_upper: Optional[float] = None
    mechanism: Optional[str] = None
    rate: Optional[float] = None
    estimator_name: Optional[str] = None
    converged: bool = True
    error_message: Optional[str] = None


@dataclass
class AggregatedMetric:
    """
    Aggregated metrics across multiple replications for a specific configuration.
    """
    bias: float
    rmse: float
    coverage: float
    mean_se: Optional[float] = None
    mechanism: Optional[str] = None
    rate: Optional[float] = None
    estimator_name: Optional[str] = None
    n_replications: int = 0