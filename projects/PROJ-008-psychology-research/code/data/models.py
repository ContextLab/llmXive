"""
Pydantic models for the Psychology Research Pipeline.

These models enforce data integrity and verified accuracy as per
Constitution Principle II and FR-007.
"""

from datetime import date
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict
import math

# ---------------------------------------------------------------------------
# Enums for Categorical Data
# ---------------------------------------------------------------------------

class DeliveryFormat(Enum):
    """
    Enum for intervention delivery formats.
    Source: FR-003 (Standardized Variables)
    """
    IN_PERSON = "in_person"
    VIRTUAL = "virtual"
    HYBRID = "hybrid"
    SELF_GUIDED = "self_guided"

class MindfulnessComponent(Enum):
    """
    Enum for specific mindfulness components extracted from studies.
    Source: FR-003, FR-009
    """
    BREATHING = "breathing"
    BODY_SCAN = "body_scan"
    MEDITATION = "meditation"
    YOGA = "yoga"
    MINDFUL_LISTENING = "mindful_listening"
    OTHER = "other"

class SocialSkillDomain(Enum):
    """
    Enum for social skill outcome domains.
    Source: FR-010
    """
    COMMUNICATION = "communication"
    INTERACTION = "interaction"
    EMOTION_RECOGNITION = "emotion_recognition"
    PEER_RELATIONS = "peer_relations"
    BEHAVIOR_REGULATION = "behavior_regulation"

class RegistrySource(Enum):
    """
    Enum for study registry sources.
    Source: Constitution Principle VI (Clinical Trial Registry Integrity)
    """
    CLINICAL_TRIALS_GOV = "ClinicalTrials.gov"
    OSF = "OSF"

class BlindingStatus(Enum):
    """
    Enum for assessor blinding status.
    Source: FR-007, T007b
    """
    SINGLE_BLIND = "single-blind"
    DOUBLE_BLIND = "double-blind"
    UNBLINDED = "unblinded"
    NOT_REPORTED = "not-reported"

# ---------------------------------------------------------------------------
# Core Data Models
# ---------------------------------------------------------------------------

class Study(BaseModel):
    """
    Represents a single study record extracted from a registry.

    Attributes:
        id (str): Unique identifier for the study.
            Source: FR-007 (Data Integrity), Constitution Principle V
        title (str): Official title of the study.
            Source: FR-002
        registry (RegistrySource): Source registry.
            Source: Constitution Principle VI
        age_range (str): Target age range (e.g., "6-12").
            Source: FR-003
        diagnosis (str): Primary diagnosis (must be ASD).
            Source: FR-003
        outcomes (List[str]): List of outcome measures used.
            Source: FR-010
        intervention_components (List[MindfulnessComponent]): Components used.
            Source: FR-003
        delivery_format (DeliveryFormat): How the intervention was delivered.
            Source: FR-003
        follow_up (str): Duration of follow-up.
            Source: FR-012
        abstract_text (Optional[str]): Extracted abstract text.
            Source: FR-009
        assessor_blinding (BlindingStatus): Blinding status of assessors.
            Source: FR-007, T007b
        registry_url (Optional[str]): Direct link to registry entry.
            Source: Constitution Principle VI
        retrieval_timestamp (Optional[str]): When data was fetched.
            Source: Constitution Principle VI
    """
    model_config = ConfigDict(use_enum_values=True, str_strip_whitespace=True)

    id: str = Field(..., description="Unique study identifier")
    title: str = Field(..., description="Study title")
    registry: RegistrySource = Field(..., description="Source registry")
    age_range: str = Field(..., description="Target age range")
    diagnosis: str = Field(..., description="Primary diagnosis")
    outcomes: List[str] = Field(default_factory=list, description="Outcome measures")
    intervention_components: List[MindfulnessComponent] = Field(default_factory=list)
    delivery_format: DeliveryFormat = Field(..., description="Delivery format")
    follow_up: str = Field(..., description="Follow-up duration")
    abstract_text: Optional[str] = Field(None, description="Abstract text")
    assessor_blinding: BlindingStatus = Field(..., description="Blinding status")
    registry_url: Optional[str] = Field(None, description="Registry URL")
    retrieval_timestamp: Optional[str] = Field(None, description="Retrieval time")

    @field_validator('age_range')
    @classmethod
    def validate_age_range(cls, v: str) -> str:
        """
        Validates that the age range is within the acceptable bounds (6-12).
        Source: FR-003 (Inclusion Criteria)
        """
        if not v:
            return v
        # Simple heuristic check for inclusion criteria
        # In a full pipeline, this would parse "6-12" specifically
        if "6" not in v and "7" not in v and "8" not in v and "9" not in v and "10" not in v and "11" not in v and "12" not in v:
            raise ValueError("Age range must include children between 6 and 12.")
        return v

class EffectSize(BaseModel):
    """
    Represents a calculated effect size for a specific study comparison.

    Attributes:
        study_id (str): Reference to the parent Study.
            Source: FR-007
        hedges_g (float): Hedges' g effect size with small-sample correction.
            Source: FR-004
        se (float): Standard error of the effect size.
            Source: FR-004
        ci_lower (float): Lower bound of 95% CI.
            Source: FR-004
        ci_upper (float): Upper bound of 95% CI.
            Source: FR-004
        n_treatment (int): Sample size of treatment group.
            Source: FR-004
        n_control (int): Sample size of control group.
            Source: FR-004
        calculation_method (str): Method used for calculation.
            Source: FR-004
    """
    model_config = ConfigDict(use_enum_values=True)

    study_id: str = Field(..., description="Reference to study ID")
    hedges_g: float = Field(..., description="Hedges' g value")
    se: float = Field(..., description="Standard error")
    ci_lower: float = Field(..., description="95% CI Lower")
    ci_upper: float = Field(..., description="95% CI Upper")
    n_treatment: int = Field(..., description="Treatment N")
    n_control: int = Field(..., description="Control N")
    calculation_method: str = Field("Hedges' g (small-sample corrected)", description="Method")

    @field_validator('hedges_g', 'se', 'ci_lower', 'ci_upper')
    @classmethod
    def validate_finite(cls, v: float) -> float:
        """
        Ensures effect size values are finite numbers.
        Source: Constitution Principle II (Verified Accuracy)
        """
        if math.isnan(v) or math.isinf(v):
            raise ValueError("Effect size metrics must be finite numbers.")
        return v

class MetaAnalysisResult(BaseModel):
    """
    Represents the aggregated results of a meta-analysis.

    Attributes:
        pooled_effect (float): Pooled effect size.
            Source: FR-005
        pooled_se (float): Standard error of the pooled effect.
            Source: FR-005
        ci_lower (float): Lower bound of pooled 95% CI.
            Source: FR-005
        ci_upper (float): Upper bound of pooled 95% CI.
            Source: FR-005
        i_squared (float): I-squared heterogeneity statistic.
            Source: FR-005
        q_statistic (float): Cochran's Q statistic.
            Source: FR-005
        p_value (float): P-value for heterogeneity.
            Source: FR-005
        model_type (str): 'random-effects' or 'fixed-effects'.
            Source: FR-005
        k_studies (int): Number of studies included.
            Source: FR-005
        total_n (int): Total sample size across studies.
            Source: FR-005
    """
    model_config = ConfigDict(use_enum_values=True)

    pooled_effect: float = Field(..., description="Pooled effect size")
    pooled_se: float = Field(..., description="Pooled SE")
    ci_lower: float = Field(..., description="Pooled CI Lower")
    ci_upper: float = Field(..., description="Pooled CI Upper")
    i_squared: float = Field(..., description="I-squared statistic")
    q_statistic: float = Field(..., description="Cochran's Q")
    p_value: float = Field(..., description="Heterogeneity p-value")
    model_type: str = Field(..., description="Model type")
    k_studies: int = Field(..., description="Number of studies")
    total_n: int = Field(..., description="Total N")
    subgroup: Optional[str] = Field(None, description="Subgroup label if applicable")

    @field_validator('pooled_effect', 'i_squared', 'q_statistic', 'p_value')
    @classmethod
    def validate_finite(cls, v: float) -> float:
        """
        Ensures meta-analysis metrics are finite.
        Source: Constitution Principle II
        """
        if math.isnan(v) or math.isinf(v):
            raise ValueError("Meta-analysis metrics must be finite.")
        return v