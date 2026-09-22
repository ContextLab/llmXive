"""
Data models (entities) for the Equivalence Principle Testing pipeline.

These dataclasses define the core data structures consumed by the analysis,
ingestion, and estimation modules. They align with the YAML schemas defined
in contracts/normal_point.schema.yaml, contracts/orbit_solution.schema.yaml,
and contracts/eotvos_result.schema.yaml.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import numpy as np
from uuid import uuid4


@dataclass
class NormalPoint:
    """
    Represents a single Satellite Laser Ranging (SLR) normal point observation.
    
    Matches the schema in contracts/normal_point.schema.yaml.
    """
    timestamp: datetime
    range: float  # meters
    satellite_id: str
    station_id: str
    quality_flag: str
    # Optional metadata for traceability
    observation_id: str = field(default_factory=lambda: str(uuid4()))
    residual: Optional[float] = None  # meters, if available from initial fit
    weight: float = 1.0

@dataclass
class OrbitSolution:
    """
    Represents the result of an orbit determination fit (separate or joint).
    
    Matches the schema in contracts/orbit_solution.schema.yaml.
    
    Fields:
        orbital_elements: Dict containing 'semi_major_axis_m', 'eccentricity', 
                          'inclination_rad', 'raan_rad', 'arg_perigee_rad', 
                          'mean_anomaly_rad'.
        non_gravitational_acceleration: float (m/s^2)
        covariance_matrix: np.ndarray (N x N)
        chi2: float (goodness of fit)
        residuals: np.ndarray (M,)
        state: np.ndarray (3,) Position vector in meters (ITRS or GCRS).
        solution_id: Unique identifier for this solution.
        converged: Boolean indicating if the solver converged.
        iterations: Number of iterations performed.
    """
    orbital_elements: Dict[str, float]
    non_gravitational_acceleration: float
    covariance_matrix: np.ndarray
    chi2: float
    residuals: np.ndarray
    state: np.ndarray  # Shape (3,)
    solution_id: str = field(default_factory=lambda: str(uuid4()))
    converged: bool = True
    iterations: int = 0
    # Metadata for joint fits
    satellite_ids: List[str] = field(default_factory=list)
    # Differential acceleration parameter (if part of a joint fit)
    differential_acceleration: Optional[float] = None

@dataclass
class EotvosResult:
    """
    Represents the calculated Eötvös parameter and associated statistics.
    
    Matches the schema in contracts/eotvos_result.schema.yaml.
    
    Fields:
        eta_value: float (The Eötvös parameter |a_c|/g)
        confidence_interval: Tuple[float, float] (95% CI lower, upper)
        p_value: float (Statistical significance)
        sensitivity_sweep_data: Dict mapping model_name -> z_score
        result_id: Unique identifier.
        method: String describing the estimation method used.
        benchmark_comparison: Dict containing 'limit', 'met', 'difference'.
    """
    eta_value: float
    confidence_interval: Tuple[float, float]
    p_value: float
    sensitivity_sweep_data: Dict[str, float]
    result_id: str = field(default_factory=lambda: str(uuid4()))
    method: str = "Joint Least Squares"
    benchmark_comparison: Optional[Dict[str, Any]] = None
    # Additional context
    satellites_used: List[str] = field(default_factory=list)
    local_gravity_g: float = 0.0