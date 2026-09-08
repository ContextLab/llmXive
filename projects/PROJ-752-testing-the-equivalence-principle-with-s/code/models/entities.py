"""
Data model entities for the Equivalence Principle Testing pipeline.

Defines core dataclasses: NormalPoint, OrbitSolution, and EotvosResult
matching the schema definitions in contracts/.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import numpy as np
from uuid import uuid4

@dataclass
class NormalPoint:
    """
    Represents a single SLR (Satellite Laser Ranging) normal point observation.
    
    Matches schema: contracts/normal_point.schema.yaml
    """
    timestamp: datetime
    range: float  # in meters
    satellite_id: str
    station_id: str
    quality_flag: str  # e.g., 'GOOD', 'MARGINAL', 'BAD'
    
    # Optional metadata
    range_rate: Optional[float] = None
    number_of_returns: Optional[int] = None
    rms_error: Optional[float] = None
    station_name: Optional[str] = None
    
    def __post_init__(self):
        """Validate types and ranges."""
        if not isinstance(self.timestamp, datetime):
            raise TypeError(f"timestamp must be datetime, got {type(self.timestamp)}")
        if not isinstance(self.range, (int, float)):
            raise TypeError(f"range must be numeric, got {type(self.range)}")
        if self.range <= 0:
            raise ValueError(f"range must be positive, got {self.range}")
        if not isinstance(self.satellite_id, str) or not self.satellite_id.strip():
            raise ValueError("satellite_id must be a non-empty string")
        if not isinstance(self.station_id, str) or not self.station_id.strip():
            raise ValueError("station_id must be a non-empty string")
        if not isinstance(self.quality_flag, str):
            raise TypeError(f"quality_flag must be string, got {type(self.quality_flag)}")

@dataclass
class OrbitSolution:
    """
    Represents the results of an orbit determination fit.
    
    Matches schema: contracts/orbit_solution.schema.yaml
    """
    state_vector: np.ndarray  # [x, y, z, vx, vy, vz] in meters and m/s
    non_gravitational_acceleration: np.ndarray  # [ax, ay, az] in m/s^2
    covariance_matrix: np.ndarray  # Full covariance of state + params
    chi2: float  # Reduced chi-squared of the fit
    residuals: np.ndarray  # Array of observation residuals (meters)
    
    # Metadata
    solution_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    satellite_ids: List[str] = field(default_factory=list)
    station_ids: List[str] = field(default_factory=list)
    n_observations: int = 0
    n_parameters: int = 0
    convergence_status: str = "converged"  # 'converged', 'max_iterations', 'failed'
    solver_type: str = "levenberg_marquardt"
    
    # Optional differential acceleration parameter (for joint fits)
    differential_acceleration_ac: Optional[float] = None
    g_local: Optional[float] = None
    
    def __post_init__(self):
        """Validate shapes and types."""
        if not isinstance(self.state_vector, np.ndarray):
            self.state_vector = np.array(self.state_vector)
        if self.state_vector.shape[0] != 6:
            raise ValueError(f"state_vector must have 6 components, got {self.state_vector.shape}")
        
        if not isinstance(self.non_gravitational_acceleration, np.ndarray):
            self.non_gravitational_acceleration = np.array(self.non_gravitational_acceleration)
        if self.non_gravitational_acceleration.shape[0] != 3:
            raise ValueError(f"non_gravitational_acceleration must have 3 components, got {self.non_gravitational_acceleration.shape}")
        
        if not isinstance(self.covariance_matrix, np.ndarray):
            self.covariance_matrix = np.array(self.covariance_matrix)
        
        if not isinstance(self.residuals, np.ndarray):
            self.residuals = np.array(self.residuals)
        
        if not isinstance(self.chi2, (int, float)):
            raise TypeError(f"chi2 must be numeric, got {type(self.chi2)}")

@dataclass
class EotvosResult:
    """
    Represents the computed Eötvös parameter and statistical validation.
    
    Matches schema: contracts/eotvos_result.schema.yaml
    """
    eta_value: float  # The Eötvös parameter value
    confidence_interval: List[float]  # [lower, upper] for 95% CI
    p_value: float  # P-value from F-test or similar
    sensitivity_sweep_data: Dict[str, Any]  # Results from geopotential sensitivity analysis
    
    # Metadata
    result_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    satellite_pair: List[str] = field(default_factory=list)
    geopotential_model: str = "GGM05C"
    solver_status: str = "success"
    
    # Statistical details
    chi2_null: Optional[float] = None
    chi2_alt: Optional[float] = None
    delta_chi2: Optional[float] = None
    f_statistic: Optional[float] = None
    bic_null: Optional[float] = None
    bic_alt: Optional[float] = None
    
    # Consistency check results
    consistency_check_passed: Optional[bool] = None
    separate_fit_difference: Optional[float] = None
    joint_estimate_ac: Optional[float] = None
    
    # Benchmark comparison
    benchmark_limit: Optional[float] = None
    precision_goal_met: Optional[bool] = None
    benchmark_source: Optional[str] = None
    
    def __post_init__(self):
        """Validate types and ranges."""
        if not isinstance(self.eta_value, (int, float)):
            raise TypeError(f"eta_value must be numeric, got {type(self.eta_value)}")
        if not isinstance(self.confidence_interval, list) or len(self.confidence_interval) != 2:
            raise ValueError("confidence_interval must be a list of 2 floats")
        if not isinstance(self.p_value, (int, float)):
            raise TypeError(f"p_value must be numeric, got {type(self.p_value)}")
        if not isinstance(self.sensitivity_sweep_data, dict):
            raise TypeError(f"sensitivity_sweep_data must be a dict, got {type(self.sensitivity_sweep_data)}")
        
        # Validate CI order
        if self.confidence_interval[0] > self.confidence_interval[1]:
            raise ValueError("confidence_interval[0] must be <= confidence_interval[1]")
        
        # Validate p-value range
        if not (0.0 <= self.p_value <= 1.0):
            raise ValueError(f"p_value must be in [0, 1], got {self.p_value}")