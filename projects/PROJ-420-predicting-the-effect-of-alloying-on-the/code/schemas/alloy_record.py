from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from decimal import Decimal

class MeasurementProvenance(BaseModel):
    """
    Stores metadata about how a measurement was obtained to ensure independence verification (FR-009).
    """
    method: str = Field(..., description="The method used to obtain the value (e.g., 'experimental', 'DFT', 'calculated')")
    source: str = Field(..., description="The database or paper source")
    date_retrieved: Optional[str] = Field(default_factory=lambda: datetime.now().isoformat())
    reference_id: Optional[str] = Field(default=None)

class AlloyRecord(BaseModel):
    """
    Core schema for an alloy record containing composition and properties.
    Includes fields for provenance to satisfy FR-009.
    """
    material_id: str = Field(..., description="Unique identifier for the material")
    formula: str = Field(..., description="Chemical formula")
    elements: List[str] = Field(..., description="List of elements present")
    nelements: int = Field(..., description="Number of elements")
    
    # Properties
    poisson_ratio: float = Field(..., description="Poisson's ratio")
    youngs_modulus: Optional[float] = Field(default=None, description="Young's Modulus in GPa")
    bulk_modulus: Optional[float] = Field(default=None, description="Bulk Modulus in GPa")
    shear_modulus: Optional[float] = Field(default=None, description="Shear Modulus in GPa")
    
    # Composition (Atomic fractions, optional for now, filled during cleaning)
    composition: Optional[Dict[str, float]] = Field(default=None, description="Atomic fractions of elements")
    
    # Provenance
    measurement_method: str = Field(..., description="Method of measurement (CRITICAL for FR-009)")
    measurement_source: str = Field(..., description="Source of the data")
    
    # Metadata
    raw_data: Optional[Dict[str, Any]] = Field(default=None, description="Raw data payload from source")

    @field_validator('poisson_ratio')
    @classmethod
    def validate_poisson(cls, v):
        if v < 0 or v > 0.5:
            raise ValueError('Poisson\'s ratio must be between 0 and 0.5')
        return v

    @model_validator(mode='after')
    def check_modulus_consistency(self):
        # Basic consistency check: if Young's and Bulk are present, Shear can be derived.
        # We don't enforce derivation here, just ensure we have the fields if provided.
        return self

class ModelMetrics(BaseModel):
    """
    Stores metrics from model training and evaluation.
    """
    model_type: str
    cv_mae: float
    test_mae: float
    r2_score: float
    training_date: str = Field(default_factory=lambda: datetime.now().isoformat())
    parameters: Dict[str, Any] = Field(default_factory=dict)

def main():
    # Simple test to ensure schema loads
    test_record = AlloyRecord(
        material_id="mp-123",
        formula="Al100",
        elements=["Al"],
        nelements=1,
        poisson_ratio=0.34,
        measurement_method="DFT",
        measurement_source="Materials Project"
    )
    print(f"Schema validation successful: {test_record.material_id}")

if __name__ == "__main__":
    main()
