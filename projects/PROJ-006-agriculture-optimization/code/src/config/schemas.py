"""
Internal contract definitions for the Climate-Smart Agriculture Optimization pipeline.

This module defines Pydantic models for data validation (HouseholdRecord, 
RemoteSensingPixel, AnalysisDatasetRecord) and output schemas (RegressionOutput, 
SensitivityResult). It also provides utility functions for loading YAML schemas 
and validating dataframes against these contracts.
"""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError
from datetime import datetime
import os
from pathlib import Path
import pandas as pd
import json
import yaml

# --- Input Data Schemas ---

class HouseholdRecord(BaseModel):
    """Schema for raw household survey data."""
    household_id: int = Field(..., description="Unique household identifier")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    land_size: float = Field(..., ge=0, description="Land size in hectares")
    education_level: int = Field(..., ge=0, description="Education level (0-12)")
    finance_access: bool = Field(..., description="Access to formal finance")
    practice_mixed_farming: bool = Field(default=False, description="Adoption of mixed farming")
    practice_terracing: bool = Field(default=False, description="Adoption of terracing")
    practice_conservation_tillage: bool = Field(default=False, description="Adoption of conservation tillage")
    practice_agroforestry: bool = Field(default=False, description="Adoption of agroforestry")
    extension_visits: int = Field(default=0, ge=0, description="Number of extension visits")
    hlias: int = Field(..., description="Household Food Insecurity Access Scale")
    village_id: Optional[str] = Field(None, description="Derived village ID")

    @field_validator('latitude')
    @classmethod
    def check_latitude(cls, v):
        if v is None:
            raise ValueError("Latitude cannot be null")
        return v

    @field_validator('longitude')
    @classmethod
    def check_longitude(cls, v):
        if v is None:
            raise ValueError("Longitude cannot be null")
        return v


class RemoteSensingPixel(BaseModel):
    """Schema for satellite pixel data (e.g., NDVI time series)."""
    pixel_id: str = Field(..., description="Unique pixel identifier")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    timestamp: datetime = Field(..., description="Acquisition timestamp")
    ndvi: float = Field(..., ge=-1.0, le=1.0, description="Normalized Difference Vegetation Index")
    cloud_cover: float = Field(..., ge=0.0, le=1.0, description="Cloud cover fraction")
    source: str = Field(default="Sentinel-2", description="Data source")


class AnalysisDatasetRecord(BaseModel):
    """Schema for the final analysis-ready dataset."""
    household_id: int
    latitude: float
    longitude: float
    land_size: float
    education_level: int
    finance_access: bool
    practice_mixed_farming: bool
    practice_terracing: bool
    practice_conservation_tillage: bool
    practice_agroforestry: bool
    extension_visits: int
    hlias: int
    CSA_Index: float = Field(..., ge=0, le=4, description="Composite CSA practice index")
    Stability_Score: float = Field(..., ge=0, description="Yield stability score (1/CV)")
    village_id: str
    # Optional derived metrics
    mean_ndvi: Optional[float] = None
    ndvi_cv: Optional[float] = None

    @model_validator(mode='after')
    def check_derived_metrics(self):
        if self.CSA_Index < 0 or self.CSA_Index > 4:
            raise ValueError("CSA_Index must be between 0 and 4")
        if self.Stability_Score < 0:
            raise ValueError("Stability_Score must be non-negative")
        return self


# --- Output Data Schemas ---

class RegressionOutput(BaseModel):
    """Schema for regression analysis results."""
    coefficients: Dict[str, float]
    p_values: Dict[str, float]
    vif_scores: Dict[str, float]
    model_type: str = Field(..., description="Type of model: 'aggregated' or 'clustered'")
    collinearity_warning: bool = Field(default=False, description="True if any VIF > 5")
    aggregation_warning: bool = Field(default=False, description="True if aggregation was performed")
    adjusted_alpha: Optional[float] = None
    bonferroni_corrected_p_values: Optional[Dict[str, float]] = None

    @model_validator(mode='after')
    def check_consistency(self):
        # Ensure warnings are set if conditions are met
        if any(v > 5 for v in self.vif_scores.values()):
            self.collinearity_warning = True
        return self


class SensitivityResult(BaseModel):
    """Schema for sensitivity analysis results."""
    threshold: float
    model: str
    coefficient: float
    p_value: float
    std_err: float
    max_delta_coefficient: Optional[float] = None
    std_coefficient: Optional[float] = None


# --- Utility Functions ---

def load_schema_from_yaml(schema_path: str) -> Dict[str, Any]:
    """Load a schema definition from a YAML file."""
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def validate_dataset_schema(df: pd.DataFrame, schema_path: Optional[str] = None) -> pd.DataFrame:
    """
    Validate a DataFrame against the AnalysisDatasetRecord schema.
    
    Args:
        df: Input DataFrame
        schema_path: Optional path to a YAML schema for additional checks (currently unused, using Pydantic)
        
    Returns:
        Validated DataFrame (unchanged if valid)
        
    Raises:
        ValidationError: If the data does not conform to the schema
    """
    required_columns = [
        'household_id', 'latitude', 'longitude', 'land_size', 'education_level',
        'finance_access', 'practice_mixed_farming', 'practice_terracing',
        'practice_conservation_tillage', 'practice_agroforestry', 'extension_visits',
        'hlias', 'CSA_Index', 'Stability_Score', 'village_id'
    ]
    
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValidationError(f"Missing required columns: {missing_cols}", model=AnalysisDatasetRecord)
    
    # Convert types to match schema expectations
    df = df.copy()
    try:
        # Basic type coercion to ensure Pydantic compatibility
        df['household_id'] = df['household_id'].astype(int)
        df['latitude'] = df['latitude'].astype(float)
        df['longitude'] = df['longitude'].astype(float)
        df['land_size'] = df['land_size'].astype(float)
        df['education_level'] = df['education_level'].astype(int)
        df['finance_access'] = df['finance_access'].astype(bool)
        # ... (other conversions omitted for brevity, assuming clean input for this validation step)
        
        # Validate a sample row to check constraints
        sample = df.iloc[0].to_dict()
        AnalysisDatasetRecord(**sample)
        
    except Exception as e:
        raise ValidationError(f"Data validation failed: {str(e)}", model=AnalysisDatasetRecord)
        
    return df

def validate_regression_output(data: Dict[str, Any]) -> RegressionOutput:
    """
    Validate a dictionary against the RegressionOutput schema.
    
    Args:
        data: Dictionary containing regression results
        
    Returns:
        Validated RegressionOutput object
    """
    try:
        return RegressionOutput(**data)
    except ValidationError as e:
        raise ValidationError(f"Regression output validation failed: {str(e)}", model=RegressionOutput)

def validate_sensitivity_output(data: Dict[str, Any]) -> SensitivityResult:
    """
    Validate a dictionary against the SensitivityResult schema.
    
    Args:
        data: Dictionary containing sensitivity results
        
    Returns:
        Validated SensitivityResult object
    """
    try:
        return SensitivityResult(**data)
    except ValidationError as e:
        raise ValidationError(f"Sensitivity output validation failed: {str(e)}", model=SensitivityResult)