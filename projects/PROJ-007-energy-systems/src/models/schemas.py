"""
Pydantic schemas for the Energy Systems Inequity Analysis Pipeline.

Defines core data structures for:
- Household: Raw and processed unit-level records.
- MatchedPair: Treatment and control units linked by PSM.
- AnalysisResult: Final causal and descriptive outputs.
"""

from datetime import date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
import math


class Household(BaseModel):
    """
    Represents a single household record after ingestion and preprocessing.

    Attributes:
        household_id: Unique identifier for the household.
        tract_id: Census tract identifier.
        income: Annual household income (USD).
        energy_cost: Annual energy expenditure (USD).
        treatment: Binary indicator (1 if solar/microgrid adopter, 0 otherwise).
        home_value: Current estimated home value (USD).
        housing_type: Categorical description (e.g., 'Single Family', 'Apartment').
        location_lat: Latitude coordinate.
        location_lon: Longitude coordinate.
        energy_cost_burden: Ratio of energy_cost to income.
        home_value_change: Change in home value over the study period (USD).
        is_low_income: Boolean flag indicating if household is in low-income tract.
        adoption_year: Year of solar/microgrid adoption (if applicable).
        missing_flags: Dictionary of boolean flags for missing values in specific fields.
    """
    household_id: str = Field(..., description="Unique identifier")
    tract_id: str = Field(..., description="Census tract ID")
    income: float = Field(..., ge=0, description="Annual income")
    energy_cost: float = Field(..., ge=0, description="Annual energy cost")
    treatment: int = Field(..., ge=0, le=1, description="Treatment status (0/1)")
    home_value: Optional[float] = Field(None, ge=0, description="Home value")
    housing_type: Optional[str] = Field(None, description="Housing type")
    location_lat: Optional[float] = Field(None, description="Latitude")
    location_lon: Optional[float] = Field(None, description="Longitude")
    energy_cost_burden: Optional[float] = Field(None, ge=0, description="Cost burden ratio")
    home_value_change: Optional[float] = Field(None, description="Home value change")
    is_low_income: bool = Field(default=False, description="Low-income tract flag")
    adoption_year: Optional[int] = Field(None, ge=1900, le=2099, description="Adoption year")
    missing_flags: Dict[str, bool] = Field(default_factory=dict, description="Flags for missing data")

    @field_validator('energy_cost_burden')
    @classmethod
    def validate_burden(cls, v, info):
        if v is not None and (v < 0 or v > 10):
            # Allow high burdens but warn if > 100% (1.0)
            if v > 1.0:
                pass # Log warning in real system, here just allow
        return v


class MatchedPair(BaseModel):
    """
    Represents a matched pair of treated and control households.

    Attributes:
        pair_id: Unique identifier for the pair.
        treated_household_id: ID of the treated unit.
        control_household_id: ID of the control unit.
        propensity_score_treated: Propensity score of the treated unit.
        propensity_score_control: Propensity score of the control unit.
        distance: Caliper distance or matching metric.
        covariates: Snapshot of covariate values at time of matching.
    """
    pair_id: str = Field(..., description="Unique pair ID")
    treated_household_id: str = Field(..., description="Treated household ID")
    control_household_id: str = Field(..., description="Control household ID")
    propensity_score_treated: float = Field(..., gt=0, lt=1, description="PS for treated")
    propensity_score_control: float = Field(..., gt=0, lt=1, description="PS for control")
    distance: float = Field(..., ge=0, description="Matching distance")
    covariates: Dict[str, Any] = Field(default_factory=dict, description="Covariate snapshot")

    @model_validator(mode='after')
    def check_ps_difference(self):
        if abs(self.propensity_score_treated - self.propensity_score_control) > 0.2:
            # Warning: Large PS difference might indicate poor match
            pass
        return self


class SensitivityResult(BaseModel):
    """
    Results from a single caliper sweep iteration.
    """
    caliper: float
    n_matched: int
    att_estimate: float
    p_value: float
    ci_lower: float
    ci_upper: float
    balance_status: str  # e.g., 'PASS', 'FAIL', 'WARN'


class AnalysisResult(BaseModel):
    """
    Final output of the causal inference and scaling analysis pipeline.

    Attributes:
        analysis_id: Unique identifier for the analysis run.
        methodology: Description of methods used (e.g., 'PSM-OLS', 'DiD').
        treatment_effect_estimate: The primary ATT or DID estimate.
        p_value: Statistical significance of the effect.
        confidence_interval: Tuple of (lower, upper) bounds.
        n_treated: Number of treated units in final sample.
        n_control: Number of control units in final sample.
        balance_summary: Summary of covariate balance (e.g., max SMD).
        sensitivity_analysis: List of results from caliper sweeps.
        scaling_law_beta: Descriptive scaling exponent (if applicable).
        scaling_law_ci: Confidence interval for scaling exponent.
        notes: Any additional context or warnings.
    """
    analysis_id: str = Field(..., description="Unique analysis ID")
    methodology: str = Field(..., description="Methodology used")
    treatment_effect_estimate: float = Field(..., description="Primary effect estimate")
    p_value: float = Field(..., ge=0, le=1, description="P-value")
    confidence_interval: List[float] = Field(..., min_length=2, max_length=2, description="95% CI")
    n_treated: int = Field(..., ge=1, description="Count of treated")
    n_control: int = Field(..., ge=1, description="Count of control")
    balance_summary: Dict[str, Any] = Field(default_factory=dict, description="Balance metrics")
    sensitivity_analysis: List[SensitivityResult] = Field(default_factory=list, description="Sweep results")
    scaling_law_beta: Optional[float] = Field(None, description="Descriptive scaling beta")
    scaling_law_ci: Optional[List[float]] = Field(None, description="Scaling beta CI")
    notes: Optional[str] = Field(None, description="Notes")

    @field_validator('confidence_interval')
    @classmethod
    def validate_ci_order(cls, v):
        if v[0] > v[1]:
            raise ValueError("Confidence interval lower bound must be less than upper bound")
        return v