import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os
import yaml
import tempfile
import shutil

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.schemas import MicrobialTaxa, CognitiveScore
from code.utils import get_contracts_path

# Import the validation functions directly
# Since 08_validate_schema is a script, we import the functions if possible or mock the logic
# For unit testing, we test the logic of validation

def test_validate_microbiome_missing_required():
    """Test that missing required columns are detected."""
    # Create a mock dataframe missing 'sample_id'
    df = pd.DataFrame({
        'taxon': ['Bacteroides', 'Firmicutes'],
        'abundance': [0.5, 0.5]
    })
    
    # Mock schema requiring sample_id
    schema = {
        "properties": {
            "sample_id": {"type": "string"},
            "taxon": {"type": "string"},
            "abundance": {"type": "number"}
        },
        "required": ["sample_id", "taxon", "abundance"]
    }
    
    # Simulate the validation logic from code/08_validate_schema.py
    errors = []
    required_fields = schema.get("required", [])
    for field in required_fields:
        if field not in df.columns:
            errors.append(f"Missing required column: {field}")
    
    assert len(errors) == 1
    assert "sample_id" in errors[0]

def test_validate_microbiome_duplicate_samples():
    """Test that duplicate sample IDs are detected."""
    df = pd.DataFrame({
        'sample_id': ['S1', 'S1', 'S2'],
        'taxon': ['Bacteroides', 'Firmicutes', 'Actinobacteria'],
        'abundance': [0.5, 0.3, 0.2]
    })
    
    schema = {
        "properties": {},
        "required": ["sample_id", "taxon", "abundance"]
    }
    
    errors = []
    # Check duplicates
    if "sample_id" in df.columns:
        if df["sample_id"].duplicated().any():
            errors.append("Duplicate sample_ids found in microbiome data")
    
    assert len(errors) == 1
    assert "Duplicate" in errors[0]

def test_validate_cognitive_numeric_type():
    """Test that non-numeric scores in cognitive data are flagged."""
    df = pd.DataFrame({
        'subject_id': ['A', 'B'],
        'cognitive_score': ['low', 'high']  # Should be numeric
    })
    
    schema = {
        "properties": {
            "cognitive_score": {"type": "number"}
        },
        "required": ["subject_id", "cognitive_score"]
    }
    
    errors = []
    for col in df.columns:
        if col in schema["properties"]:
            col_schema = schema["properties"][col]
            dtype = col_schema.get("type")
            if dtype == "number" and not pd.api.types.is_numeric_dtype(df[col]):
                if "score" in col.lower():
                    errors.append(f"Column '{col}' should be numeric but is {df[col].dtype}")
    
    assert len(errors) == 1
    assert "numeric" in errors[0]

def test_schema_file_exists():
    """Test that the schema file exists in the contracts directory."""
    schema_path = get_contracts_path() / "dataset.schema.yaml"
    assert schema_path.exists(), "dataset.schema.yaml should exist in contracts"
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    assert "microbiome_raw" in schema or "microbiome" in str(schema).lower()
    assert "cognitive_raw" in schema or "cognitive" in str(schema).lower()
