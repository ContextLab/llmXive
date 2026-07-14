"""
Base data model classes for the corrosion potential prediction pipeline.

Defines structured records for Alloy composition, Environmental conditions,
and Corrosion measurements. These classes enforce strict typing and
basic validation to ensure data integrity before processing.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
import json

@dataclass
class AlloyRecord:
    """
    Represents a specific alloy composition.
    
    Attributes:
        alloy_id: Unique identifier for the alloy (e.g., from NIST database).
        designation: Commercial or standard designation (e.g., "304L", "Inconel 625").
        composition: Dictionary mapping element symbol to weight fraction (0.0-1.0).
        source: Reference to the source of the composition data.
        created_at: Timestamp of record creation.
    """
    alloy_id: str
    designation: str
    composition: Dict[str, float]
    source: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate composition data after initialization."""
        if not self.alloy_id:
            raise ValueError("alloy_id cannot be empty")
        if not self.designation:
            raise ValueError("designation cannot be empty")
        if not self.composition:
            raise ValueError("composition dictionary cannot be empty")
        
        # Validate weight fractions are within [0, 1]
        for element, fraction in self.composition.items():
            if not isinstance(fraction, (int, float)):
                raise TypeError(f"Composition fraction for {element} must be numeric")
            if fraction < 0.0 or fraction > 1.0:
                raise ValueError(f"Composition fraction for {element} must be between 0.0 and 1.0")
        
        # Ensure total composition is reasonable (allow small floating point errors)
        total = sum(self.composition.values())
        if total < 0.99 or total > 1.01:
            # Log warning or raise error depending on strictness requirements
            # For now, we allow it but note it
            pass

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary for serialization."""
        return {
            "alloy_id": self.alloy_id,
            "designation": self.designation,
            "composition": self.composition,
            "source": self.source,
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlloyRecord":
        """Create an AlloyRecord from a dictionary."""
        # Handle datetime parsing if needed
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


@dataclass
class EnvironmentRecord:
    """
    Represents the environmental conditions of a corrosion test.
    
    Attributes:
        env_id: Unique identifier for the environment condition.
        ph: pH value of the solution.
        temperature_c: Temperature in Celsius.
        solution_composition: Dictionary of solution components (e.g., {"Cl-": 0.5, "SO4--": 0.1}).
        aeration: Description of aeration state (e.g., "aerated", "deaerated").
        source: Reference to the source of the environmental data.
        created_at: Timestamp of record creation.
    """
    env_id: str
    ph: Optional[float] = None
    temperature_c: Optional[float] = None
    solution_composition: Dict[str, float] = field(default_factory=dict)
    aeration: Optional[str] = None
    source: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate environment data after initialization."""
        if not self.env_id:
            raise ValueError("env_id cannot be empty")
        
        # Validate pH if present
        if self.ph is not None:
            if not isinstance(self.ph, (int, float)):
                raise TypeError("pH must be numeric")
            # pH is typically 0-14, but extreme conditions exist. We allow >14 or <0 with a note.
            if self.ph < 0.0 or self.ph > 14.0:
                # Log warning or raise error depending on strictness
                pass

        # Validate temperature if present
        if self.temperature_c is not None:
            if not isinstance(self.temperature_c, (int, float)):
                raise TypeError("temperature must be numeric")
            if self.temperature_c < -273.15:
                raise ValueError("Temperature cannot be below absolute zero")

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary for serialization."""
        return {
            "env_id": self.env_id,
            "ph": self.ph,
            "temperature_c": self.temperature_c,
            "solution_composition": self.solution_composition,
            "aeration": self.aeration,
            "source": self.source,
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EnvironmentRecord":
        """Create an EnvironmentRecord from a dictionary."""
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


@dataclass
class CorrosionMeasurement:
    """
    Represents a single corrosion measurement result.
    
    This class links an AlloyRecord and an EnvironmentRecord to a specific
    measurement result (e.g., corrosion potential, corrosion rate).
    
    Attributes:
        measurement_id: Unique identifier for the measurement.
        alloy_id: Reference to the alloy used.
        env_id: Reference to the environment condition.
        corrosion_potential_mv: Measured corrosion potential in millivolts (vs. reference).
        corrosion_rate_mpy: Corrosion rate in mils per year (optional).
        corrosion_rate_mm_y: Corrosion rate in mm/year (optional).
        method: Measurement method used (e.g., "potentiodynamic polarization", "EIS").
        reference_electrode: Reference electrode used (e.g., "SCE", "Ag/AgCl").
        source: Reference to the source of the measurement data.
        created_at: Timestamp of record creation.
    """
    measurement_id: str
    alloy_id: str
    env_id: str
    corrosion_potential_mv: Optional[float] = None
    corrosion_rate_mpy: Optional[float] = None
    corrosion_rate_mm_y: Optional[float] = None
    method: Optional[str] = None
    reference_electrode: Optional[str] = None
    source: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate measurement data after initialization."""
        if not self.measurement_id:
            raise ValueError("measurement_id cannot be empty")
        if not self.alloy_id:
            raise ValueError("alloy_id reference cannot be empty")
        if not self.env_id:
            raise ValueError("env_id reference cannot be empty")

        # Validate potential if present
        if self.corrosion_potential_mv is not None:
            if not isinstance(self.corrosion_potential_mv, (int, float)):
                raise TypeError("corrosion_potential_mv must be numeric")

        # Validate rates if present
        if self.corrosion_rate_mpy is not None and self.corrosion_rate_mpy < 0:
            raise ValueError("corrosion_rate_mpy cannot be negative")
        if self.corrosion_rate_mm_y is not None and self.corrosion_rate_mm_y < 0:
            raise ValueError("corrosion_rate_mm_y cannot be negative")

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary for serialization."""
        return {
            "measurement_id": self.measurement_id,
            "alloy_id": self.alloy_id,
            "env_id": self.env_id,
            "corrosion_potential_mv": self.corrosion_potential_mv,
            "corrosion_rate_mpy": self.corrosion_rate_mpy,
            "corrosion_rate_mm_y": self.corrosion_rate_mm_y,
            "method": self.method,
            "reference_electrode": self.reference_electrode,
            "source": self.source,
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CorrosionMeasurement":
        """Create a CorrosionMeasurement from a dictionary."""
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)

    def to_json(self) -> str:
        """Serialize the record to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "CorrosionMeasurement":
        """Deserialize a JSON string to a CorrosionMeasurement."""
        data = json.loads(json_str)
        return cls.from_dict(data)
