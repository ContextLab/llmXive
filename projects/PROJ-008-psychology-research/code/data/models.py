"""
Pydantic data models for the llmXive psychology research pipeline.

This module defines the core data structures for Studies, Effect Sizes, and
Meta-Analysis results used throughout the data collection, cleaning, and
analysis phases.
"""

from datetime import date
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict
import math


class RegistrySource(str, Enum):
    """Enum representing the source registry of a study."""
    CLINICAL_TRIALS = "ClinicalTrials.gov"
    OSF = "OSF"


class DeliveryFormat(str, Enum):
    """Enum representing the delivery format of the intervention."""
    CAREGIVER_MEDIATED = "caregiver-mediated"
    CHILD_LED = "child-led"
    MIXED = "mixed"
    NOT_REPORTED = "not-reported"


class MindfulnessComponent(str, Enum):
    """Enum representing specific mindfulness intervention components."""
    BREATHING = "breathing"
    BODY_SCAN = "body scan"
    MINDFUL_MOVEMENT = "mindful movement"
    MINDFUL_EATING = "mindful eating"
    NONE = "none"


class SocialSkillDomain(str, Enum):
    """Enum representing the primary social skill domain targeted."""
    COMMUNICATION = "communication"
    PEER_INTERACTION = "peer interaction"
    EMOTIONAL_REGULATION = "emotional regulation"
    MIXED = "mixed"
    OTHER = "other"


class BlindingStatus(str, Enum):
    """Enum representing the blinding status of the outcome rater."""
    BLINDED = "blinded"
    UNBLINDED = "unblinded"
    UNKNOWN = "unknown"


class AgeRange(BaseModel):
    """
    Represents the age range of participants in a study.

    Attributes:
        min (int): Minimum age of participants.
        max (int): Maximum age of participants.
    """
    model_config = ConfigDict(validate_assignment=True)
    min: int = Field(..., ge=0, description="Minimum age of participants")
    max: int = Field(..., ge=0, description="Maximum age of participants")

    @field_validator('max')
    @classmethod
    def max_must_be_greater_than_min(cls, v, info) -> int:
        """Ensure max age is not less than min age."""
        if info.data and 'min' in info.data:
            if v < info.data['min']:
                raise ValueError('max age cannot be less than min age')
        return v


class Study(BaseModel):
    """
    Represents a single clinical study record.

    This model captures the core metadata and intervention details for a study
    ingested from registries like ClinicalTrials.gov or OSF.

    Attributes:
        id (str): Unique identifier for the study.
        title (str): Title of the study.
        registry (RegistrySource): Source registry of the study.
        age_range (AgeRange): Age range of the study participants.
        diagnosis (str): Primary diagnosis (expected "ASD").
        outcomes (List[str]): List of outcome measures used.
        intervention_components (List[MindfulnessComponent]): Components of the intervention.
        delivery_format (DeliveryFormat): Format of intervention delivery.
        social_skill_domain (SocialSkillDomain): Primary domain targeted.
        follow_up (Optional[str]): Follow-up duration description.
        abstract_text (Optional[str]): Abstract text of the study.
        rater_type (BlindingStatus): Type of rater used.
        blinded_assessment_flag (bool): Flag indicating if assessment was blinded.
    """
    model_config = ConfigDict(use_enum_values=True)

    id: str = Field(..., description="Unique study identifier")
    title: str = Field(..., description="Title of the study")
    registry: RegistrySource = Field(..., description="Source registry")
    age_range: AgeRange = Field(..., description="Participant age range")
    diagnosis: str = Field(..., const="ASD", description="Primary diagnosis")
    outcomes: List[str] = Field(default_factory=list, description="Outcome measures")
    intervention_components: List[MindfulnessComponent] = Field(
        default_factory=list, description="Intervention components"
    )
    delivery_format: DeliveryFormat = Field(..., description="Delivery format")
    social_skill_domain: SocialSkillDomain = Field(
        default=SocialSkillDomain.OTHER, description="Social skill domain"
    )
    follow_up: Optional[str] = Field(None, description="Follow-up duration")
    abstract_text: Optional[str] = Field(None, description="Abstract text")
    rater_type: BlindingStatus = Field(
        default=BlindingStatus.UNKNOWN, description="Rater type"
    )
    blinded_assessment_flag: bool = Field(
        default=False, description="Blinded assessment flag"
    )

    @field_validator('diagnosis')
    @classmethod
    def validate_diagnosis(cls, v) -> str:
        """Ensure diagnosis is ASD."""
        if v != "ASD":
            raise ValueError("Diagnosis must be 'ASD' for this pipeline")
        return v


class EffectSize(BaseModel):
    """
    Represents a calculated effect size for a study.

    Attributes:
        study_id (str): Reference to the study ID.
        hedges_g (float): Calculated Hedges' g effect size.
        se (float): Standard error of the effect size.
        ci_lower (float): Lower bound of the confidence interval.
        ci_upper (float): Upper bound of the confidence interval.
        n_treatment (int): Sample size of the treatment group.
        n_control (int): Sample size of the control group.
        rater_blinding_status (BlindingStatus): Blinding status of the rater.
    """
    study_id: str = Field(..., description="Reference study ID")
    hedges_g: float = Field(..., description="Hedges' g effect size")
    se: float = Field(..., description="Standard error")
    ci_lower: float = Field(..., description="CI lower bound")
    ci_upper: float = Field(..., description="CI upper bound")
    n_treatment: int = Field(..., ge=1, description="Treatment group size")
    n_control: int = Field(..., ge=1, description="Control group size")
    rater_blinding_status: BlindingStatus = Field(
        default=BlindingStatus.UNKNOWN, description="Rater blinding status"
    )

    @field_validator('hedges_g', 'se', 'ci_lower', 'ci_upper')
    @classmethod
    def validate_finite_numbers(cls, v) -> float:
        """Ensure numerical fields are finite."""
        if not math.isfinite(v):
            raise ValueError("Effect size metrics must be finite numbers")
        return v


class SubgroupResult(BaseModel):
    """
    Represents results for a specific subgroup analysis.

    Attributes:
        subgroup_name (str): Name of the subgroup.
        pooled_effect_size (float): Pooled effect size for the subgroup.
        ci_lower (float): Lower CI bound.
        ci_upper (float): Upper CI bound.
        n_studies (int): Number of studies in the subgroup.
        heterogeneity_i2 (float): Heterogeneity statistic I-squared.
    """
    subgroup_name: str = Field(..., description="Name of the subgroup")
    pooled_effect_size: float = Field(..., description="Pooled effect size")
    ci_lower: float = Field(..., description="CI lower bound")
    ci_upper: float = Field(..., description="CI upper bound")
    n_studies: int = Field(..., description="Number of studies")
    heterogeneity_i2: float = Field(..., description="I-squared heterogeneity")


class MetaAnalysisResult(BaseModel):
    """
    Represents the final output of a meta-analysis.

    Attributes:
        pooled_effect_size (float): Overall pooled effect size.
        ci_lower (float): Lower bound of the 95% CI.
        ci_upper (float): Upper bound of the 95% CI.
        model_type (str): Type of model used (fixed/random).
        heterogeneity_i2 (float): Overall heterogeneity I-squared.
        heterogeneity_q (float): Cochran's Q statistic.
        p_value (float): P-value for the overall effect.
        subgroup_results (List[SubgroupResult]): Results for subgroups if analyzed.
    """
    pooled_effect_size: float = Field(..., description="Overall pooled effect size")
    ci_lower: float = Field(..., description="CI lower bound")
    ci_upper: float = Field(..., description="CI upper bound")
    model_type: str = Field(..., description="Model type used")
    heterogeneity_i2: float = Field(..., description="I-squared")
    heterogeneity_q: float = Field(..., description="Cochran's Q")
    p_value: float = Field(..., description="P-value")
    subgroup_results: List[SubgroupResult] = Field(
        default_factory=list, description="Subgroup analysis results"
    )