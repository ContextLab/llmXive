"""
Pydantic Schemas for Data Validation.
Defines CeramicEntry, DescriptorSet, and ModelResult schemas.
"""
import json
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
import yaml
from pydantic import BaseModel, Field, field_validator, ConfigDict
import numpy as np

class CeramicEntry(BaseModel):
    """Schema for a single ceramic entry."""
    composition: str
    weibull_modulus: float
    sample_count: int
    is_range_flag: bool = False
    range_original: Optional[str] = None
    primary_anion_cation_group: str
    sintering_temp: Optional[float] = None
    is_imputed: bool = False
    mean_atomic_radius: Optional[float] = None
    electronegativity_std: Optional[float] = None
    valence_electron_concentration: Optional[float] = None
    cation_size_variance: Optional[float] = None
    range_uncertainty: Optional[float] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

class DescriptorSet(BaseModel):
    """Schema for a set of descriptors."""
    descriptors: List[str]
    values: Dict[str, float]
    source: str

class ModelResult(BaseModel):
    """Schema for model training results."""
    model_type: str
    mae: float
    r_squared: float
    feature_importance_ranking: List[Dict[str, Any]]
    cv_stability_scores: Dict[str, float]

def export_schemas_to_yaml(output_dir: str = "code/contracts"):
    """Export schemas to YAML files."""
    Path(output_dir).mkdir(exist_ok=True)
    
    # Export CeramicEntry
    schema_entry = CeramicEntry.model_json_schema()
    with open(f"{output_dir}/ceramic_entry.schema.yaml", "w") as f:
        yaml.dump(schema_entry, f, default_flow_style=False)
    
    # Export ModelResult
    schema_result = ModelResult.model_json_schema()
    with open(f"{output_dir}/model_result.schema.yaml", "w") as f:
        yaml.dump(schema_result, f, default_flow_style=False)
    
    print(f"Schemas exported to {output_dir}")

def load_schema(schema_name: str) -> Dict[str, Any]:
    """Load a schema from YAML."""
    path = Path(f"code/contracts/{schema_name}.yaml")
    with open(path) as f:
        return yaml.safe_load(f)

def validate_schemas():
    """Validate that schemas are correctly formatted."""
    try:
        load_schema("ceramic_entry")
        load_schema("model_result")
        return True
    except Exception as e:
        print(f"Schema validation failed: {e}")
        return False

def validate_data_against_schema(data: Dict[str, Any], schema_name: str) -> bool:
    """Validate data against a schema."""
    try:
        if schema_name == "ceramic_entry":
            CeramicEntry(**data)
        elif schema_name == "model_result":
            ModelResult(**data)
        return True
    except Exception as e:
        print(f"Validation failed: {e}")
        return False

if __name__ == "__main__":
    export_schemas_to_yaml()
