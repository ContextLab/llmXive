import pytest
import pandas as pd
import yaml
import os
from pathlib import Path
from pydantic import BaseModel, ValidationError
from typing import Dict, Any, List

# Add src to path for imports if needed, though this is a contract test
# relying on file validation

class ParticipantModel(BaseModel):
    participant_id: str
    age: int
    sex: str
    bmi: float

class LifestyleModel(BaseModel):
    fiber_intake: float
    antibiotics_use: bool

class MicrobiomeModel(BaseModel):
    shannon_diversity: float
    simpson_diversity: float
    chao1: float

class CognitiveModel(BaseModel):
    cognitive_score: float

class FilteredCohortModel(ParticipantModel, LifestyleModel, MicrobiomeModel, CognitiveModel):
    class Config:
        extra = "forbid"

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load YAML schema definition."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_row_against_schema(row: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate a single row dictionary against the filtered_cohort schema.
    This function performs type checking and constraint validation.
    """
    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})
    
    # Check required fields
    for field in required_fields:
        if field not in row:
            raise ValueError(f"Missing required field: {field}")
    
    # Check types and constraints
    for field, value in row.items():
        if field not in properties:
            # Allow extra fields if not strictly forbidden by schema logic, 
            # but typically we want strict adherence for contract tests
            continue 
        
        field_spec = properties[field]
        field_type = field_spec.get('type')
        
        if field_type == 'string':
            if not isinstance(value, str):
                raise TypeError(f"Field {field} must be string, got {type(value)}")
            if 'enum' in field_spec and value not in field_spec['enum']:
                raise ValueError(f"Field {field} value '{value}' not in allowed values {field_spec['enum']}")
        elif field_type == 'integer':
            if not isinstance(value, int):
                raise TypeError(f"Field {field} must be integer, got {type(value)}")
            if 'minimum' in field_spec and value < field_spec['minimum']:
                raise ValueError(f"Field {field} value {value} is below minimum {field_spec['minimum']}")
        elif field_type == 'number':
            if not isinstance(value, (int, float)):
                raise TypeError(f"Field {field} must be number, got {type(value)}")
            if 'minimum' in field_spec and value < field_spec['minimum']:
                raise ValueError(f"Field {field} value {value} is below minimum {field_spec['minimum']}")
        elif field_type == 'boolean':
            if not isinstance(value, bool):
                raise TypeError(f"Field {field} must be boolean, got {type(value)}")
    
    return True

@pytest.fixture
def schema_path():
    """Path to the dataset schema."""
    return Path("contracts/dataset.schema.yaml")

@pytest.fixture
def filtered_cohort_path():
    """Path to the filtered cohort CSV."""
    return Path("data/processed/filtered_cohort.csv")

def test_schema_exists(schema_path):
    """Test that the schema file exists."""
    assert schema_path.exists(), f"Schema file not found at {schema_path}"

def test_cohort_exists(filtered_cohort_path):
    """Test that the filtered cohort file exists."""
    assert filtered_cohort_path.exists(), f"Filtered cohort file not found at {filtered_cohort_path}"

def test_cohort_validates_against_schema(filtered_cohort_path, schema_path):
    """
    Contract test: Validates that data/processed/filtered_cohort.csv
    conforms to the structure and constraints defined in contracts/dataset.schema.yaml.
    """
    if not filtered_cohort_path.exists():
        pytest.skip("Filtered cohort file does not exist yet. Run ingestion and filtering first.")
    
    # Load schema
    schema = load_schema(schema_path)
    cohort_schema = schema.get('filtered_cohort', {})
    
    # Load data
    df = pd.read_csv(filtered_cohort_path)
    
    assert df.shape[0] > 0, "Filtered cohort is empty."
    
    errors = []
    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        try:
            validate_row_against_schema(row_dict, cohort_schema)
        except (ValueError, TypeError) as e:
            errors.append(f"Row {idx}: {str(e)}")
    
    if errors:
        error_msg = "Schema validation failed for the following rows:\n" + "\n".join(errors[:10])
        if len(errors) > 10:
            error_msg += f"\n... and {len(errors) - 10} more."
        pytest.fail(error_msg)
    
    # Additional specific checks based on task requirements (US1: age >= 65)
    if 'age' in df.columns:
        assert (df['age'] >= 65).all(), "All participants must be age 65 or older."
    
    # Check for nulls in critical columns defined in schema as required
    required_cols = cohort_schema.get('required', [])
    for col in required_cols:
        if col in df.columns:
            assert not df[col].isnull().any(), f"Column '{col}' contains null values, which violates the schema."
