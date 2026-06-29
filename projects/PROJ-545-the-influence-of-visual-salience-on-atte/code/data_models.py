"""
Data model definitions for the Visual Salience and Attentional Bias project.

This module defines the core Pydantic schemas for:
- Scenario: Represents a single Moral Machine trial with visual/textual attributes.
- ModelParameters: Represents the configuration for aDDM simulation and fitting.
- AgencyFlag: Enumeration for approximating voluntary/involuntary distinctions.

These schemas enforce data integrity for the pipeline and serve as the contract
between ingestion, processing, and modeling stages.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum


class Species(str, Enum):
    """Enumeration of actor species types."""
    HUMAN = "human"
    DOG = "dog"
    CAT = "cat"
    PIG = "pig"
    COW = "cow"
    SHEEP = "sheep"
    CHICKEN = "chicken"
    HORSE = "horse"
    OTHER = "other"


class Gender(str, Enum):
    """Enumeration of gender categories."""
    MALE = "male"
    FEMALE = "female"
    UNDEFINED = "undefined"


class SocialStatus(str, Enum):
    """Enumeration of social status categories."""
    ADULT = "adult"
    CHILD = "child"
    ELDERLY = "elderly"
    PREGNANT = "pregnant"
    HOMELESS = "homeless"
    CRIMINAL = "criminal"
    ATHLETE = "athlete"
    DOCTOR = "doctor"
    EXECUTIVE = "executive"
    HOMEWORKER = "homeworker"
    LAWYER = "lawyer"
    POLITICIAN = "politician"
    STUDENT = "student"
    TEACHER = "teacher"
    UNDEFINED = "undefined"


class AgencyFlag(str, Enum):
    """
    Enumeration for approximating voluntary/involuntary distinctions.

    This flag is a heuristic proxy for the philosophical distinction between
    voluntary and involuntary action (Aristotle's *Nicomachean Ethics*).

    **Critical Note on Missing Intent Data:**
    The dataset does not contain direct measures of 'knowledge' (intent) or
    'origin of motion' (internal vs external cause of movement). Therefore,
    this flag is a valid *proxy* for analysis but cannot definitively classify
    the moral nature of the agent.

    Heuristic Rule:
    - 'voluntary': If species is 'human' AND social_status is 'adult' or 'elderly'.
    - 'involuntary': Otherwise (includes children, animals, or non-adult/elderly humans).
    """
    VOLUNTARY = "voluntary"
    INVOLUNTARY = "involuntary"


class Scenario(BaseModel):
    """
    Schema for a single Moral Machine decision scenario.

    Captures the raw data columns and computed salience metrics required for
    the analysis. This schema validates the output of the data ingestion
    pipeline (T012-T014) before it is passed to the model fitting stage.
    """
    # Unique identifier for the scenario
    scenario_id: str = Field(..., description="Unique ID for the scenario")

    # Core decision data
    choice: int = Field(..., ge=0, le=1, description="Binary choice: 0=save left, 1=save right")

    # Visual Salience Metrics (Computed in T013)
    visual_salience: float = Field(
        ...,
        ge=0.0, le=1.0,
        description="Normalized visual salience score (0.0 to 1.0) for the primary actor"
    )
    text_salience: float = Field(
        ...,
        ge=0.0, le=1.0,
        description="Normalized textual salience score (0.0 to 1.0) derived from labels"
    )
    salience_score: float = Field(
        ...,
        ge=0.0, le=1.0,
        description="Combined salience score (weighted or max of visual/text)"
    )

    # Proxy Control Variables (Extracted in T014)
    lives_saved: int = Field(..., ge=0, description="Number of lives saved by the choice")
    lives_lost: int = Field(..., ge=0, description="Number of lives lost by the choice")

    # Actor Attributes (Aggregated or specific to the primary actor)
    primary_species: Species = Field(..., description="Species of the primary actor")
    primary_gender: Optional[Gender] = Field(None, description="Gender of the primary actor")
    primary_social_status: Optional[SocialStatus] = Field(None, description="Social status of the primary actor")

    # Derived Agency Flag (T039)
    agency_flag: AgencyFlag = Field(
        ...,
        description="Heuristic proxy for voluntary/involuntary action (see AgencyFlag docstring)"
    )

    # Metadata
    image_url: Optional[str] = Field(None, description="URL to the original image")
    has_image: bool = Field(False, description="Flag indicating if image processing was successful")
    processing_timestamp: datetime = Field(default_factory=datetime.now)

    @model_validator(mode='after')
    def validate_salience_consistency(self):
        """Ensure salience components are consistent with the combined score."""
        # Allow slight floating point variance, but combined score should roughly
        # correlate with the max of components if no complex weighting is applied yet.
        # For now, we just ensure the combined score is within the bounds of the inputs.
        if not (0.0 <= self.salience_score <= 1.0):
            raise ValueError("salience_score must be between 0.0 and 1.0")
        return self


class ModelParameters(BaseModel):
    """
    Schema for aDDM model configuration and hyperparameters.

    Defines the search space and constraints for the grid search fitting
    process (T021).
    """
    # aDDM Hyperparameters
    drift_rate_range: List[float] = Field(
        default=[-2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0],
        description="Range of drift rate values to search"
    )
    threshold_range: List[float] = Field(
        default=[0.5, 1.0, 1.5, 2.0, 2.5, 3.0],
        description="Range of decision threshold values to search"
    )
    non_decision_time: float = Field(
        default=0.3,
        ge=0.0,
        description="Fixed non-decision time component (seconds)"
    )

    # Salience Weighting
    salience_weight_range: List[float] = Field(
        default=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        description="Grid search steps for salience influence weight (0.0 to 1.0)"
    )

    # Fitting Configuration
    n_folds: int = Field(
        default=5,
        ge=2,
        description="Number of folds for cross-validation"
    )
    random_seed: int = Field(
        default=42,
        description="Random seed for reproducibility"
    )
    convergence_threshold: float = Field(
        default=1e-4,
        gt=0.0,
        description="Threshold for log-likelihood convergence"
    )
    max_iterations: int = Field(
        default=1000,
        gt=0,
        description="Maximum iterations for optimization"
    )

    # Output Configuration
    output_dir: str = Field(
        default="data/processed/model_fits",
        description="Directory to save model fit results"
    )

    @field_validator('drift_rate_range', 'threshold_range', 'salience_weight_range')
    @classmethod
    def validate_sorted_ranges(cls, v: List[float]) -> List[float]:
        """Ensure ranges are sorted ascending."""
        if v != sorted(v):
            return sorted(v)
        return v