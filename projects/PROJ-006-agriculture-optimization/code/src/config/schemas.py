"""
Internal contract definitions for the llmXive agriculture optimization pipeline.

This module defines Pydantic models used for validating data structures
during ingestion, processing, and analysis. These schemas enforce the
data contracts specified in the project design documents.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import os
from pathlib import Path

# Constants for validation thresholds (referenced from constants.py if needed,
# but defined here for self-contained schema validation)
MIN_SAMPLE_SIZE = 300
VALID_COUNTRIES = {"Malawi", "Tanzania"}
VALID_GROWING_SEASONS = {
    "Malawi": ["March-May"],
    "Tanzania": ["March-May", "Nov-Dec"]
}


class HouseholdRecord(BaseModel):
    """Schema for a single household record from LSMS-ISA survey data."""
    household_id: str = Field(..., description="Unique identifier for the household")
    country: str = Field(..., description="Country name (Malawi or Tanzania)")
    region: str = Field(..., description="Administrative region")
    village_id: str = Field(..., description="Village identifier for aggregation")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    survey_year: int = Field(..., ge=2000, le=2030, description="Year of survey")
    plot_area_ha: float = Field(..., ge=0.0, description="Total plot area in hectares")
    crop_types: List[str] = Field(default_factory=list, description="List of crops grown")
    csa_practices: List[str] = Field(default_factory=list, description="List of adopted CSA practices")
    extension_frequency: int = Field(default=0, ge=0, description="Frequency of extension visits")
    hfias_score: Optional[float] = Field(None, ge=0.0, description="Household Food Insecurity Access Scale score")
    yield_stability_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Calculated yield stability score")
    csa_index: Optional[float] = Field(None, ge=0.0, le=1.0, description="Calculated CSA adoption index")

    @field_validator('country')
    @classmethod
    def validate_country(cls, v: str) -> str:
        if v not in VALID_COUNTRIES:
            raise ValueError(f"Country must be one of {VALID_COUNTRIES}, got '{v}'")
        return v

    @field_validator('crops')
    @classmethod
    def validate_crops(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("crop_types cannot be empty")
        return v


class RemoteSensingPixel(BaseModel):
    """Schema for a single remote sensing pixel record."""
    pixel_id: str = Field(..., description="Unique pixel identifier")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    acquisition_date: datetime = Field(..., description="Satellite acquisition date")
    ndvi: float = Field(..., ge=-1.0, le=1.0, description="Normalized Difference Vegetation Index")
    cloud_cover: float = Field(..., ge=0.0, le=100.0, description="Cloud cover percentage")
    band_b02: float = Field(..., description="Blue band reflectance")
    band_b03: float = Field(..., description="Green band reflectance")
    band_b04: float = Field(..., description="Red band reflectance")
    band_b08: float = Field(..., description="NIR band reflectance")

    @field_validator('cloud_cover')
    @classmethod
    def validate_cloud_cover(cls, v: float) -> float:
        if v > 80.0:  # Hard threshold for unusable data
            raise ValueError(f"Cloud cover {v}% exceeds maximum threshold of 80%")
        return v


class AnalysisDatasetRecord(BaseModel):
    """Schema for the final analysis-ready dataset record."""
    household_id: str
    country: str
    village_id: str
    survey_year: int
    csa_index: float = Field(..., ge=0.0, le=1.0)
    stability_score: float = Field(..., ge=0.0, le=1.0)
    hfias: float = Field(..., ge=0.0)
    mean_ndvi: float = Field(..., ge=-1.0, le=1.0)
    ndvi_cv: float = Field(..., ge=0.0)
    cloud_cover_mean: float = Field(..., ge=0.0, le=100.0)
    plot_area_ha: float
    extension_frequency: int
    sample_size: int = Field(..., ge=1)
    aggregation_level: str = Field(..., pattern="^(household|village)$")

    @field_validator('aggregation_level')
    @classmethod
    def validate_agg_level(cls, v: str) -> str:
        if v not in {"household", "village"}:
            raise ValueError(f"aggregation_level must be 'household' or 'village', got '{v}'")
        return v


class RegressionOutput(BaseModel):
    """Schema for regression model output."""
    model_name: str
    dependent_variable: str
    independent_variables: List[str]
    coefficients: Dict[str, float]
    p_values: Dict[str, float]
    std_errors: Dict[str, float]
    r_squared: float
    adj_r_squared: float
    n_observations: int
    vif_scores: Dict[str, float]
    bonferroni_adjusted: bool
    bonferroni_threshold: float
    robust_se: bool
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class SensitivityResult(BaseModel):
    """Schema for sensitivity analysis results."""
    threshold_value: float
    coefficient_csa_index: float
    p_value_csa_index: float
    r_squared: float
    n_observations: int
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# Validation utilities
def validate_dataset_schema(df: Any) -> bool:
    """
    Validate a pandas DataFrame against the AnalysisDatasetRecord schema.
    
    Args:
        df: pandas DataFrame to validate
        
    Returns:
        True if valid, raises ValueError if invalid
    """
    try:
        # Convert DataFrame to list of dicts for validation
        records = df.to_dict(orient='records')
        for i, record in enumerate(records):
            AnalysisDatasetRecord(**record)
        return True
    except Exception as e:
        raise ValueError(f"Dataset validation failed at record {i}: {str(e)}")


def validate_regression_output(output: Dict[str, Any]) -> bool:
    """Validate regression output dictionary."""
    RegressionOutput(**output)
    return True