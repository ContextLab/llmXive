import math
from datetime import datetime
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict


class IonSolventPair(BaseModel):
    """
    Represents an experimental measurement of solvation free energy for a specific
    ion-solvent pair.

    Fields:
        ion_identifier: Standard chemical identifier (e.g., "Na+", "Cl-").
        solvent_identifier: Standard chemical identifier (e.g., "H2O", "Ethanol").
        experimental_deltaG: Experimental solvation free energy in kcal/mol.
        uncertainty: Estimated uncertainty of the experimental value in kcal/mol.
        temperature: Measurement temperature in Kelvin.
        charge: Integer charge of the ion.
        radius: Ionic radius in Angstroms.
        radius_type: Type of radius used (e.g., "crystal", "hydrated", "van_der_waals").
        instrument_metadata: Optional dictionary containing instrument details,
                             source citations, and method descriptions.
    """
    model_config = ConfigDict(extra="forbid")

    ion_identifier: str = Field(..., description="Standard chemical identifier for the ion")
    solvent_identifier: str = Field(..., description="Standard chemical identifier for the solvent")
    experimental_deltaG: float = Field(..., description="Experimental solvation free energy in kcal/mol")
    uncertainty: float = Field(..., description="Estimated uncertainty in kcal/mol")
    temperature: float = Field(..., description="Measurement temperature in Kelvin")
    charge: int = Field(..., description="Integer charge of the ion")
    radius: float = Field(..., description="Ionic radius in Angstroms")
    radius_type: str = Field(..., description="Type of radius used (crystal, hydrated, etc.)")
    instrument_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Instrument and source metadata")

    @field_validator('experimental_deltaG', 'uncertainty', 'temperature', 'radius')
    @classmethod
    def check_positive(cls, v, info):
        if v <= 0 and info.field_name != 'experimental_deltaG':
            # experimental_deltaG can be negative (exothermic), but others must be positive
            raise ValueError(f"{info.field_name} must be positive")
        return v

    @field_validator('charge')
    @classmethod
    def check_non_zero_charge(cls, v):
        if v == 0:
            raise ValueError("Charge cannot be zero for an ion")
        return v


class BornPrediction(BaseModel):
    """
    Represents a theoretical solvation free energy prediction calculated using
    the Born model.

    Fields:
        ion_identifier: Standard chemical identifier (e.g., "Na+", "Cl-").
        solvent_identifier: Standard chemical identifier (e.g., "H2O", "Ethanol").
        predicted_deltaG: Predicted solvation free energy in kcal/mol.
        ionic_radius: Ionic radius used in calculation in Angstroms.
        dielectric_constant: Dielectric constant of the solvent used.
        calculation_timestamp: Timestamp when the calculation was performed.
    """
    model_config = ConfigDict(extra="forbid")

    ion_identifier: str = Field(..., description="Standard chemical identifier for the ion")
    solvent_identifier: str = Field(..., description="Standard chemical identifier for the solvent")
    predicted_deltaG: float = Field(..., description="Predicted solvation free energy in kcal/mol")
    ionic_radius: float = Field(..., description="Ionic radius used in calculation in Angstroms")
    dielectric_constant: float = Field(..., description="Dielectric constant of the solvent")
    calculation_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of calculation")

    @field_validator('ionic_radius', 'dielectric_constant')
    @classmethod
    def check_positive(cls, v, info):
        if v <= 0:
            raise ValueError(f"{info.field_name} must be positive")
        return v


class ResidualAnalysis(BaseModel):
    """
    Represents the statistical analysis of the difference between experimental
    and Born model predictions.

    Fields:
        residual: The difference (experimental - predicted) in kcal/mol.
        ion_size_class: Categorical size class of the ion (e.g., "small", "medium", "large").
        solvent_class: Categorical class of the solvent (e.g., "water", "alcohol", "aprotic").
        statistical_significance: Boolean indicating if the residual is statistically significant.
        p_value: P-value from the statistical test.
        confidence_interval: Tuple of (lower, upper) bounds for the confidence interval.
    """
    model_config = ConfigDict(extra="forbid")

    residual: float = Field(..., description="Difference between experimental and predicted values")
    ion_size_class: str = Field(..., description="Categorical size class of the ion")
    solvent_class: str = Field(..., description="Categorical class of the solvent")
    statistical_significance: bool = Field(..., description="Whether the residual is statistically significant")
    p_value: float = Field(..., description="P-value from the statistical test")
    confidence_interval: List[float] = Field(..., description="Confidence interval bounds [lower, upper]")

    @field_validator('p_value')
    @classmethod
    def check_p_value_range(cls, v):
        if not (0.0 <= v <= 1.0):
            raise ValueError("p_value must be between 0 and 1")
        return v

    @field_validator('confidence_interval')
    @classmethod
    def check_ci_order(cls, v):
        if len(v) != 2:
            raise ValueError("confidence_interval must have exactly 2 elements")
        if v[0] > v[1]:
            raise ValueError("confidence_interval lower bound must be less than upper bound")
        return v