"""
Pydantic data models for Alloy Entry representation.

Defines the core schema for storing alloy compositions,
target properties (Bulk/Shear moduli), and derived feature vectors.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
import math


class ElementDescriptor(BaseModel):
    """
    Descriptive features for a single element within an alloy composition.
    """
    element_symbol: str = Field(..., description="Chemical symbol (e.g., 'Fe', 'Ni')")
    atomic_fraction: float = Field(..., ge=0.0, le=1.0, description="Molar fraction of the element")
    atomic_radius: Optional[float] = Field(None, description="Atomic radius in Angstroms")
    electronegativity: Optional[float] = Field(None, description="Pauling electronegativity")
    valence_electrons: Optional[float] = Field(None, description="Number of valence electrons")
    melting_point: Optional[float] = Field(None, description="Melting point in Kelvin")

    @field_validator('atomic_fraction')
    @classmethod
    def validate_fraction(cls, v: float) -> float:
        if math.isnan(v) or math.isinf(v):
            raise ValueError("Fraction cannot be NaN or Infinity")
        return v


class AlloyEntry(BaseModel):
    """
    Core data model for an alloy entry.

    Represents a single sample with:
    - Unique identifier
    - Composition (list of ElementDescriptors)
    - Target properties (Bulk/Shear moduli) if available
    - Metadata (source, timestamp)
    """
    entry_id: str = Field(..., description="Unique identifier for the alloy entry")
    composition: List[ElementDescriptor] = Field(..., description="List of elemental descriptors")
    
    # Target Properties (DFT Proxies)
    bulk_modulus: Optional[float] = Field(None, ge=0.0, description="Bulk modulus in GPa")
    shear_modulus: Optional[float] = Field(None, ge=0.0, description="Shear modulus in GPa")
    
    # Metadata
    source_dataset: Optional[str] = Field(None, description="Name of the source dataset (e.g., 'OQMD')")
    source_id: Optional[str] = Field(None, description="Original ID in source dataset")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_validated: bool = Field(default=False, description="Flag indicating if data passed validation checks")

    # Feature vector (optional, populated after encoding)
    feature_vector: Optional[List[float]] = Field(None, description="Encoded feature vector for ML models")

    @model_validator(mode='after')
    def check_composition_sum(self) -> "AlloyEntry":
        """Ensure atomic fractions sum to ~1.0."""
        if not self.composition:
            raise ValueError("Composition list cannot be empty")
        
        total = sum(e.atomic_fraction for e in self.composition)
        if not math.isclose(total, 1.0, rel_tol=1e-4):
            raise ValueError(f"Atomic fractions must sum to 1.0, got {total:.6f}")
        
        return self

    @field_validator('bulk_modulus', 'shear_modulus')
    @classmethod
    def validate_moduli(cls, v: Optional[float]) -> Optional[float]:
        """Ensure moduli are non-negative if present."""
        if v is not None:
            if v < 0:
                raise ValueError("Moduli cannot be negative")
            if math.isnan(v) or math.isinf(v):
                raise ValueError("Moduli cannot be NaN or Infinity")
        return v

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary representation."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlloyEntry":
        """Create model from dictionary."""
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        return cls(**data)
