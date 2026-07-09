"""
Pydantic models for the Mindfulness ASD Social Skills Meta-Analysis.

Defines the core data structures for Study, EffectSize, and MetaAnalysisResult
to ensure type safety and validation throughout the pipeline.
"""

from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict


class DeliveryFormat(str, Enum):
    """Delivery format of the intervention."""
    INDIVIDUAL = "individual"
    GROUP = "group"
    HYBRID = "hybrid"
    ONLINE = "online"


class MindfulnessComponent(str, Enum):
    """Specific mindfulness components extracted from the study."""
    BREATHING = "breathing"
    BODY_AWARENESS = "body_awareness"
    MINDFUL_MOVEMENT = "mindful_movement"
    LOVING_KINDNESS = "loving_kindness"
    OPEN_MONITORING = "open_monitoring"
    FOCUSED_ATTENTION = "focused_attention"


class SocialSkillDomain(str, Enum):
    """Domains of social skills measured."""
    COMMUNICATION = "communication"
    INTERACTION = "interaction"
    EMOTION_RECOGNITION = "emotion_recognition"
    PEER_RELATIONS = "peer_relations"
    BEHAVIOR_REGULATION = "behavior_regulation"


class Study(BaseModel):
    """
    Represents a single clinical study included in the meta-analysis.
    Captures metadata, participant demographics, and intervention details.
    """
    model_config = ConfigDict(frozen=False, populate_by_name=True)

    study_id: str = Field(..., description="Unique identifier for the study (e.g., NCT number or OSF ID)")
    title: str = Field(..., description="Full title of the study")
    authors: List[str] = Field(..., description="List of author names")
    publication_year: int = Field(..., ge=1900, le=2100, description="Year of publication")
    source: str = Field(..., description="Source registry: 'ClinicalTrials.gov' or 'OSF'")
    source_url: str = Field(..., description="Direct URL to the study record")
    publication_date: Optional[date] = Field(None, description="Exact publication date if available")

    # Inclusion Criteria Validation
    age_min: int = Field(..., ge=6, le=12, description="Minimum age of participants")
    age_max: int = Field(..., ge=6, le=12, description="Maximum age of participants")
    asd_diagnosis_required: bool = Field(True, description="Whether ASD diagnosis was required for inclusion")
    diagnosis_tool: Optional[str] = Field(None, description="Tool used for ASD diagnosis (e.g., ADOS-2)")

    # Intervention Details
    intervention_name: str = Field(..., description="Name of the mindfulness intervention")
    delivery_format: DeliveryFormat = Field(..., description="Format of delivery")
    mindfulness_components: List[MindfulnessComponent] = Field(..., description="Components included")
    duration_weeks: float = Field(..., gt=0, description="Duration of intervention in weeks")
    session_count: int = Field(..., gt=0, description="Total number of sessions")
    session_duration_minutes: Optional[int] = Field(None, description="Duration per session in minutes")

    # Control Condition
    control_type: str = Field(..., description="Type of control condition (e.g., Waitlist, Treatment as Usual)")

    # Outcomes
    primary_outcome_domain: SocialSkillDomain = Field(..., description="Primary social skill domain measured")
    outcome_measure_name: str = Field(..., description="Name of the specific outcome measure used")

    # Metadata
    included_in_meta_analysis: bool = Field(True, description="Whether this study passed inclusion criteria")
    exclusion_reason: Optional[str] = Field(None, description="Reason for exclusion if not included")

    @field_validator('mindfulness_components')
    @classmethod
    def validate_components(cls, v):
        if not v:
            raise ValueError("At least one mindfulness component must be specified")
        return v


class EffectSize(BaseModel):
    """
    Represents a calculated effect size (Hedges' g) for a specific arm comparison.
    """
    study_id: str = Field(..., description="Reference to the parent Study")
    arm_treatment: str = Field(..., description="Name/ID of the treatment arm")
    arm_control: str = Field(..., description="Name/ID of the control arm")

    # Raw Data
    n_treatment: int = Field(..., gt=0, description="Sample size of treatment arm")
    n_control: int = Field(..., gt=0, description="Sample size of control arm")
    mean_treatment: float = Field(..., description="Mean outcome for treatment arm")
    mean_control: float = Field(..., description="Mean outcome for control arm")
    sd_treatment: float = Field(..., gt=0, description="Standard deviation for treatment arm")
    sd_control: float = Field(..., gt=0, description="Standard deviation for control arm")

    # Calculated Metrics
    hedges_g: float = Field(..., description="Hedges' g effect size (with small-sample correction)")
    se_hedges_g: float = Field(..., description="Standard error of Hedges' g")
    ci_lower: float = Field(..., description="Lower bound of 95% CI")
    ci_upper: float = Field(..., description="Upper bound of 95% CI")

    # Context
    follow_up_months: Optional[float] = Field(None, description="Follow-up duration in months if applicable")
    outcome_domain: SocialSkillDomain = Field(..., description="Domain this effect size pertains to")

    @field_validator('hedges_g', 'se_hedges_g', 'ci_lower', 'ci_upper')
    @classmethod
    def validate_finite(cls, v):
        if not isinstance(v, float) or (v != v):  # NaN check
            raise ValueError("Effect size metrics must be finite numbers")
        return v


class MetaAnalysisResult(BaseModel):
    """
    Aggregated results from the meta-analysis for a specific subgroup or overall pool.
    """
    analysis_type: str = Field(..., description="Type of analysis (e.g., 'Overall', 'Group Delivery', 'Breathing Component')")
    subgroup_label: Optional[str] = Field(None, description="Specific label if this is a subgroup")

    # Pooled Effect
    pooled_hedges_g: float = Field(..., description="Pooled Hedges' g")
    pooled_se: float = Field(..., description="Pooled standard error")
    pooled_ci_lower: float = Field(..., description="Pooled 95% CI lower")
    pooled_ci_upper: float = Field(..., description="Pooled 95% CI upper")
    p_value: float = Field(..., description="P-value for the pooled effect")

    # Heterogeneity
    n_studies: int = Field(..., ge=1, description="Number of studies included")
    i_squared: float = Field(..., description="I-squared heterogeneity statistic (0-100)")
    tau_squared: float = Field(..., description="Tau-squared (between-study variance)")
    q_statistic: float = Field(..., description="Cochran's Q statistic")
    q_p_value: float = Field(..., description="P-value for heterogeneity")

    # Model Selection
    model_used: str = Field(..., description="'Random-Effects' or 'Fixed-Effect'")
    reason_for_model: str = Field(..., description="Justification for model selection based on I²")

    # Publication Bias (if applicable)
    eggers_test_p: Optional[float] = Field(None, description="P-value from Egger's test")
    publication_bias_assessment: Optional[str] = Field(None, description="Qualitative assessment of bias")

    # Metadata
    analysis_date: date = Field(default_factory=date.today, description="Date analysis was run")