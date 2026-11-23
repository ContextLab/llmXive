"""
Pydantic schemas for the plant biomass prediction pipeline.

These schemas define the data structure for spectral data, biomass labels,
and processed records as specified in the data-model.md.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
import numpy as np


class SpectralBand(BaseModel):
    """Represents a single spectral band measurement."""
    model_config = ConfigDict(extra='forbid')
    
    wavelength_nm: float = Field(..., description="Wavelength in nanometers")
    reflectance: float = Field(..., ge=0.0, le=1.0, description="Reflectance value [0, 1]")
    band_name: Optional[str] = Field(None, description="Optional name for the band")

class RawSpectralRecord(BaseModel):
    """Raw spectral data record from hyperspectral imagery."""
    model_config = ConfigDict(extra='forbid')
    
    site_id: str = Field(..., description="Unique site identifier")
    scene_id: str = Field(..., description="Unique scene identifier")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    bands: List[SpectralBand] = Field(..., min_length=1, description="List of spectral bands")
    cloud_flag: bool = Field(False, description="True if cloud contamination detected")

class ProcessedRecord(BaseModel):
    """Processed record with atmospheric correction and derived features."""
    model_config = ConfigDict(extra='forbid')
    
    record_id: str = Field(..., description="Unique record identifier")
    site_id: str
    scene_id: str
    timestamp: str
    latitude: float
    longitude: float
    corrected_reflectance: Dict[str, float] = Field(
        ..., 
        description="Dictionary of band names to corrected reflectance values"
    )
    structural_features: Optional[Dict[str, float]] = Field(
        None, 
        description="Derived structural features (e.g., NDVI, LAI)"
    )
    cloud_flag: bool
    exclusion_reason: Optional[str] = Field(
        None, 
        description="Reason for exclusion if cloud_flag is True"
    )

class BiomassLabel(BaseModel):
    """Ground-truth biomass measurement."""
    model_config = ConfigDict(extra='forbid')
    
    sample_id: str = Field(..., description="Unique sample identifier")
    site_id: str
    collection_date: str
    dry_mass_g: float = Field(..., gt=0.0, description="Dry biomass in grams")
    wet_mass_g: Optional[float] = Field(None, gt=0.0, description="Optional wet biomass")
    species: Optional[str] = Field(None, description="Plant species name")
    measurement_method: str = Field(..., description="Method used for measurement")

class TrainingSample(BaseModel):
    """Combined training sample with features and label."""
    model_config = ConfigDict(extra='forbid')
    
    sample_id: str
    record_id: str
    site_id: str
    features: Dict[str, float] = Field(..., description="Flattened feature vector")
    target: float = Field(..., description="Target biomass value")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class ModelPrediction(BaseModel):
    """Model prediction output."""
    model_config = ConfigDict(extra='forbid')
    
    sample_id: str
    predicted_biomass_g: float = Field(..., gt=0.0)
    confidence_interval: Optional[tuple[float, float]] = Field(
        None, 
        description="95% confidence interval (lower, upper)"
    )
    model_version: str = Field(..., description="Model version identifier")

# Export all schemas for easy importing
__all__ = [
    "SpectralBand",
    "RawSpectralRecord", 
    "ProcessedRecord",
    "BiomassLabel",
    "TrainingSample",
    "ModelPrediction"
]
