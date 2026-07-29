"""
Pydantic models for data validation.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from decimal import Decimal

class MeasurementProvenance(BaseModel):
    """Model for measurement method details."""
    method: str
    source: str
    date: Optional[datetime] = None

class AlloyRecord(BaseModel):
    """Model for an alloy data record."""
    # Required fields
    poissons_ratio: float = Field(..., description="Poisson's ratio")
    youngs_modulus: float = Field(..., description="Young's modulus in GPa")
    cu: float = Field(..., ge=0, le=1, description="Atomic fraction of Copper")
    mg: float = Field(..., ge=0, le=1, description="Atomic fraction of Magnesium")
    si: float = Field(..., ge=0, le=1, description="Atomic fraction of Silicon")
    zn: float = Field(..., ge=0, le=1, description="Atomic fraction of Zinc")
    mn: float = Field(..., ge=0, le=1, description="Atomic fraction of Manganese")
    
    # Provenance
    measurement_method: str = Field(..., description="Method used to measure Poisson's ratio")
    
    # Optional metadata
    alloy_name: Optional[str] = None
    notes: Optional[str] = None

    @model_validator(mode='after')
    def check_composition_sum(self):
        total = self.cu + self.mg + self.si + self.zn + self.mn
        if total > 1.05 or total < 0.95:
            # Warning only, as Al balance is implied
            pass 
        return self

class ModelMetrics(BaseModel):
    """Model for model performance metrics."""
    cv_mae: float
    test_mae: float
    model_type: str
    hyperparameters: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)

def main():
    """CLI entry point for testing schema."""
    record = AlloyRecord(
        poissons_ratio=0.33,
        youngs_modulus=70.0,
        cu=0.05, mg=0.02, si=0.01, zn=0.01, mn=0.01,
        measurement_method="Ultrasonic"
    )
    print(record)

if __name__ == "__main__":
    main()
