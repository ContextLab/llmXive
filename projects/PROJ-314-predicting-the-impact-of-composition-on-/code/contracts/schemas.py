from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import json
import yaml
import os

class CeramicEntry(BaseModel):
    """Schema for a single ceramic data entry."""
    composition: str = Field(..., description="Chemical composition string, e.g., 'Al2O3'")
    weibull_modulus: float = Field(..., description="Weibull modulus value")
    sample_count: int = Field(..., ge=1, description="Number of samples used")
    is_range_flag: bool = Field(False, description="Flag if the value was a range")
    range_original: Optional[str] = Field(None, description="Original range string if applicable")
    primary_anion_cation_group: str = Field(..., description="Primary anion-cation group identifier")
    sintering_temp: Optional[float] = Field(None, description="Sintering temperature in Celsius")
    is_imputed: bool = Field(False, description="Flag if any values were imputed")
    mean_atomic_radius: Optional[float] = Field(None, description="Mean atomic radius of elements")
    electronegativity_std: Optional[float] = Field(None, description="Standard deviation of electronegativity")
    valence_electron_concentration: Optional[float] = Field(None, description="Valence electron concentration")

class DescriptorSet(BaseModel):
    """Schema for a set of computed descriptors."""
    composition: str = Field(..., description="Chemical composition string")
    descriptors: Dict[str, float] = Field(..., description="Dictionary of computed descriptor values")
    computed_at: datetime = Field(default_factory=datetime.now, description="Timestamp of computation")

class ModelResult(BaseModel):
    """Schema for model evaluation results."""
    model_type: str = Field(..., description="Type of model used, e.g., 'RandomForest'")
    mae: float = Field(..., description="Mean Absolute Error")
    r_squared: float = Field(..., description="R-squared value")
    feature_importance_ranking: List[str] = Field(..., description="List of feature names ranked by importance")
    cv_stability_scores: Dict[str, List[float]] = Field(..., description="Stability scores across CV folds")

def export_schemas_to_yaml():
    """Export Pydantic schemas to YAML files."""
    schemas = [
        ("ceramic_entry.schema.yaml", CeramicEntry),
        ("descriptor_set.schema.yaml", DescriptorSet),
        ("model_result.schema.yaml", ModelResult)
    ]
    
    output_dir = Path(__file__).parent
    
    for filename, schema_obj in schemas:
        schema_dict = schema_obj.model_json_schema()
        output_path = output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(schema_dict, f, default_flow_style=False, sort_keys=False)
        
        print(f"Exported {filename}")

from pathlib import Path