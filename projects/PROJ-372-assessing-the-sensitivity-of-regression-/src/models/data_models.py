"""
Data models for the sensitivity analysis pipeline.

Defines Pydantic models for DatasetProfile, StabilityResult, and InteractionModel.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, field_validator
import math

class DatasetProfile(BaseModel):
    """
    Model representing the profile of a dataset including OLS assumption violations.
    """
    dataset_name: str
    condition_number: float = Field(..., ge=0, description="Condition number of the design matrix")
    breusch_pagan_stat: float = Field(..., ge=0, description="Breusch-Pagan statistic for heteroscedasticity")
    breusch_pagan_p_value: float = Field(..., ge=0, le=1, description="P-value for Breusch-Pagan test")
    max_cooks_distance: float = Field(..., ge=0, description="Maximum Cook's distance")
    violation_severity: str = Field(..., description="Classified severity: Low, Medium, High")
    n_samples: int = Field(..., gt=0)
    n_predictors: int = Field(..., gt=0)

    @field_validator("violation_severity")
    @classmethod
    def validate_severity(cls, v):
        if v not in ["Low", "Medium", "High"]:
            raise ValueError("violation_severity must be 'Low', 'Medium', or 'High'")
        return v

class StabilityResult(BaseModel):
    """
    Model representing the stability of coefficients across subsets.
    """
    dataset_name: str
    sample_size_tier: str
    subset_size: int
    coefficient_sd: Dict[str, float] = Field(..., description="Standard deviation of each coefficient across subsets")
    n_subsets: int = Field(..., gt=0)

class InteractionModel(BaseModel):
    """
    Model representing the result of the meta-analysis (Multiple Regression).
    Captures the relationship between empirical variance and predictors (condition number, violation severity).
    """
    intercept: float = Field(..., description="Intercept of the regression model")
    coefficients: Dict[str, float] = Field(..., description="Coefficients for condition_number, violation_severity, and interaction")
    p_values: Dict[str, float] = Field(..., description="P-values for the coefficients")
    r_squared: float = Field(..., ge=0, le=1, description="R-squared of the regression model")
    interaction_p_value: float = Field(..., ge=0, le=1, description="P-value for the interaction term")
    summary: str = Field(..., description="Human-readable summary of the model results")

    @field_validator("coefficients")
    @classmethod
    def validate_coefficients_keys(cls, v):
        required_keys = {"condition_number", "violation_severity", "interaction"}
        if not required_keys.issubset(v.keys()):
            raise ValueError(f"coefficients must contain keys: {required_keys}")
        return v

    @field_validator("p_values")
    @classmethod
    def validate_p_values_keys(cls, v):
        required_keys = {"condition_number", "violation_severity", "interaction"}
        if not required_keys.issubset(v.keys()):
            raise ValueError(f"p_values must contain keys: {required_keys}")
        return v
