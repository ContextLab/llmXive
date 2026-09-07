"""
Internal contract definitions for the Agriculture Optimization pipeline.

Defines Pydantic models for strict validation of dataset records,
remote sensing pixels, regression outputs, and sensitivity analysis results.
"""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
import os
from pathlib import Path
import pandas as pd
import json
import yaml

# --- Core Data Models ---

class HouseholdRecord(BaseModel):
    """Schema for raw survey data ingestion."""
    household_id: int = Field(..., description="Unique identifier for the household")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude of household")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude of household")
    land_size: float = Field(..., gt=0, description="Land size in hectares")
    education_level: int = Field(..., ge=0, description="Years of education of head of household")
    finance_access: bool = Field(..., description="Boolean: access to financial services")
    practice_mixed_farming: bool = Field(default=False, description="Adoption of mixed farming")
    practice_terracing: bool = Field(default=False, description="Adoption of terracing")
    practice_conservation_tillage: bool = Field(default=False, description="Adoption of conservation tillage")
    practice_agroforestry: bool = Field(default=False, description="Adoption of agroforestry")
    extension_visits: int = Field(default=0, ge=0, description="Number of extension visits in last year")
    hlias: int = Field(default=0, ge=0, description="Hunger and Food Insecurity Access Scale score")
    village_id: Optional[str] = Field(None, description="Derived village cluster ID")

    @field_validator('latitude')
    @classmethod
    def validate_lat(cls, v):
        if not (-90 <= v <= 90):
            raise ValueError('Latitude must be between -90 and 90')
        return v

    @field_validator('longitude')
    @classmethod
    def validate_lon(cls, v):
        if not (-180 <= v <= 180):
            raise ValueError('Longitude must be between -180 and 180')
        return v


class RemoteSensingPixel(BaseModel):
    """Schema for a single remote sensing observation (pixel)."""
    pixel_id: str = Field(..., description="Unique pixel identifier")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    timestamp: datetime = Field(..., description="Acquisition timestamp")
    ndvi: Optional[float] = Field(None, ge=-1.0, le=1.0, description="Normalized Difference Vegetation Index")
    cloud_cover: float = Field(..., ge=0.0, le=1.0, description="Cloud cover fraction")
    source: str = Field(..., description="Source satellite (e.g., Sentinel-2)")

    @field_validator('ndvi')
    @classmethod
    def validate_ndvi(cls, v):
        if v is not None and not (-1.0 <= v <= 1.0):
            raise ValueError('NDVI must be between -1.0 and 1.0')
        return v


class AnalysisDatasetRecord(BaseModel):
    """Schema for the final analysis-ready dataset (merged survey + remote sensing)."""
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
    village_id: str
    CSA_Index: float = Field(..., ge=0.0, description="Composite CSA practice index")
    Stability_Score: float = Field(..., gt=0.0, description="Yield stability score (1/CV)")
    mean_ndvi: Optional[float] = Field(None, description="Mean NDVI over growing season")
    ndvi_cv: Optional[float] = Field(None, description="Coefficient of variation of NDVI")

    @model_validator(mode='after')
    def check_derived_fields(self):
        if self.CSA_Index < 0:
            raise ValueError("CSA_Index cannot be negative")
        if self.Stability_Score <= 0:
            raise ValueError("Stability_Score must be positive")
        return self


class RegressionOutput(BaseModel):
    """Schema for regression analysis results."""
    model_name: str
    dependent_variable: str
    independent_variables: List[str]
    coefficients: Dict[str, float]
    p_values: Dict[str, float]
    std_errors: Dict[str, float]
    r_squared: float
    adjusted_r_squared: float
    vif_scores: Dict[str, float]
    model_type: str = Field(..., description="e.g., 'clustered', 'aggregated', 'ols'")
    bonferroni_adjusted_alpha: float
    warnings: List[str] = Field(default_factory=list)

    @field_validator('coefficients', 'p_values', 'std_errors', 'vif_scores')
    @classmethod
    def check_dicts_not_empty(cls, v):
        if not v:
            raise ValueError("Dictionary cannot be empty")
        return v


class SensitivityResult(BaseModel):
    """Schema for sensitivity analysis results."""
    threshold: float
    model: str
    coefficient: float
    p_value: float
    std_err: float

    @field_validator('threshold', 'coefficient', 'p_value', 'std_err')
    @classmethod
    def check_numeric(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError("Must be numeric")
        return v


# --- Validation Helpers ---

def validate_dataset_schema(df: pd.DataFrame) -> bool:
    """
    Validates a pandas DataFrame against the AnalysisDatasetRecord schema.
    
    Args:
        df: DataFrame to validate.
        
    Returns:
        True if valid, raises ValueError otherwise.
    """
    required_columns = [
        'household_id', 'latitude', 'longitude', 'land_size', 
        'education_level', 'finance_access', 'practice_mixed_farming',
        'practice_terracing', 'practice_conservation_tillage', 
        'practice_agroforestry', 'extension_visits', 'hlias', 
        'village_id', 'CSA_Index', 'Stability_Score'
    ]
    
    missing = set(required_columns) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
        
    # Basic type and value checks
    if df['CSA_Index'].min() < 0:
        raise ValueError("CSA_Index contains negative values")
    if (df['Stability_Score'] <= 0).any():
        raise ValueError("Stability_Score contains non-positive values")
        
    return True


def validate_regression_output(data: Dict[str, Any]) -> bool:
    """
    Validates a dictionary against the RegressionOutput schema.
    
    Args:
        data: Dictionary of regression results.
        
    Returns:
        True if valid, raises ValueError otherwise.
    """
    try:
        RegressionOutput(**data)
        return True
    except Exception as e:
        raise ValueError(f"Regression output validation failed: {e}")


def load_schema_from_yaml(path: str) -> Dict[str, Any]:
    """
    Loads a schema definition from a YAML file.
    
    Args:
        path: Path to the YAML file.
        
    Returns:
        Dictionary representation of the schema.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Schema file not found: {path}")
    with open(path, 'r') as f:
        return yaml.safe_load(f)