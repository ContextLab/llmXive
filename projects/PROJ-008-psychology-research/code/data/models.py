"""
Pydantic data models for the Mindfulness Components and Delivery Formats in ASD Social Skills research pipeline.

These models enforce data integrity and schema validation as required by:
- Constitution Principle II (Verified Accuracy)
- Constitution Principle V (Fail Fast)
- FR-007 (Data Integrity)
"""

from datetime import date
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict
import math


class DeliveryFormat(Enum):
    """
    Enumeration of delivery formats for the intervention.

    Constitution Principle VII mandates strict adherence to these categories.
    FR-010 requires extraction of this field from study metadata.
    """
    CAREGIVER_MEDIANATED = "caregiver-mediated"
    CHILD_LEAD = "child-led"
    MIXED = "mixed"
    NOT_REPORTED = "not-reported"


class MindfulnessComponent(Enum):
    """
    Enumeration of specific mindfulness components extracted from study descriptions.

    FR-003 requires detection of these components via regex scanning of abstract/description.
    Constitution Principle II ensures these labels match the actual intervention content.
    """
    BREATHING = "breathing"
    BODY_SCAN = "body_scan"
    MINDFUL_MOVEMENT = "mindful_movement"
    MINDFUL_EATING = "mindful_eating"
    OTHER = "other"


class SocialSkillDomain(Enum):
    """
    Enumeration of social skill domains targeted by the intervention.

    Defined in T017b and T031.
    FR-010 requires mapping keywords to these domains.
    """
    COMMUNICATION = "communication"
    PEER_INTERACTION = "peer_interaction"
    EMOTIONAL_REGULATION = "emotional_regulation"
    MIXED = "mixed"


class RegistrySource(Enum):
    """
    Source registry for the study data.

    Constitution Principle VI restricts sources to ClinicalTrials.gov and OSF.
    FR-001 mandates data collection from these specific registries.
    """
    CLINICAL_TRIALS_GOV = "ClinicalTrials.gov"
    OSF = "OSF"


class BlindingStatus(Enum):
    """
    Status of blinding in the study.

    FR-008 requires capturing blinding status for quality assessment.
    """
    SINGLE_BLIND = "single"
    DOUBLE_BLIND = "double"
    NOT_BLINDED = "not_blinded"
    NOT_REPORTED = "not_reported"


class Study(BaseModel):
    """
    Represents a single study record extracted from a clinical trial registry.

    Constitution Principle II (Verified Accuracy): All fields must be derived from
    verified registry metadata or validated extraction logic.
    FR-007 (Data Integrity): Schema validation ensures no malformed data enters the pipeline.
    FR-003: Intervention components must be explicitly detected.
    FR-010: Social skill domain must be categorized.
    """
    model_config = ConfigDict(use_enum_values=True, str_strip_whitespace=True)

    id: str = Field(..., description="Unique registry identifier (e.g., NCT number or OSF ID).")
    title: str = Field(..., description="Full title of the study.")
    registry: RegistrySource = Field(..., description="Source registry (Constitution Principle VI).")
    age_range_min: Optional[float] = Field(None, description="Minimum age of participants.")
    age_range_max: Optional[float] = Field(None, description="Maximum age of participants.")
    diagnosis: str = Field(..., description="Primary diagnosis criteria (e.g., ASD, Autistic Disorder).")
    outcomes: List[str] = Field(..., description="List of outcome measures used (must be validated).")
    intervention_components: List[MindfulnessComponent] = Field(
        default_factory=list,
        description="Detected mindfulness components (FR-003)."
    )
    delivery_format: DeliveryFormat = Field(
        default=DeliveryFormat.NOT_REPORTED,
        description="Delivery format of the intervention (Constitution Principle VII)."
    )
    follow_up_months: Optional[float] = Field(None, description="Follow-up duration in months.")
    abstract_text: Optional[str] = Field(None, description="Extracted abstract text (FR-009).")
    social_skill_domain: Optional[SocialSkillDomain] = Field(
        None,
        description="Targeted social skill domain (FR-010)."
    )
    blinding_status: Optional[BlindingStatus] = Field(None, description="Blinding status of the study.")
    n_treatment: Optional[int] = Field(None, description="Number of participants in treatment group.")
    n_control: Optional[int] = Field(None, description="Number of participants in control group.")
    mean_treatment: Optional[float] = Field(None, description="Mean outcome for treatment group.")
    mean_control: Optional[float] = Field(None, description="Mean outcome for control group.")
    sd_treatment: Optional[float] = Field(None, description="Standard deviation for treatment group.")
    sd_control: Optional[float] = Field(None, description="Standard deviation for control group.")
    registry_url: Optional[str] = Field(None, description="URL to the registry entry.")
    retrieval_timestamp: Optional[str] = Field(None, description="ISO timestamp of data retrieval.")

    @field_validator('age_range_min', 'age_range_max')
    @classmethod
    def validate_age(cls, v: Optional[float]) -> Optional[float]:
        """
        Validate age values are within reasonable bounds for pediatric ASD research.
        Constitution Principle II: Ensures data accuracy by rejecting impossible values.
        """
        if v is None:
            return v
        if v < 0 or v > 100:
            raise ValueError(f"Age must be between 0 and 100, got {v}")
        return v

    @field_validator('outcomes')
    @classmethod
    def validate_outcomes(cls, v: List[str]) -> List[str]:
        """
        Validate that outcomes are non-empty strings.
        FR-007: Ensures data integrity by preventing empty outcome lists.
        """
        if not v:
            raise ValueError("Outcomes list cannot be empty")
        return [str(o).strip() for o in v if str(o).strip()]


class EffectSize(BaseModel):
    """
    Represents a calculated effect size (Hedges' g) for a specific study comparison.

    Constitution Principle II: Calculations must be reproducible and accurate.
    FR-004: Requires Hedges' g with small-sample correction.
    """
    study_id: str = Field(..., description="Reference to the parent Study.id.")
    hedges_g: float = Field(..., description="Calculated Hedges' g effect size.")
    se: float = Field(..., description="Standard error of the effect size.")
    ci_lower: float = Field(..., description="Lower bound of 95% confidence interval.")
    ci_upper: float = Field(..., description="Upper bound of 95% confidence interval.")
    n_treatment: int = Field(..., description="Sample size of treatment group.")
    n_control: int = Field(..., description="Sample size of control group.")
    calculation_method: str = Field(
        default="hedges_g_correction",
        description="Method used for calculation (FR-004)."
    )

    @field_validator('hedges_g', 'se', 'ci_lower', 'ci_upper')
    @classmethod
    def validate_finite(cls, v: float) -> float:
        """
        Ensure effect size metrics are finite numbers.
        Constitution Principle V: Fail fast on invalid numerical results.
        """
        if not math.isfinite(v):
            raise ValueError(f"Value must be finite, got {v}")
        return v

    @field_validator('n_treatment', 'n_control')
    @classmethod
    def validate_sample_size(cls, v: int) -> int:
        """
        Ensure sample sizes are positive integers.
        FR-004: Required for effect size calculation.
        """
        if v <= 0:
            raise ValueError(f"Sample size must be positive, got {v}")
        return v


class MetaAnalysisResult(BaseModel):
    """
    Represents the aggregated results of a meta-analysis.

    Constitution Principle II: Aggregated statistics must be derived from verified inputs.
    FR-005: Requires random-effects model and subgroup analysis.
    """
    model_config = ConfigDict(use_enum_values=True)

    analysis_type: str = Field(..., description="Type of analysis (e.g., 'random_effects', 'subgroup').")
    pooled_effect_size: Optional[float] = Field(None, description="Pooled Hedges' g.")
    pooled_se: Optional[float] = Field(None, description="Pooled standard error.")
    ci_lower: Optional[float] = Field(None, description="Lower CI of pooled effect.")
    ci_upper: Optional[float] = Field(None, description="Upper CI of pooled effect.")
    i_squared: Optional[float] = Field(None, description="Heterogeneity statistic I².")
    q_statistic: Optional[float] = Field(None, description="Cochran's Q statistic.")
    p_value: Optional[float] = Field(None, description="P-value for heterogeneity or pooled effect.")
    k_studies: int = Field(..., description="Number of studies included in analysis.")
    subgroup_breakdown: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Results broken down by subgroup (e.g., domain, format)."
    )
    method: str = Field(
        default="restricted_maximum_likelihood",
        description="Estimation method for random effects (FR-005)."
    )
    timestamp: Optional[str] = Field(None, description="ISO timestamp of analysis run.")

    @field_validator('pooled_effect_size', 'i_squared', 'q_statistic', 'p_value')
    @classmethod
    def validate_metrics(cls, v: Optional[float]) -> Optional[float]:
        """
        Ensure metrics are finite if present.
        Constitution Principle V: Fail fast on invalid statistical results.
        """
        if v is None:
            return v
        if not math.isfinite(v):
            raise ValueError(f"Metric must be finite, got {v}")
        return v