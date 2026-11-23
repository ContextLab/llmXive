from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import numpy as np
from uuid import uuid4

@dataclass
class NormalPoint:
    """
    Represents a single Satellite Laser Ranging (SLR) normal point.
    Corresponds to the schema in contracts/normal_point.schema.yaml
    """
    timestamp: datetime
    range: float  # meters
    satellite_id: str
    station_id: str
    quality_flag: str
    id: str = field(default_factory=lambda: str(uuid4()))

@dataclass
class OrbitSolution:
    """
    Represents the result of an orbit determination fit.
    Corresponds to the schema in contracts/orbit_solution.schema.yaml
    """
    orbital_elements: Dict[str, float]  # keys: semi_major_axis_m, eccentricity, etc.
    non_gravitational_acceleration: float  # m/s²
    covariance_matrix: np.ndarray  # shape N x N
    chi2: float
    residuals: np.ndarray  # shape M
    state: np.ndarray  # shape (3,), position vector in meters (ITRS)
    id: str = field(default_factory=lambda: str(uuid4()))

@dataclass
class EotvosResult:
    """
    Represents the final Eötvös parameter estimation result.
    Corresponds to the schema in contracts/eotvos_result.schema.yaml
    """
    eta_value: float
    confidence_interval: Tuple[float, float]
    p_value: float
    sensitivity_sweep_data: Dict[str, float]  # model_name -> z_score
    id: str = field(default_factory=lambda: str(uuid4()))
