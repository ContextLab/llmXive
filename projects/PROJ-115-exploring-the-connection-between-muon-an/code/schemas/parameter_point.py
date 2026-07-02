"""
Schema definition for the ParameterPoint data model.

This module defines the structure for a single point in the parameter space
of the muon g-2 dark matter model, including masses, couplings, and derived
physical observables.

Corresponds to FR-001 (Parameter Point Definition) and FR-005 (Data Contracts).
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import math


@dataclass
class ParameterPoint:
    """
    Represents a single point in the dark matter parameter space.
    
    Attributes:
        m_dm: Dark matter fermion mass (MeV).
        m_v: Vector mediator mass (MeV).
        g: Dark coupling constant (dimensionless).
        omega_dm_h2: Dark matter relic density times h^2 (dimensionless).
        delta_a_mu: Contribution to the muon anomalous magnetic dipole moment (dimensionless).
        sigma_si: Spin-independent scattering cross-section (cm^2).
        is_viable: Boolean flag indicating if the point satisfies all experimental constraints.
        constraints: Dictionary of constraint statuses (e.g., {'planck': True, 'xenon': False}).
        notes: Optional string for additional context or flags.
    """
    m_dm: float
    m_v: float
    g: float
    
    # Derived observables (optional, can be None if not yet calculated)
    omega_dm_h2: Optional[float] = None
    delta_a_mu: Optional[float] = None
    sigma_si: Optional[float] = None
    
    # Validation status
    is_viable: bool = False
    constraints: Dict[str, bool] = field(default_factory=dict)
    notes: Optional[str] = None
    
    def __post_init__(self):
        """Validate physical constraints on input parameters."""
        if self.m_dm <= 0:
            raise ValueError(f"m_dm must be positive, got {self.m_dm}")
        if self.m_v <= 0:
            raise ValueError(f"m_v must be positive, got {self.m_v}")
        if self.g <= 0:
            raise ValueError(f"g must be positive, got {self.g}")
        
        # Check for non-finite values
        if not math.isfinite(self.m_dm) or not math.isfinite(self.m_v) or not math.isfinite(self.g):
            raise ValueError("Input parameters must be finite numbers")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataclass instance to a dictionary for serialization."""
        return {
            "m_dm": self.m_dm,
            "m_v": self.m_v,
            "g": self.g,
            "omega_dm_h2": self.omega_dm_h2,
            "delta_a_mu": self.delta_a_mu,
            "sigma_si": self.sigma_si,
            "is_viable": self.is_viable,
            "constraints": self.constraints,
            "notes": self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ParameterPoint":
        """Create a ParameterPoint instance from a dictionary."""
        # Handle optional fields that might be missing or null
        return cls(
            m_dm=data["m_dm"],
            m_v=data["m_v"],
            g=data["g"],
            omega_dm_h2=data.get("omega_dm_h2"),
            delta_a_mu=data.get("delta_a_mu"),
            sigma_si=data.get("sigma_si"),
            is_viable=data.get("is_viable", False),
            constraints=data.get("constraints", {}),
            notes=data.get("notes")
        )
    
    def validate_observables(self) -> bool:
        """
        Validate that any calculated observables are physically sensible.
        
        Returns:
            True if all present observables are non-negative and finite.
        """
        for attr in ["omega_dm_h2", "delta_a_mu", "sigma_si"]:
            val = getattr(self, attr)
            if val is not None:
                if not math.isfinite(val):
                    return False
                # Most physical observables in this context should be non-negative
                # Note: delta_a_mu can technically be negative in some models, 
                # but for this specific vector mediator model it's positive.
                # We allow negative for delta_a_mu to be safe, but check others.
                if attr in ["omega_dm_h2", "sigma_si"] and val < 0:
                    return False
        return True
    
    def __str__(self) -> str:
        return (
            f"ParameterPoint(m_dm={self.m_dm:.3f} MeV, m_v={self.m_v:.3f} MeV, "
            f"g={self.g:.3e}, is_viable={self.is_viable})"
        )

def validate_parameter_point(point: ParameterPoint) -> tuple[bool, str]:
    """
    Comprehensive validation of a ParameterPoint instance.
    
    Args:
        point: The ParameterPoint instance to validate.
        
    Returns:
        A tuple (is_valid, error_message). If is_valid is True, error_message is empty.
    """
    try:
        # Check basic dataclass invariants
        if not math.isfinite(point.m_dm) or point.m_dm <= 0:
            return False, f"Invalid m_dm: {point.m_dm}"
        if not math.isfinite(point.m_v) or point.m_v <= 0:
            return False, f"Invalid m_v: {point.m_v}"
        if not math.isfinite(point.g) or point.g <= 0:
            return False, f"Invalid g: {point.g}"
        
        # Check derived observables if present
        if point.omega_dm_h2 is not None and (not math.isfinite(point.omega_dm_h2) or point.omega_dm_h2 < 0):
            return False, f"Invalid omega_dm_h2: {point.omega_dm_h2}"
        
        if point.sigma_si is not None and (not math.isfinite(point.sigma_si) or point.sigma_si < 0):
            return False, f"Invalid sigma_si: {point.sigma_si}"
        
        # Check constraint dictionary consistency
        if not isinstance(point.constraints, dict):
            return False, "Constraints must be a dictionary"
        
        return True, ""
        
    except Exception as e:
        return False, f"Validation error: {str(e)}"
