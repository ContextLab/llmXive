from datetime import date
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict
import math

class RegistrySource(str, Enum):
    CLINICAL_TRIALS = "ClinicalTrials.gov"
    OSF = "OSF"

class DeliveryFormat(str, Enum):
    CAREGIVER_MEDIATED = "caregiver-mediated"
    CHILD_LED = "child-led"
    MIXED = "mixed"
    NOT_REPORTED = "not-reported"

class MindfulnessComponent(str, Enum):
    BREATHING = "breathing"
    BODY_SCAN = "body scan"
    MINDFUL_MOVEMENT = "mindful movement"
    MINDFUL_EATING = "mindful eating"
    NONE = "none"

class SocialSkillDomain(str, Enum):
    COMMUNICATION = "communication"
    PEER_INTERACTION = "peer interaction"
    EMOTIONAL_REGULATION = "emotional regulation"
    MIXED = "mixed"
    OTHER = "other"

class BlindingStatus(str, Enum):
    BLINDED = "blinded"
    UNBLINDED = "unblinded"
    MIXED = "mixed"
    UNKNOWN = "unknown"

class AgeRange(BaseModel):
    min: int = Field(..., ge=6, le=12)
    max: int = Field(..., ge=6, le=12)

    @field_validator('max')
    @classmethod
    def max_must_be_gte_min(cls, v, info):
        data = info.data
        if 'min' in data and v < data['min']:
            raise ValueError('max must be >= min')
        return v

class Study(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    registry: RegistrySource
    age_range: AgeRange
    diagnosis: str = Field(..., const="ASD")
    outcomes: List[str]
    intervention_components: List[MindfulnessComponent]
    delivery_format: DeliveryFormat
    social_skill_domain: SocialSkillDomain
    follow_up: Optional[str] = None
    abstract_text: Optional[str] = None
    domain_notes: Optional[str] = None
    blinded_assessment_flag: bool
    rater_type: BlindingStatus

class EffectSize(BaseModel):
    study_id: str
    hedges_g: float
    se: float
    ci_lower: float
    ci_upper: float
    n_treatment: int = Field(..., ge=1)
    n_control: int = Field(..., ge=1)
    rater_blinding_status: BlindingStatus

class SubgroupResult(BaseModel):
    name: str
    n_studies: int
    pooled_effect: float
    ci_lower: float
    ci_upper: float
    heterogeneity_i2: Optional[float] = None

class MetaAnalysisResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    total_studies: int
    pooled_effect_size: float
    pooled_se: float
    ci_lower: float
    ci_upper: float
    model_type: str  # 'fixed' or 'random'
    heterogeneity_q: Optional[float] = None
    heterogeneity_i2: Optional[float] = None
    subgroup_results: List[SubgroupResult] = []
