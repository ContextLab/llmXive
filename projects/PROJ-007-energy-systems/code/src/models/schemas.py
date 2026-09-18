from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class Household(BaseModel):
    """Schema for household data."""
    household_id: str
    income: float
    energy_cost: float
    solar_installation: bool
    location: str
    housing_type: str
    census_tract: str

class MatchedPair(BaseModel):
    """Schema for a matched pair in PSM."""
    pair_id: str
    treatment_household_id: str
    control_household_id: str
    propensity_score_treatment: float
    propensity_score_control: float

class GracefulDegradationStatus(BaseModel):
    """
    Schema for the Graceful Degradation Protocol status.
    Captures why the pipeline halted if PSM failed and DiD was impossible.
    """
    halt_reason: str = Field(..., description="Reason for halting the pipeline")
    methodology_attempted: str = Field(..., description="Methodologies that were attempted")
    data_availability_check: str = Field(..., description="Result of data availability checks")

class AnalysisResult(BaseModel):
    """Schema for the final analysis result."""
    status: str = Field(..., description="Pipeline status: 'success' or 'failed'")
    balance_status: str = Field(..., description="PSM balance status: 'passed' or 'failed'")
    graceful_degradation_status: Optional[GracefulDegradationStatus] = Field(
        None, 
        description="Status object if graceful degradation was triggered"
    )
    att_estimate: Optional[float] = Field(None, description="Average Treatment Effect on the Treated")
    p_value: Optional[float] = Field(None, description="P-value for the ATT estimate")
    ci_lower: Optional[float] = Field(None, description="Lower bound of 95% CI")
    ci_upper: Optional[float] = Field(None, description="Upper bound of 95% CI")
    methodology: str = Field(..., description="Methodology used (e.g., 'PSM-OLS')")
    sensitivity_data: Dict[str, Any] = Field(default_factory=dict, description="Sensitivity analysis results")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of analysis")

class Config:
    arbitrary_types_allowed = True
