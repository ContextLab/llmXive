"""
Internal contract definitions for the agriculture optimization pipeline.
Defines Pydantic models for data validation across the pipeline stages.
"""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
import os
from pathlib import Path

# --- Data Ingestion Models ---

class HouseholdRecord(BaseModel):
    """Schema for raw survey data from LSMS-ISA."""
    household_id: int = Field(..., description="Unique household identifier")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude (fuzzed)")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude (fuzzed)")
    land_size: float = Field(..., ge=0, description="Land size in hectares")
    education_level: int = Field(..., ge=0, description="Years of education")
    finance_access: bool = Field(..., description="Access to financial services")
    
    # Practice indicators (binary)
    practice_mixed_farming: bool = Field(default=False, description="Mixed farming practice")
    practice_terracing: bool = Field(default=False, description="Terracing practice")
    practice_conservation_tillage: bool = Field(default=False, description="Conservation tillage")
    practice_agroforestry: bool = Field(default=False, description="Agroforestry practice")
    
    # Support and Outcomes
    extension_visits: int = Field(default=0, ge=0, description="Number of extension visits")
    hlias: int = Field(default=0, ge=0, description="Household Food Insecurity Access Scale")
    
    # Derived/Calculated fields (optional in raw, required in processed)
    CSA_Index: Optional[float] = Field(None, description="Composite CSA adoption index")
    Stability_Score: Optional[float] = Field(None, description="Yield stability score (1/CV)")
    HFIAS: Optional[float] = Field(None, description="Food insecurity score")
    village_id: Optional[str] = Field(None, description="Derived village cluster ID")

class RemoteSensingPixel(BaseModel):
    """Schema for a single satellite pixel observation."""
    pixel_id: str = Field(..., description="Unique pixel identifier")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    acquisition_date: datetime = Field(..., description="Satellite acquisition date")
    cloud_cover: float = Field(..., ge=0.0, le=1.0, description="Cloud cover fraction")
    ndvi: float = Field(..., description="Normalized Difference Vegetation Index")
    source: str = Field(..., description="Data source (e.g., Sentinel-2)")

# --- Processed Analysis Models ---

class AnalysisDatasetRecord(BaseModel):
    """Schema for the final analysis-ready dataset (merged survey + satellite)."""
    household_id: int = Field(..., description="Unique household identifier")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    village_id: str = Field(..., description="Derived village cluster ID for clustering")
    
    # Predictors
    land_size: float = Field(..., ge=0)
    education_level: int = Field(..., ge=0)
    finance_access: bool = Field(...)
    
    # Practice indicators
    practice_mixed_farming: bool = Field(default=False)
    practice_terracing: bool = Field(default=False)
    practice_conservation_tillage: bool = Field(default=False)
    practice_agroforestry: bool = Field(default=False)
    
    # Derived Indices
    CSA_Index: float = Field(..., ge=0, description="Sum of practice indicators or weighted index")
    Stability_Score: float = Field(..., ge=0, description="Inverse of NDVI Coefficient of Variation")
    HFIAS: float = Field(..., description="Food insecurity score")
    extension_visits: int = Field(..., ge=0)
    
    # Metadata
    linkage_status: str = Field(..., description="Status of spatial linkage (linked/aggregated)")

# --- Analysis Output Models ---

class RegressionOutput(BaseModel):
    """Schema for regression model results."""
    model_name: str = Field(..., description="Identifier for the model (e.g., 'Model1_Stability')")
    dependent_variable: str = Field(..., description="Name of the dependent variable")
    independent_variables: List[str] = Field(..., description="List of predictor names")
    
    # Results
    coefficients: Dict[str, float] = Field(..., description="Coefficients for each predictor")
    p_values: Dict[str, float] = Field(..., description="P-values for each predictor")
    adjusted_r_squared: float = Field(..., ge=0, le=1, description="Adjusted R-squared")
    vif_scores: Dict[str, float] = Field(..., description="Variance Inflation Factors")
    
    # Diagnostics
    collinearity_warning: bool = Field(default=False, description="True if any VIF > 5")
    standard_error_type: str = Field(..., description="Type of SE used (e.g., 'cluster_robust', 'robust')")
    n_observations: int = Field(..., ge=1)
    n_clusters: Optional[int] = Field(None, description="Number of clusters if clustered SE used")

class SensitivityResult(BaseModel):
    """Schema for sensitivity analysis results across thresholds."""
    threshold_type: str = Field(..., description="Type of threshold (e.g., 'cloud_cover')")
    threshold_value: float = Field(..., description="The specific threshold value used")
    model_name: str = Field(..., description="Which model this result belongs to")
    coefficient_csa_index: float = Field(..., description="Coefficient for CSA_Index at this threshold")
    p_value_csa_index: float = Field(..., description="P-value for CSA_Index at this threshold")
    n_observations: int = Field(..., ge=1)

# --- Validation Helpers ---

def validate_dataset_schema(data: Dict[str, Any]) -> AnalysisDatasetRecord:
    """
    Validates a dictionary against the AnalysisDatasetRecord schema.
    Raises ValidationError if invalid.
    """
    return AnalysisDatasetRecord(**data)

def validate_regression_output(data: Dict[str, Any]) -> RegressionOutput:
    """
    Validates a dictionary against the RegressionOutput schema.
    Raises ValidationError if invalid.
    """
    return RegressionOutput(**data)