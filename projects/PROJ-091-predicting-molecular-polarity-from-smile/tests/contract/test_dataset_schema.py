"""
Contract tests for the DescriptorMatrix schema.
Validates dynamic column patterns for descriptor columns.
"""
import pytest
from pydantic import BaseModel, Field, field_validator, ValidationError
from typing import List, Dict, Any, Optional
import re

class DescriptorMatrix(BaseModel):
    """
    Schema for the descriptor matrix.
    - smiles: str
    - target: float
    - Any number of columns starting with 'desc_'
    """
    smiles: str
    target: float
    # Allow arbitrary extra fields, but we will validate them in the validator
    model_config = {"extra": "allow"}

    @field_validator('smiles')
    @classmethod
    def validate_smiles(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError('smiles must be a non-empty string')
        return v

    @field_validator('target')
    @classmethod
    def validate_target(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError('target must be a number')
        return float(v)

    @field_validator('model_fields', mode='before')
    @classmethod
    def validate_extra_fields(cls, values):
        # This validator runs before standard validation to check extra fields
        if isinstance(values, dict):
            for key, value in values.items():
                if key in ['smiles', 'target']:
                    continue
                if not key.startswith('desc_'):
                    raise ValueError(f"Extra column '{key}' must start with 'desc_'")
                if not isinstance(value, (int, float, type(None))):
                    # Allow None for missing values, but ensure numeric otherwise
                    raise ValueError(f"Descriptor column '{key}' must be numeric or None, got {type(value)}")
        return values

    def model_dump(self, exclude_none=True):
        return super().model_dump(exclude_none=exclude_none)

def test_valid_descriptor_matrix():
    """Test that a valid descriptor matrix passes validation."""
    data = {
        "smiles": "CCO",
        "target": 1.5,
        "desc_mol_weight": 46.07,
        "desc_logp": 0.5,
        "desc_num_h_donors": 1
    }
    model = DescriptorMatrix(**data)
    assert model.smiles == "CCO"
    assert model.target == 1.5
    assert model.desc_mol_weight == 46.07

def test_missing_required_fields():
    """Test that missing required fields raise ValidationError."""
    with pytest.raises(ValidationError):
        DescriptorMatrix(smiles="CCO") # missing target

    with pytest.raises(ValidationError):
        DescriptorMatrix(target=1.5) # missing smiles

def test_invalid_smiles_type():
    """Test that non-string smiles raises ValidationError."""
    with pytest.raises(ValidationError):
        DescriptorMatrix(smiles=123, target=1.5)

def test_invalid_extra_column_prefix():
    """Test that extra columns not starting with 'desc_' raise ValidationError."""
    data = {
        "smiles": "CCO",
        "target": 1.5,
        "invalid_column": 100
    }
    with pytest.raises(ValidationError) as exc_info:
        DescriptorMatrix(**data)
    assert "must start with 'desc_'" in str(exc_info.value)

def test_dynamic_descriptor_count():
    """Test that any number of descriptor columns are accepted."""
    data = {
        "smiles": "CCO",
        "target": 1.5
    }
    # Add 100 descriptor columns
    for i in range(100):
        data[f"desc_feature_{i}"] = float(i)

    model = DescriptorMatrix(**data)
    assert model.smiles == "CCO"
    # Verify all extra fields are accessible
    for i in range(100):
        assert getattr(model, f"desc_feature_{i}") == float(i)

def test_non_numeric_descriptor():
    """Test that non-numeric descriptor values raise ValidationError."""
    data = {
        "smiles": "CCO",
        "target": 1.5,
        "desc_bad": "not_a_number"
    }
    with pytest.raises(ValidationError) as exc_info:
        DescriptorMatrix(**data)
    assert "must be numeric" in str(exc_info.value)
