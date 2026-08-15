"""
Base data models for the sensitivity analysis pipeline.

Defines Pydantic models for:
- DatasetProfile: Metadata and violation statistics for an ingested dataset.
- StabilityResult: Coefficient stability metrics across resampling tiers.
- InteractionModel: Results from the meta-analysis regression.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator, ConfigDict
import numpy as np


class ViolationSeverity(str, Enum):
    """Severity classification for OLS assumption violations."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class DatasetProfile(BaseModel):
    """
    Profile of a single dataset including violation statistics.

    Attributes:
        dataset_id: Unique identifier for the dataset.
        source_url: Original URL or path where data was fetched.
        n_rows: Total number of observations.
        n_features: Total number of features (excluding target).
        condition_number: Condition number of the feature matrix (collinearity).
        breusch_pagan_stat: Breusch-Pagan heteroskedasticity statistic.
        breusch_pagan_pvalue: P-value for the Breusch-Pagan test.
        max_cooks_distance: Maximum Cook's distance value (outlier influence).
        violation_severity: Classified severity of assumption violations.
        timestamp: ISO timestamp of when the profile was generated.
        checksum: MD5 checksum of the raw data file for validation.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    dataset_id: str = Field(..., description="Unique identifier for the dataset")
    source_url: str = Field(..., description="Source URL or path")
    n_rows: int = Field(..., ge=1, description="Number of observations")
    n_features: int = Field(..., ge=1, description="Number of features")
    condition_number: float = Field(..., ge=0.0, description="Condition number")
    breusch_pagan_stat: float = Field(..., ge=0.0, description="BP statistic")
    breusch_pagan_pvalue: float = Field(..., ge=0.0, le=1.0, description="BP p-value")
    max_cooks_distance: float = Field(..., ge=0.0, description="Max Cook's distance")
    violation_severity: ViolationSeverity = Field(..., description="Severity classification")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Generation time")
    checksum: Optional[str] = Field(None, description="MD5 checksum of raw data")

    @field_validator('breusch_pagan_pvalue')
    @classmethod
    def validate_pvalue(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("P-value must be between 0 and 1")
        return v


class StabilityResult(BaseModel):
    """
    Stability metrics for a specific sample size tier.

    Attributes:
        dataset_id: Reference to the dataset used.
        tier_percentage: The sample size tier (e.g., 10, 25, 50).
        n_subsets: Number of valid subsets generated.
        mean_coefficients: Mean of coefficients across valid subsets.
        std_coefficients: Empirical standard deviation of coefficients across subsets.
        subset_sizes: List of actual sizes of the subsets used (for audit).
        fit_success_rate: Ratio of successful fits to total attempts.
        timestamp: ISO timestamp of generation.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    dataset_id: str
    tier_percentage: int = Field(..., ge=1, le=100, description="Sample size percentage")
    n_subsets: int = Field(..., ge=1, description="Number of valid subsets")
    mean_coefficients: Dict[str, float] = Field(..., description="Mean coefficients")
    std_coefficients: Dict[str, float] = Field(..., description="Std dev of coefficients")
    subset_sizes: List[int] = Field(..., description="Actual subset sizes")
    fit_success_rate: float = Field(..., ge=0.0, le=1.0, description="Success rate")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @field_validator('fit_success_rate')
    @classmethod
    def validate_rate(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("Success rate must be between 0 and 1")
        return v


class InteractionModel(BaseModel):
    """
    Results from the meta-analysis regression (US3).

    Attributes:
        model_type: Type of model (e.g., "OLS_Interaction").
        outcome_variable: The dependent variable (e.g., "empirical_variance").
        predictors: List of predictor variable names used.
        coefficients: Fitted coefficients for the meta-model.
        p_values: P-values for the coefficients.
        r_squared: R-squared value of the meta-model.
        interaction_term: Name of the interaction term if present.
        interaction_significance: Boolean indicating if interaction is significant (p < 0.05).
        sensitivity_sweep_results: Optional results from the BP p-value sweep.
        timestamp: ISO timestamp of generation.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    model_type: str = Field(default="OLS_Interaction")
    outcome_variable: str
    predictors: List[str]
    coefficients: Dict[str, float]
    p_values: Dict[str, float]
    r_squared: float = Field(..., ge=0.0, le=1.0)
    interaction_term: Optional[str] = None
    interaction_significance: Optional[bool] = None
    sensitivity_sweep_results: Optional[List[Dict[str, Any]]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @field_validator('r_squared')
    @classmethod
    def validate_r2(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("R-squared must be between 0 and 1")
        return v