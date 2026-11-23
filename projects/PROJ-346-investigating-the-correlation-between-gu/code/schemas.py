from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Dict, Optional, Any, Union
import json
from pathlib import Path
import yaml

class MicrobialTaxa(BaseModel):
    """Schema for microbial taxa data."""
    model_config = ConfigDict(extra='forbid')
    
    taxon_name: str = Field(..., description="Name of the taxon (e.g., genus, species)")
    relative_abundance: float = Field(..., ge=0.0, le=1.0, description="Relative abundance fraction")
    sample_id: str = Field(..., description="Unique identifier for the sample")

class CognitiveScore(BaseModel):
    """Schema for cognitive score data."""
    model_config = ConfigDict(extra='forbid')
    
    task_type: str = Field(..., description="Type of cognitive task performed")
    z_score: float = Field(..., description="Standardized z-score of the cognitive performance")
    participant_id: str = Field(..., description="Unique identifier for the participant")

def validate_microbial_data(df):
    """Validate a pandas DataFrame against MicrobialTaxa schema."""
    required_cols = ['taxon_name', 'relative_abundance', 'sample_id']
    if not all(col in df.columns for col in required_cols):
        missing = set(required_cols) - set(df.columns)
        raise ValueError(f"Microbial data missing required columns: {missing}")
    
    # Basic type and range checks
    if not all(isinstance(x, str) for x in df['taxon_name']):
        raise ValueError("taxon_name must be string")
    if not all(isinstance(x, str) for x in df['sample_id']):
        raise ValueError("sample_id must be string")
    if not all(0.0 <= x <= 1.0 for x in df['relative_abundance']):
        raise ValueError("relative_abundance must be between 0.0 and 1.0")
    return True

def validate_cognitive_data(df):
    """Validate a pandas DataFrame against CognitiveScore schema."""
    required_cols = ['task_type', 'z_score', 'participant_id']
    if not all(col in df.columns for col in required_cols):
        missing = set(required_cols) - set(df.columns)
        raise ValueError(f"Cognitive data missing required columns: {missing}")
    
    # Basic type and range checks
    if not all(isinstance(x, str) for x in df['task_type']):
        raise ValueError("task_type must be string")
    if not all(isinstance(x, str) for x in df['participant_id']):
        raise ValueError("participant_id must be string")
    # z_score can be any float, but we check it's numeric
    if not pd.api.types.is_numeric_dtype(df['z_score']):
        raise ValueError("z_score must be numeric")
    return True

def export_schema_definitions(output_path: Optional[Union[str, Path]] = None):
    """
    Export schema definitions to a YAML file.
    
    Args:
        output_path: Path to write the YAML file. If None, prints to stdout.
    
    Returns:
        The dictionary representation of the schemas.
    """
    schema_dict = {
        "MicrobialTaxa": {
            "fields": [
                {"name": "taxon_name", "type": "string", "description": "Name of the taxon (e.g., genus, species)"},
                {"name": "relative_abundance", "type": "number", "description": "Relative abundance fraction", "minimum": 0.0, "maximum": 1.0},
                {"name": "sample_id", "type": "string", "description": "Unique identifier for the sample"}
            ]
        },
        "CognitiveScore": {
            "fields": [
                {"name": "task_type", "type": "string", "description": "Type of cognitive task performed"},
                {"name": "z_score", "type": "number", "description": "Standardized z-score of the cognitive performance"},
                {"name": "participant_id", "type": "string", "description": "Unique identifier for the participant"}
            ]
        }
    }
    
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            yaml.dump(schema_dict, f, default_flow_style=False, sort_keys=False)
    
    return schema_dict

# Helper to ensure pandas is imported for type checks if needed elsewhere
import pandas as pd
