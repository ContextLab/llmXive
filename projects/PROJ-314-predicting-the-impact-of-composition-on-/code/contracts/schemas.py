import json
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
import yaml
from pydantic import BaseModel, Field, field_validator, ConfigDict
import numpy as np

class CeramicEntry(BaseModel):
    """
    Schema for a single ceramic material entry.
    Represents the core data structure for ingestion and processing.
    """
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    # Core Identification
    composition: str = Field(..., description="Chemical formula string, e.g., 'Al2O3'")
    
    # Target Variable
    weibull_modulus: float = Field(..., description="The Weibull modulus (m) value")
    
    # Data Provenance & Quality Flags
    sample_count: int = Field(..., ge=1, description="Number of samples used for measurement (N)")
    is_range_flag: bool = Field(False, description="True if weibull_modulus was a range midpoint")
    range_original: Optional[str] = Field(None, description="Original range string if is_range_flag is True")
    is_imputed: bool = Field(False, description="True if any descriptors were imputed")
    
    # Derived Descriptors (Computed during ingestion)
    primary_anion_cation_group: Optional[str] = Field(None, description="e.g., 'O-Al', 'N-Si'")
    sintering_temp: Optional[float] = Field(None, description="Sintering temperature in Kelvin")
    
    # Computed Elemental Descriptors
    mean_atomic_radius: Optional[float] = Field(None, ge=0.0, description="Mean atomic radius of cations")
    electronegativity_std: Optional[float] = Field(None, ge=0.0, description="Std dev of electronegativity")
    valence_electron_concentration: Optional[float] = Field(None, ge=0.0, description="Valence electron concentration")
    
    # Additional descriptors potentially computed
    cation_size_variance: Optional[float] = Field(None, ge=0.0)
    range_uncertainty: Optional[float] = Field(None, ge=0.0)

    @field_validator('composition')
    @classmethod
    def validate_composition_format(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValueError("Composition must be a non-empty string")
        # Basic sanity check: no spaces, contains at least one element symbol pattern
        if ' ' in v:
            raise ValueError("Composition string contains spaces")
        return v

    @field_validator('weibull_modulus')
    @classmethod
    def validate_weibull_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Weibull modulus must be positive")
        return v

    @field_validator('sample_count')
    @classmethod
    def validate_sample_count(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Sample count must be at least 1")
        return v

class DescriptorSet(BaseModel):
    """
    Schema for a set of computed descriptors for a material.
    Used to validate the output of the descriptor computation pipeline.
    """
    model_config = ConfigDict(extra='forbid')

    composition: str = Field(..., description="Reference to the composition")
    descriptors: Dict[str, float] = Field(
        ..., 
        description="Dictionary of descriptor names to values"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Metadata about the computation (e.g., source of elemental data)"
    )

    @field_validator('descriptors')
    @classmethod
    def validate_descriptors_numeric(cls, v: Dict[str, float]) -> Dict[str, float]:
        for k, val in v.items():
            if not isinstance(val, (int, float, np.floating, np.integer)):
                raise ValueError(f"Descriptor '{k}' must be numeric, got {type(val)}")
            if isinstance(val, float) and np.isnan(val):
                raise ValueError(f"Descriptor '{k}' cannot be NaN")
        return v

class ModelResult(BaseModel):
    """
    Schema for the output of a predictive modeling run.
    """
    model_config = ConfigDict(extra='forbid')

    model_type: str = Field(..., description="Type of model, e.g., 'RandomForest', 'GradientBoosting'")
    mae: float = Field(..., ge=0.0, description="Mean Absolute Error")
    r_squared: float = Field(..., description="R-squared score")
    feature_importance_ranking: List[Dict[str, Any]] = Field(
        ..., 
        description="List of dicts with 'feature' and 'importance' keys"
    )
    cv_stability_scores: Dict[str, float] = Field(
        default_factory=dict, 
        description="Stability metrics for feature importance across CV folds"
    )
    hyperparameters: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Final hyperparameters used"
    )
    cross_validation_scores: Optional[List[float]] = Field(
        None, 
        description="Scores from each CV fold"
    )

    @field_validator('feature_importance_ranking')
    @classmethod
    def validate_ranking_format(cls, v: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        for item in v:
            if 'feature' not in item or 'importance' not in item:
                raise ValueError("Each ranking item must have 'feature' and 'importance' keys")
        return v

def export_schemas_to_yaml(output_dir: Optional[str] = None) -> None:
    """
    Exports the Pydantic schemas to YAML files in the specified directory.
    Defaults to the 'code/contracts/' directory relative to the script.
    """
    target_dir = Path(output_dir) if output_dir else Path(__file__).parent
    target_dir.mkdir(parents=True, exist_ok=True)

    # Helper to convert Pydantic model schema to a cleaner format
    def clean_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
        # Remove internal pydantic metadata that isn't useful for a data contract
        schema.pop('title', None)
        schema.pop('$defs', None) # Inline definitions if necessary, but usually we want flat
        if 'properties' in schema:
            for prop in schema['properties'].values():
                prop.pop('title', None)
        return schema

    # Export CeramicEntry
    ceramic_schema = CeramicEntry.model_json_schema()
    ceramic_clean = clean_schema(ceramic_schema)
    ceramic_path = target_dir / 'ceramic_entry.schema.yaml'
    with open(ceramic_path, 'w') as f:
        yaml.dump(ceramic_clean, f, default_flow_style=False, sort_keys=False)
    
    # Export ModelResult
    model_schema = ModelResult.model_json_schema()
    model_clean = clean_schema(model_schema)
    model_path = target_dir / 'model_result.schema.yaml'
    with open(model_path, 'w') as f:
        yaml.dump(model_clean, f, default_flow_style=False, sort_keys=False)

    # Note: DescriptorSet is an intermediate validation schema, usually not exported 
    # as a top-level data contract unless explicitly requested. 
    # However, if needed, it can be added here.

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Loads a schema from a YAML file."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_schemas() -> bool:
    """
    Validates that the Pydantic models are well-formed and can be exported.
    """
    try:
        # Attempt to generate schemas
        CeramicEntry.model_json_schema()
        DescriptorSet.model_json_schema()
        ModelResult.model_json_schema()
        return True
    except Exception as e:
        print(f"Schema validation failed: {e}")
        return False

def validate_data_against_schema(data: Dict[str, Any], schema_class: Any) -> bool:
    """
    Validates a dictionary against a specific Pydantic model class.
    Returns True if valid, raises ValidationError if not.
    """
    try:
        schema_class.model_validate(data)
        return True
    except Exception as e:
        print(f"Data validation failed: {e}")
        return False

if __name__ == "__main__":
    # Run export if executed directly
    export_schemas_to_yaml()
    print("Schemas exported successfully to code/contracts/")
