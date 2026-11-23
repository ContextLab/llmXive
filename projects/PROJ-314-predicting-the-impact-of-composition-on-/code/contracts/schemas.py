import json
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
import yaml
from pydantic import BaseModel, Field, field_validator, ConfigDict
import numpy as np

class CeramicEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    composition: str = Field(..., description="Chemical composition string")
    weibull_modulus: float = Field(..., description="Weibull modulus value")
    sample_count: int = Field(..., ge=30, description="Number of samples (N)")
    is_range_flag: bool = Field(False, description="Flag indicating if value was a range")
    range_original: Optional[str] = Field(None, description="Original range string if applicable")
    primary_anion_cation_group: str = Field(..., description="Derived group identifier")
    sintering_temp: Optional[float] = Field(None, description="Sintering temperature")
    is_imputed: bool = Field(False, description="Flag indicating if sintering temp was imputed")
    mean_atomic_radius: Optional[float] = Field(None, description="Mean atomic radius")
    electronegativity_std: Optional[float] = Field(None, description="Std dev of electronegativity")
    valence_electron_concentration: Optional[float] = Field(None, description="Valence electron concentration")
    
    @field_validator('weibull_modulus')
    @classmethod
    def check_weibull_positive(cls, v):
        if v <= 0:
            raise ValueError('Weibull modulus must be positive')
        return v

class DescriptorSet(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    descriptors: Dict[str, float] = Field(..., description="Dictionary of computed descriptors")
    composition: str = Field(..., description="Original composition")

class ModelResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    model_type: str = Field(..., description="Type of model (e.g., RandomForest)")
    mae: float = Field(..., description="Mean Absolute Error")
    r_squared: float = Field(..., description="R-squared score")
    feature_importance_ranking: List[Dict[str, Any]] = Field(..., description="List of features and importance")
    cv_stability_scores: Dict[str, float] = Field(..., description="CV stability metrics")

def export_schemas_to_yaml(output_dir: Optional[Path] = None):
    """Export Pydantic schemas to YAML files."""
    if output_dir is None:
        output_dir = Path(__file__).parent
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Export CeramicEntry
    ceramic_schema = CeramicEntry.model_json_schema()
    ceramic_yaml_path = output_dir / "ceramic_entry.schema.yaml"
    with open(ceramic_yaml_path, 'w') as f:
        yaml.dump(ceramic_schema, f, default_flow_style=False)
    print(f"Exported CeramicEntry schema to {ceramic_yaml_path}")
    
    # Export ModelResult
    model_schema = ModelResult.model_json_schema()
    model_yaml_path = output_dir / "model_result.schema.yaml"
    with open(model_yaml_path, 'w') as f:
        yaml.dump(model_schema, f, default_flow_style=False)
    print(f"Exported ModelResult schema to {model_yaml_path}")

def load_schema(schema_name: str) -> Dict[str, Any]:
    """Load a schema from a YAML file."""
    schema_path = Path(__file__).parent / f"{schema_name}.schema.yaml"
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_schemas():
    """Validate that schema files exist and are valid."""
    required_files = [
        "ceramic_entry.schema.yaml",
        "model_result.schema.yaml"
    ]
    for file in required_files:
        path = Path(__file__).parent / file
        if not path.exists():
            raise FileNotFoundError(f"Schema file not found: {path}")
    return True

def validate_data_against_schema(data: Dict[str, Any], schema_name: str) -> bool:
    """Validate data against a specific schema."""
    if schema_name == "ceramic_entry":
        CeramicEntry(**data)
        return True
    elif schema_name == "model_result":
        ModelResult(**data)
        return True
    return False

if __name__ == "__main__":
    export_schemas_to_yaml()
    validate_schemas()
    print("Schemas exported and validated successfully.")
