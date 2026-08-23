from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
import math

class ElementDescriptor(BaseModel):
    """Descriptor for a single element in a composition."""
    symbol: str
    fraction: float
    atomic_radius: Optional[float] = None
    electronegativity: Optional[float] = None
    
    @field_validator('fraction')
    @classmethod
    def validate_fraction(cls, v):
        if v < 0 or v > 1:
            raise ValueError('Fraction must be between 0 and 1')
        return v

class AlloyEntry(BaseModel):
    """Model for an alloy entry with composition and properties."""
    composition: str
    bulk_modulus: float
    shear_modulus: float
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('bulk_modulus', 'shear_modulus')
    @classmethod
    def validate_moduli(cls, v):
        if v <= 0:
            raise ValueError('Moduli must be positive')
        return v
    
    @model_validator(mode='after')
    def check_composition(self):
        if not self.composition or not isinstance(self.composition, str):
            raise ValueError('Composition must be a non-empty string')
        return self
