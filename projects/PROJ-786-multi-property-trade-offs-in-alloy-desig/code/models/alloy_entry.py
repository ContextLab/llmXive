from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, model_validator
from datetime import datetime
import math

class ElementDescriptor(BaseModel):
    symbol: str
    atomic_radius: Optional[float] = None
    electronegativity: Optional[float] = None
    atomic_mass: Optional[float] = None
    valence_electrons: Optional[int] = None

class AlloyEntry(BaseModel):
    composition: str
    bulk_modulus: float
    shear_modulus: float
    system: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @model_validator(mode='after')
    def validate_moduli(cls, values):
        if values.bulk_modulus <= 0:
            raise ValueError("Bulk modulus must be positive")
        if values.shear_modulus <= 0:
            raise ValueError("Shear modulus must be positive")
        return values