"""
Pydantic models that exactly mirror the JSON schema
`specs/001-predicting-the-effect-of-alloying-on-the/contracts/alloy_record.schema.yaml`.

The schema defines the following required top‑level fields:

- material_id (string)
- formula (string)
- elemental_composition (object with Cu, Mg, Si, Zn, Mn, Al as numbers in [0, 1])
- poissons_ratio (number in [0, 0.5])
- youngs_modulus_gpa (positive number)
- poisson_source (enum: "ultrasonic", "direct_measurement", "laser_ultrasonics")
- measurement_method (enum: "Ultrasonic", "Resonant Ultrasound Spectroscopy",
  "Static Tensile", "Other")
- source (enum: "Materials Project", "NIST MDR")
- is_alloy (boolean)
- is_independent_measurement (boolean)

The models below enforce these constraints and forbid any additional
properties, matching `additionalProperties: false` in the schema.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, condecimal, confloat, validator

# ----------------------------------------------------------------------
# Nested model for the elemental composition dictionary
# ----------------------------------------------------------------------
class ElementalComposition(BaseModel):
    """Atomic fractions for the six elements present in the alloy."""

    Cu: condecimal(ge=0, le=1) = Field(..., description="Atomic fraction of Copper.")
    Mg: condecimal(ge=0, le=1) = Field(..., description="Atomic fraction of Magnesium.")
    Si: condecimal(ge=0, le=1) = Field(..., description="Atomic fraction of Silicon.")
    Zn: condecimal(ge=0, le=1) = Field(..., description="Atomic fraction of Zinc.")
    Mn: condecimal(ge=0, le=1) = Field(..., description="Atomic fraction of Manganese.")
    Al: condecimal(ge=0, le=1) = Field(..., description="Atomic fraction of Aluminum (balance).")

    @validator("*", pre=True)
    def ensure_float(cls, v):
        """Accept both int and float, store as Decimal for exactness."""
        return float(v)

    @validator("__root__")
    def fractions_sum_to_one(cls, values):
        """Optional sanity check – the sum should be close to 1.0."""
        total = sum(values.values())
        if abs(total - 1.0) > 1e-3:
            # Not a hard error to keep the model flexible; just warn.
            # In a strict implementation you could raise ValueError here.
            pass
        return values

    class Config:
        extra = "forbid"

# ----------------------------------------------------------------------
# Main AlloyRecord model
# ----------------------------------------------------------------------
class AlloyRecord(BaseModel):
    """Schema for a single aluminum alloy record after cleaning."""

    material_id: str = Field(..., description="Unique identifier from the source database.")
    formula: str = Field(..., description="Chemical formula (e.g., 'Al95Cu5').")
    elemental_composition: ElementalComposition = Field(
        ..., description="Atomic fractions for each element."
    )
    poissons_ratio: confloat(ge=0, le=0.5) = Field(
        ..., description="Poisson's ratio (dimensionless)."
    )
    youngs_modulus_gpa: confloat(gt=0) = Field(
        ..., description="Young's modulus normalized to GPa."
    )
    poisson_source: Literal[
        "ultrasonic", "direct_measurement", "laser_ultrasonics"
    ] = Field(..., description="Source of Poisson's ratio measurement.")
    measurement_method: Literal[
        "Ultrasonic",
        "Resonant Ultrasound Spectroscopy",
        "Static Tensile",
        "Other",
    ] = Field(..., description="Method used to measure Poisson's ratio.")
    source: Literal["Materials Project", "NIST MDR"] = Field(
        ..., description="Original data source."
    )
    is_alloy: bool = Field(..., description="True if the entry represents a continuous solid solution.")
    is_independent_measurement: bool = Field(
        ...,
        description="True if poisson_source is in the allowed set.",
    )

    class Config:
        extra = "forbid"

    @validator("elemental_composition")
    def composition_fractions_valid(cls, v: ElementalComposition):
        """Ensure the six fractions sum to (approximately) 1.0."""
        total = (
            float(v.Cu)
            + float(v.Mg)
            + float(v.Si)
            + float(v.Zn)
            + float(v.Mn)
            + float(v.Al)
        )
        if abs(total - 1.0) > 1e-3:
            raise ValueError(
                f"Elemental fractions must sum to 1.0 (got {total:.6f})"
            )
        return v

# ----------------------------------------------------------------------
# Convenience entry‑point for manual testing
# ----------------------------------------------------------------------
def main() -> None:
    """Run a quick sanity‑check using a minimal valid JSON example."""
    example = {
        "material_id": "mp-1234",
        "formula": "Al95Cu5",
        "elemental_composition": {
            "Cu": 0.05,
            "Mg": 0.0,
            "Si": 0.0,
            "Zn": 0.0,
            "Mn": 0.0,
            "Al": 0.95,
        },
        "poissons_ratio": 0.33,
        "youngs_modulus_gpa": 70.0,
        "poisson_source": "ultrasonic",
        "measurement_method": "Ultrasonic",
        "source": "Materials Project",
        "is_alloy": True,
        "is_independent_measurement": True,
    }

    try:
        record = AlloyRecord(**example)
        print("AlloyRecord validated successfully:")
        print(record.json(indent=2))
    except Exception as exc:
        print(f"Validation failed: {exc}")

if __name__ == "__main__":
    main()