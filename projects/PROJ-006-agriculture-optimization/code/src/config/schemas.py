from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
import os
from pathlib import Path
import pandas as pd
import json

# --- Dataset Schemas ---

class HouseholdRecord(BaseModel):
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
    CSA_Index: float
    Stability_Score: float
    HFIAS: float
    village_id: str

class RemoteSensingPixel(BaseModel):
    pixel_id: str
    latitude: float
    longitude: float
    ndvi: float
    cloud_cover: float
    acquisition_date: datetime

class AnalysisDatasetRecord(BaseModel):
    # This is a simplified version for validation
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
    CSA_Index: float
    Stability_Score: float
    HFIAS: float
    village_id: str

# --- Regression Output Schema ---

class RegressionOutput(BaseModel):
    adjusted_alpha: float
    bonferroni_corrected_p_values: Dict[str, float]
    coefficients: Dict[str, float]
    vif_scores: Dict[str, float]
    model_type: str  # 'aggregated' or 'clustered'
    collinearity_warning: Optional[str] = None

class SensitivityResult(BaseModel):
    threshold: float
    model: str
    coefficient: float
    p_value: float
    std_err: float

# --- Validation Functions ---

def validate_dataset_schema(df: pd.DataFrame) -> bool:
    """
    Validate a pandas DataFrame against the dataset schema.
    Returns True if valid, False otherwise.
    """
    required_columns = [
        "household_id", "latitude", "longitude", "land_size", "education_level",
        "finance_access", "practice_mixed_farming", "practice_terracing",
        "practice_conservation_tillage", "practice_agroforestry", "extension_visits",
        "hlias", "CSA_Index", "Stability_Score", "HFIAS", "village_id"
    ]
    
    if not all(col in df.columns for col in required_columns):
        missing = [col for col in required_columns if col not in df.columns]
        raise ValueError(f"Missing required columns: {missing}")
    
    # Check for nulls in critical columns
    critical_columns = ["CSA_Index", "Stability_Score", "HFIAS", "household_id"]
    for col in critical_columns:
        if df[col].isnull().any():
            logger = logging.getLogger(__name__)
            logger.warning(f"Column {col} contains null values.")
            # Depending on strictness, we might return False here
            # For now, we allow it but log a warning
    
    return True

def validate_regression_output(data: Dict[str, Any]) -> bool:
    """
    Validate a dictionary against the regression output schema.
    """
    required_keys = ["adjusted_alpha", "bonferroni_corrected_p_values", "coefficients", "vif_scores", "model_type"]
    if not all(key in data for key in required_keys):
        missing = [key for key in required_keys if key not in data]
        raise ValueError(f"Missing required keys: {missing}")
    
    if data["model_type"] not in ["aggregated", "clustered"]:
        raise ValueError(f"Invalid model_type: {data['model_type']}")
    
    return True
