"""
Data model classes for the corrosion prediction pipeline.

Uses Pydantic v2 for strict schema enforcement as required by T007.
"""
from typing import Dict, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from utils.exceptions import DataInsufficientError, SchemaMismatchError
from utils.logging import get_logger

logger = get_logger(__name__)


class AlloyRecord(BaseModel):
    """
    Represents an alloy record with its composition and designation.
    
    Fields:
        alloy_id: Unique identifier for the alloy.
        composition: Dictionary mapping element names to weight fractions.
        specific_alloy_designation: Specific name/designation of the alloy (e.g., "304 Stainless Steel").
    """
    model_config = ConfigDict(strict=True, frozen=True)

    alloy_id: str = Field(..., description="Unique identifier for the alloy")
    composition: Dict[str, float] = Field(..., description="Mapping of element name to weight fraction")
    specific_alloy_designation: str = Field(..., description="Specific alloy designation name")

    @field_validator('composition')
    @classmethod
    def validate_composition(cls, v: Dict[str, float]) -> Dict[str, float]:
        if not v:
            raise SchemaMismatchError("Composition dictionary cannot be empty")
        for element, fraction in v.items():
            if not isinstance(element, str) or not element:
                raise SchemaMismatchError(f"Invalid element name in composition: {element}")
            if not isinstance(fraction, (int, float)):
                raise SchemaMismatchError(f"Composition value must be a number, got {type(fraction)} for {element}")
            if fraction < 0.0 or fraction > 1.0:
                # Allow > 1.0 if it represents percentage (0-100) but warn? 
                # Strictly, weight fraction is 0-1. If input is 0-100, preprocessing should handle it.
                # For strict schema, we enforce 0-1.
                raise SchemaMismatchError(f"Weight fraction for {element} must be between 0 and 1, got {fraction}")
        return v

    @field_validator('alloy_id', 'specific_alloy_designation')
    @classmethod
    def validate_non_empty_string(cls, v: str, info) -> str:
        if not v or not v.strip():
            field_name = info.field_name
            raise SchemaMismatchError(f"{field_name} cannot be empty")
        return v.strip()


class EnvironmentRecord(BaseModel):
    """
    Represents the environmental conditions for a corrosion measurement.
    
    Fields:
        ph: pH value of the electrolyte.
        temperature: Temperature in Celsius.
        electrolyte_type: Type of electrolyte (e.g., "NaCl", "H2SO4").
    """
    model_config = ConfigDict(strict=True, frozen=True)

    ph: float = Field(..., description="pH value of the electrolyte")
    temperature: float = Field(..., description="Temperature in Celsius")
    electrolyte_type: str = Field(..., description="Type of electrolyte")

    @field_validator('ph')
    @classmethod
    def validate_ph(cls, v: float) -> float:
        if v < 0.0 or v > 14.0:
            # Strictly, pH can be outside 0-14 in extreme cases, but typically 0-14 in standard tests.
            # If the spec implies standard ranges, we might enforce 0-14. 
            # However, to be safe against real data outliers, we might just warn or allow.
            # Given the task says "strict schema", we allow real values but could add a constraint if spec demands.
            # Let's allow any float but log a warning if out of typical range.
            logger.warning(f"pH value {v} is outside typical 0-14 range.")
        return v

    @field_validator('temperature')
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        if v < -273.15:
            raise SchemaMismatchError(f"Temperature cannot be below absolute zero: {v}")
        return v

    @field_validator('electrolyte_type')
    @classmethod
    def validate_electrolyte_type(cls, v: str) -> str:
        if not v or not v.strip():
            raise SchemaMismatchError("Electrolyte type cannot be empty")
        return v.strip()


class CorrosionMeasurement(BaseModel):
    """
    Represents a corrosion measurement result.
    
    Fields:
        record_id: Unique identifier linking to the alloy/environment record.
        potential_mV: Corrosion potential in millivolts.
    """
    model_config = ConfigDict(strict=True, frozen=True)

    record_id: str = Field(..., description="Unique identifier for the measurement record")
    potential_mV: float = Field(..., description="Corrosion potential in millivolts")

    @field_validator('record_id')
    @classmethod
    def validate_record_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise SchemaMismatchError("Record ID cannot be empty")
        return v.strip()
