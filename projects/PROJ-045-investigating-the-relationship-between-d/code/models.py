"""
Pydantic models for the Defect Chemistry and Ionic Conductivity project.

These models define the data structures for electrolyte compositions,
defect configurations, migration barriers, and analysis results.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing_extensions import Annotated


class DefectType(str, Enum):
    """Enumeration of supported defect types."""
    VACANCY = "vacancy"
    INTERSTITIAL = "interstitial"
    ANTISITE = "antisite"


class ElectrolyteComposition(BaseModel):
    """
    Represents the chemical composition of an electrolyte material.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    composition_id: str = Field(..., description="Unique identifier for the composition")
    formula: str = Field(..., description="Chemical formula (e.g., 'Li7La3Zr2O12')")
    elements: Dict[str, float] = Field(
        ..., description="Elemental stoichiometry (element -> count)"
    )
    crystal_system: Optional[str] = Field(None, description="Crystal system (e.g., 'cubic', 'tetragonal')")
    space_group: Optional[str] = Field(None, description="Space group symbol or number")
    lattice_parameters: Optional[Dict[str, float]] = Field(
        None, description="Lattice parameters (a, b, c, alpha, beta, gamma)"
    )
    mp_id: Optional[str] = Field(None, description="Materials Project ID")
    source: str = Field("unknown", description="Data source (e.g., 'Materials Project', 'OBELiX')")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("elements")
    @classmethod
    def validate_elements_positive(cls, v: Dict[str, float]) -> Dict[str, float]:
        if any(val <= 0 for val in v.values()):
            raise ValueError("Element counts must be positive.")
        return v


class DefectConfiguration(BaseModel):
    """
    Represents a specific defect configuration within an electrolyte.
    Includes quantification of defect density as per Marie Curie review requirements.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    config_id: str = Field(..., description="Unique identifier for the configuration")
    composition_id: str = Field(..., description="Reference to ElectrolyteComposition")
    defect_type: DefectType = Field(..., description="Type of defect")
    site_index: int = Field(..., description="Index of the affected site in the structure")
    species_in: str = Field(..., description="Species removed (for vacancy) or added (for interstitial)")
    species_out: Optional[str] = Field(None, description="Species replacing the original (for antisite)")
    supercell_multiplier: Optional[Dict[str, int]] = Field(
        None, description="Supercell expansion (e.g., {'x': 2, 'y': 2, 'z': 2})"
    )
    supercell_volume: Optional[float] = Field(
        None, description="Volume of the supercell in Å³"
    )
    defect_density: Optional[float] = Field(
        None, description="Defect concentration (defects/volume) in defects/Å³"
    )
    formation_energy_eV: Optional[float] = Field(None, description="Defect formation energy in eV")
    method: Optional[str] = Field(None, description="Calculation method (e.g., 'DFT', 'Semi-empirical')")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("defect_density")
    @classmethod
    def validate_density_positive(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError("Defect density must be positive.")
        return v

    @field_validator("formation_energy_eV")
    @classmethod
    def validate_energy_reasonable(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < -10.0:
            # Unusually low formation energy, likely an error
            raise ValueError("Formation energy seems unphysically low (< -10 eV).")
        return v


class MigrationBarrier(BaseModel):
    """
    Represents the migration barrier for a specific ion hopping mechanism.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    barrier_id: str = Field(..., description="Unique identifier for the barrier")
    config_id: str = Field(..., description="Reference to DefectConfiguration")
    hop_start_site: int = Field(..., description="Starting site index")
    hop_end_site: int = Field(..., description="Ending site index")
    barrier_height_eV: float = Field(..., description="Migration barrier height in eV")
    method: str = Field(..., description="Method used (e.g., 'NEB', 'Bond Valence')")
    convergence_criteria: Optional[str] = Field(None, description="Convergence criteria used")
    force_convergence_eV_A: Optional[float] = Field(
        None, description="Final force convergence in eV/Å"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("barrier_height_eV")
    @classmethod
    def validate_barrier_positive(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Migration barrier cannot be negative.")
        return v


class AnalysisResult(BaseModel):
    """
    Represents the results of statistical analysis on defect and conductivity data.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    analysis_id: str = Field(..., description="Unique identifier for the analysis run")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    model_type: str = Field(..., description="Type of statistical model (e.g., 'LinearRegression')")
    predictors: List[str] = Field(..., description="List of predictor variables used")
    target_variable: str = Field(..., description="Target variable (e.g., 'conductivity')")
    r_squared: Optional[float] = Field(None, description="R-squared value")
    adjusted_r_squared: Optional[float] = Field(None, description="Adjusted R-squared value")
    p_values: Optional[Dict[str, float]] = Field(None, description="P-values for each predictor")
    coefficients: Optional[Dict[str, float]] = Field(None, description="Regression coefficients")
    standard_errors: Optional[Dict[str, float]] = Field(None, description="Standard errors of coefficients")
    n_samples: int = Field(..., description="Number of samples used in the analysis")
    multiple_comparison_method: Optional[str] = Field(None, description="Method used for correction (e.g., 'Bonferroni')")
    significant_predictors: Optional[List[str]] = Field(None, description="List of statistically significant predictors")
    diagnostics: Optional[Dict[str, Any]] = Field(None, description="Additional diagnostic metrics (e.g., VIF)")
    notes: Optional[str] = Field(None, description="Any notes or observations from the analysis")