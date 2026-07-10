from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
import re
import json
from pathlib import Path

class MicrobialTaxa(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    sample_id: str = Field(..., description="Unique identifier for the sample")
    study_id: Optional[str] = Field(None, description="Source study identifier")
    taxa_path: str = Field(..., description="Taxonomic path (e.g., 'k__Bacteria; p__Firmicutes')")
    abundance: float = Field(..., ge=0.0, description="Relative abundance (0.0 to 1.0)")
    read_count: Optional[int] = Field(None, ge=0, description="Raw read count for the taxon")
    sequencing_depth: Optional[int] = Field(None, ge=0, description="Total sequencing depth for the sample")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

    @field_validator('taxa_path')
    @classmethod
    def validate_taxa_path(cls, v):
        if not v:
            raise ValueError('taxa_path cannot be empty')
        # Basic check for taxonomic rank markers
        if not re.search(r'[kprcofgs]__', v):
            raise ValueError('taxa_path must contain taxonomic rank markers (k__, p__, etc.)')
        return v

    @field_validator('abundance')
    @classmethod
    def validate_abundance(cls, v):
        if v < 0.0 or v > 1.0:
            raise ValueError('abundance must be between 0.0 and 1.0')
        return v

class CognitiveScore(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    subject_id: str = Field(..., description="Unique identifier for the subject")
    study_id: Optional[str] = Field(None, description="Source study identifier")
    score_type: str = Field(..., description="Type of cognitive test (e.g., 'digit_symbol', 'processing_speed')")
    raw_score: float = Field(..., description="Raw score from the cognitive test")
    age: Optional[float] = Field(None, ge=0, description="Age of subject in years")
    sex: Optional[str] = Field(None, description="Sex of subject (M/F)")
    bmi: Optional[float] = Field(None, ge=0, description="Body Mass Index")
    collection_date: Optional[datetime] = Field(None, description="Date of data collection")
    z_score: Optional[float] = Field(None, description="Z-score normalized score")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

    @field_validator('raw_score')
    @classmethod
    def validate_raw_score(cls, v):
        if v < 0:
            raise ValueError('raw_score cannot be negative')
        return v

def validate_microbial_data(data: pd.DataFrame) -> List[str]:
    """
    Validates a pandas DataFrame against the MicrobialTaxa schema.
    Returns a list of error messages.
    """
    errors = []
    required_cols = ['sample_id', 'taxa_path', 'abundance']
    
    # Check columns
    missing_cols = set(required_cols) - set(data.columns)
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
        return errors

    # Validate row by row
    for idx, row in data.iterrows():
        try:
            MicrobialTaxa(
                sample_id=row['sample_id'],
                taxa_path=row['taxa_path'],
                abundance=float(row['abundance']),
                read_count=row.get('read_count'),
                sequencing_depth=row.get('sequencing_depth')
            )
        except Exception as e:
            errors.append(f"Row {idx}: {str(e)}")
    
    return errors

def validate_cognitive_data(data: pd.DataFrame) -> List[str]:
    """
    Validates a pandas DataFrame against the CognitiveScore schema.
    Returns a list of error messages.
    """
    errors = []
    required_cols = ['subject_id', 'score_type', 'raw_score']
    
    # Check columns
    missing_cols = set(required_cols) - set(data.columns)
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
        return errors

    # Validate row by row
    for idx, row in data.iterrows():
        try:
            CognitiveScore(
                subject_id=row['subject_id'],
                score_type=row['score_type'],
                raw_score=float(row['raw_score']),
                age=row.get('age'),
                sex=row.get('sex'),
                bmi=row.get('bmi')
            )
        except Exception as e:
            errors.append(f"Row {idx}: {str(e)}")
    
    return errors

def export_schema_definitions(output_path: str) -> None:
    """
    Exports the Pydantic schema definitions to a YAML file.
    """
    schema = {
        "MicrobialTaxa": {
            "type": "object",
            "properties": {
                "sample_id": {"type": "string", "description": "Unique identifier for the sample"},
                "study_id": {"type": ["string", "null"], "description": "Source study identifier"},
                "taxa_path": {"type": "string", "description": "Taxonomic path (e.g., 'k__Bacteria; p__Firmicutes')"},
                "abundance": {"type": "number", "minimum": 0.0, "maximum": 1.0, "description": "Relative abundance"},
                "read_count": {"type": ["integer", "null"], "minimum": 0, "description": "Raw read count"},
                "sequencing_depth": {"type": ["integer", "null"], "minimum": 0, "description": "Total sequencing depth"},
                "metadata": {"type": "object", "description": "Additional metadata"}
            },
            "required": ["sample_id", "taxa_path", "abundance"]
        },
        "CognitiveScore": {
            "type": "object",
            "properties": {
                "subject_id": {"type": "string", "description": "Unique identifier for the subject"},
                "study_id": {"type": ["string", "null"], "description": "Source study identifier"},
                "score_type": {"type": "string", "description": "Type of cognitive test"},
                "raw_score": {"type": "number", "minimum": 0, "description": "Raw score"},
                "age": {"type": ["number", "null"], "minimum": 0, "description": "Age in years"},
                "sex": {"type": ["string", "null"], "description": "Sex (M/F)"},
                "bmi": {"type": ["number", "null"], "minimum": 0, "description": "Body Mass Index"},
                "collection_date": {"type": ["string", "null"], "format": "date-time", "description": "Collection date"},
                "z_score": {"type": ["number", "null"], "description": "Z-score normalized score"},
                "metadata": {"type": "object", "description": "Additional metadata"}
            },
            "required": ["subject_id", "score_type", "raw_score"]
        }
    }
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(schema, f, indent=2)

import pandas as pd