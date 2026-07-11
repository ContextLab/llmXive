"""
Data model for Kepler exoplanet records.

Matches contracts/planet_record.schema.yaml structure.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import math
from datetime import datetime


@dataclass
class PlanetRecord:
    """
    Represents a single exoplanet record from the merged Kepler catalog.
    
    Attributes correspond to the schema defined in contracts/planet_record.schema.yaml.
    """
    # Core Identifiers
    kic_id: int
    kepler_id: Optional[int] = None
    planet_name: Optional[str] = None
    
    # Orbital Parameters
    period: float
    period_uncertainty: float
    period_unit: str = "days"
    
    # Planetary Parameters
    radius: float
    radius_uncertainty: float
    radius_unit: str = "Earth_radii"
    
    # Stellar Parameters (Required for analysis)
    stellar_teff: float
    stellar_teff_uncertainty: float
    stellar_logg: Optional[float] = None
    stellar_mass: Optional[float] = None
    stellar_radius: Optional[float] = None
    
    # Derived/Calculated Fields
    radius_gap_bin: Optional[str] = None
    gap_location: Optional[float] = None
    
    # Metadata
    source: str = "kepler_dr25"
    download_timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    flags: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate data types and basic constraints."""
        if self.period <= 0:
            raise ValueError(f"Period must be positive, got {self.period}")
        if self.radius <= 0:
            raise ValueError(f"Radius must be positive, got {self.radius}")
        if self.stellar_teff <= 0:
            raise ValueError(f"Stellar Teff must be positive, got {self.stellar_teff}")
        
        if self.period_uncertainty < 0:
            raise ValueError(f"Period uncertainty cannot be negative, got {self.period_uncertainty}")
        if self.radius_uncertainty < 0:
            raise ValueError(f"Radius uncertainty cannot be negative, got {self.radius_uncertainty}")
        
        # Validate uncertainty percentages if provided
        if self.period_uncertainty > 0 and self.period > 0:
            pct = (self.period_uncertainty / self.period) * 100
            if pct > 100:
                # Log warning or raise depending on strictness, but allow for now
                pass

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary for serialization."""
        return {
            "kic_id": self.kic_id,
            "kepler_id": self.kepler_id,
            "planet_name": self.planet_name,
            "period": self.period,
            "period_uncertainty": self.period_uncertainty,
            "period_unit": self.period_unit,
            "radius": self.radius,
            "radius_uncertainty": self.radius_uncertainty,
            "radius_unit": self.radius_unit,
            "stellar_teff": self.stellar_teff,
            "stellar_teff_uncertainty": self.stellar_teff_uncertainty,
            "stellar_logg": self.stellar_logg,
            "stellar_mass": self.stellar_mass,
            "stellar_radius": self.stellar_radius,
            "radius_gap_bin": self.radius_gap_bin,
            "gap_location": self.gap_location,
            "source": self.source,
            "download_timestamp": self.download_timestamp,
            "flags": self.flags
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlanetRecord":
        """Create a PlanetRecord from a dictionary."""
        # Handle missing optional fields gracefully
        required_fields = ["kic_id", "period", "radius", "stellar_teff"]
        for field_name in required_fields:
            if field_name not in data:
                raise ValueError(f"Missing required field: {field_name}")
        
        # Convert numeric fields safely
        try:
            data["period"] = float(data["period"])
            data["radius"] = float(data["radius"])
            data["stellar_teff"] = float(data["stellar_teff"])
            
            # Handle optional numeric fields
            if "period_uncertainty" in data and data["period_uncertainty"] is not None:
                data["period_uncertainty"] = float(data["period_uncertainty"])
            else:
                data["period_uncertainty"] = 0.0
                
            if "radius_uncertainty" in data and data["radius_uncertainty"] is not None:
                data["radius_uncertainty"] = float(data["radius_uncertainty"])
            else:
                data["radius_uncertainty"] = 0.0
                
            if "stellar_teff_uncertainty" in data and data["stellar_teff_uncertainty"] is not None:
                data["stellar_teff_uncertainty"] = float(data["stellar_teff_uncertainty"])
            else:
                data["stellar_teff_uncertainty"] = 0.0
                
        except (ValueError, TypeError) as e:
            raise ValueError(f"Error converting numeric fields: {e}")
        
        return cls(**data)
