from datetime import date
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
import math

class DeliveryFormat(Enum):
    """Delivery formats for mindfulness interventions."""
    IN_PERSON_GROUP = "in_person_group"
    IN_PERSON_INDIVIDUAL = "in_person_individual"
    ONLINE_GROUP = "online_group"
    ONLINE_INDIVIDUAL = "online_individual"
    HYBRID = "hybrid"

class MindfulnessComponent(Enum):
    """Core mindfulness intervention components."""
    BREATHING = "breathing"
    BODY_AWARENESS = "body_awareness"
    MEDITATION = "meditation"
    YOGA = "yoga"
    ACCEPTANCE = "acceptance"
    PRESENCE = "presence"
    OTHER = "other"

class SocialSkillDomain(Enum):
    """Domains of social skills measured."""
    COMMUNICATION = "communication"
    INTERACTION = "interaction"
    EMOTION_RECOGNITION = "emotion_recognition"
    THEORY_OF_MIND = "theory_of_mind"
    PERSPECTIVE_TAKING = "perspective_taking"
    CONFLICT_RESOLUTION = "conflict_resolution"
    OTHER = "other"

class Study(BaseModel):
    """
    Represents a single study record from the meta-analysis.
    Contains metadata, intervention details, and outcome data.
    """
    model_config = ConfigDict(use_enum_values=True, str_strip_whitespace=True)

    study_id: str = Field(..., description="Unique identifier for the study")
    source: str = Field(..., description="Source registry (ClinicalTrials.gov or OSF)")
    registry_id: str = Field(..., description="Original registry identifier")
    title: str = Field(..., description="Study title")
    publication_year: int = Field(..., ge=1900, le=2099, description="Year of publication")
    first_author: str = Field(..., description="First author's last name")

    # Population
    age_min: float = Field(..., ge=0, description="Minimum age of participants")
    age_max: float = Field(..., ge=0, description="Maximum age of participants")
    sample_size: int = Field(..., gt=0, description="Total sample size")
    asd_diagnosis_required: bool = Field(..., description="Whether ASD diagnosis was required")

    # Intervention
    intervention_name: str = Field(..., description="Name of the mindfulness intervention")
    delivery_format: List[DeliveryFormat] = Field(default_factory=list, description="Delivery formats used")
    mindfulness_components: List[MindfulnessComponent] = Field(default_factory=list, description="Mindfulness components included")
    session_duration_minutes: Optional[int] = Field(None, ge=1, description="Duration of each session in minutes")
    total_sessions: Optional[int] = Field(None, ge=1, description="Total number of sessions")
    follow_up_months: Optional[int] = Field(None, ge=0, description="Follow-up duration in months")

    # Outcomes
    primary_outcome_domain: List[SocialSkillDomain] = Field(default_factory=list, description="Primary social skill domains measured")
    outcome_measure_name: str = Field(..., description="Name of the primary outcome measure")

    # Effect size data (intervention vs control)
    # Intervention group
    n_intervention: int = Field(..., gt=0, description="Sample size of intervention group")
    mean_intervention: float = Field(..., description="Mean outcome for intervention group")
    sd_intervention: float = Field(..., gt=0, description="Standard deviation for intervention group")

    # Control group
    n_control: int = Field(..., gt=0, description="Sample size of control group")
    mean_control: float = Field(..., description="Mean outcome for control group")
    sd_control: float = Field(..., gt=0, description="Standard deviation for control group")

    # Metadata
    inclusion_criteria_met: bool = Field(..., description="Whether study met all inclusion criteria")
    exclusion_reason: Optional[str] = Field(None, description="Reason for exclusion if not included")
    extracted_at: Optional[date] = Field(None, description="Date of data extraction")

    @field_validator('sd_intervention', 'sd_control')
    @classmethod
    def check_positive_sd(cls, v):
        if v <= 0:
            raise ValueError('Standard deviation must be positive')
        return v

    @field_validator('mean_intervention', 'mean_control', 'sd_intervention', 'sd_control')
    @classmethod
    def check_not_nan(cls, v):
        if math.isnan(v):
            raise ValueError('Value cannot be NaN')
        return v

class EffectSize(BaseModel):
    """
    Represents a calculated effect size (Hedges' g) for a study.
    Includes the effect size, standard error, and confidence intervals.
    """
    model_config = ConfigDict(use_enum_values=True)

    study_id: str = Field(..., description="Reference to the Study")
    effect_size: float = Field(..., description="Hedges' g effect size")
    standard_error: float = Field(..., gt=0, description="Standard error of the effect size")
    variance: float = Field(..., gt=0, description="Variance of the effect size")
    ci_lower_95: float = Field(..., description="Lower bound of 95% confidence interval")
    ci_upper_95: float = Field(..., description="Upper bound of 95% confidence interval")
    sample_size: int = Field(..., gt=0, description="Total sample size for this comparison")
    small_sample_correction_applied: bool = Field(default=True, description="Whether small-sample correction was applied")

class MetaAnalysisResult(BaseModel):
    """
    Represents the results of a meta-analysis.
    Includes pooled effect size, heterogeneity statistics, and subgroup analyses.
    """
    model_config = ConfigDict(use_enum_values=True)

    analysis_id: str = Field(..., description="Unique identifier for this analysis")
    model_type: str = Field(..., description="Type of meta-analysis model (e.g., 'random_effects', 'fixed_effects')")
    
    # Pooled results
    pooled_effect_size: float = Field(..., description="Pooled effect size (Hedges' g)")
    pooled_se: float = Field(..., gt=0, description="Standard error of pooled effect")
    pooled_ci_lower_95: float = Field(..., description="Lower bound of 95% CI for pooled effect")
    pooled_ci_upper_95: float = Field(..., description="Upper bound of 95% CI for pooled effect")
    z_statistic: float = Field(..., description="Z-statistic for pooled effect")
    p_value: float = Field(..., ge=0, le=1, description="P-value for pooled effect")

    # Heterogeneity
    i_squared: Optional[float] = Field(None, ge=0, le=100, description="I² statistic (percentage)")
    tau_squared: Optional[float] = Field(None, ge=0, description="Tau² (between-study variance)")
    q_statistic: Optional[float] = Field(None, description="Cochran's Q statistic")
    q_p_value: Optional[float] = Field(None, ge=0, le=1, description="P-value for Q statistic")
    k_studies: int = Field(..., gt=0, description="Number of studies included")

    # Subgroup analyses (optional)
    subgroup_results: Optional[List[Dict[str, Any]]] = Field(
        None, 
        description="Results for subgroup analyses (e.g., by delivery format or component)"
    )
    
    # Publication bias (optional)
    eggers_test_p_value: Optional[float] = Field(None, ge=0, le=1, description="P-value from Egger's test")
    funnel_plot_generated: bool = Field(default=False, description="Whether funnel plot was generated")

    # Metadata
    analysis_date: Optional[date] = Field(None, description="Date of analysis")
    notes: Optional[str] = Field(None, description="Additional notes about the analysis")