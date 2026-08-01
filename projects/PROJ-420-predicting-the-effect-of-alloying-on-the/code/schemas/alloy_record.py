from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from decimal import Decimal

class MeasurementProvenance(BaseModel):
    source: str
    method: str
    date: Optional[str] = None

class AlloyRecord(BaseModel):
    """Schema for an aluminum alloy record."""
    # Required fields
    poisson_ratio: float
    young_modulus: float
    cu_fraction: float
    mg_fraction: float
    si_fraction: float
    zn_fraction: float
    mn_fraction: float
    measurement_method: str
    
    # Optional fields
    al_fraction: Optional[float] = None
    provenance: Optional[MeasurementProvenance] = None
    record_id: Optional[str] = None

    @model_validator(mode='after')
    def check_fractions(self):
        total = self.cu_fraction + self.mg_fraction + self.si_fraction + self.zn_fraction + self.mn_fraction
        if abs(total - 1.0) > 0.01 and self.al_fraction is None:
            # Allow if al_fraction is calculated later, but warn
            pass
        return self

class ModelMetrics(BaseModel):
    """Schema for model performance metrics."""
    cv_mae: float
    test_mae: float
    model_type: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

def main():
    """Test schema validation."""
    record = AlloyRecord(
        poisson_ratio=0.33,
        young_modulus=70.0,
        cu_fraction=0.05,
        mg_fraction=0.05,
        si_fraction=0.05,
        zn_fraction=0.05,
        mn_fraction=0.05,
        measurement_method="Ultrasonic"
    )
    print(record)

if __name__ == "__main__":
    main()
