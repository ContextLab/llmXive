"""
Contract tests for the model output schema (ModelOutput).
Validates that the prediction artifacts adhere to the expected schema:
- 'smiles': str
- 'prediction': float
- 'shap_value': float
"""
import pytest
import pandas as pd
from pydantic import BaseModel, field_validator, ValidationError
from typing import List, Dict, Any

# --- Pydantic Model Definition ---

class ModelOutput(BaseModel):
    """
    Pydantic model representing a single model prediction output.
    Enforces:
    - 'smiles' is a string
    - 'prediction' is a float
    - 'shap_value' is a float
    """
    smiles: str
    prediction: float
    shap_value: float

    @field_validator('prediction', 'shap_value', mode='before')
    @classmethod
    def ensure_float(cls, v):
        if v is None:
            raise ValueError('Numeric field cannot be None')
        try:
            return float(v)
        except (TypeError, ValueError):
            raise ValueError(f"Field must be numeric, got {type(v)}")

# --- Test Functions ---

def test_valid_model_output():
    """Test that a valid output row passes validation."""
    data = {
        'smiles': 'CCO',
        'prediction': 1.5,
        'shap_value': 0.25
    }
    row = ModelOutput(**data)
    assert row.smiles == 'CCO'
    assert row.prediction == 1.5
    assert row.shap_value == 0.25

def test_missing_required_field():
    """Test that missing 'smiles' raises ValidationError."""
    data = {
        'prediction': 1.5,
        'shap_value': 0.25
    }
    with pytest.raises(ValidationError):
        ModelOutput(**data)

def test_missing_prediction():
    """Test that missing 'prediction' raises ValidationError."""
    data = {
        'smiles': 'CCO',
        'shap_value': 0.25
    }
    with pytest.raises(ValidationError):
        ModelOutput(**data)

def test_missing_shap_value():
    """Test that missing 'shap_value' raises ValidationError."""
    data = {
        'smiles': 'CCO',
        'prediction': 1.5
    }
    with pytest.raises(ValidationError):
        ModelOutput(**data)

def test_invalid_prediction_type():
    """Test that non-numeric prediction raises ValidationError."""
    data = {
        'smiles': 'CCO',
        'prediction': 'invalid',
        'shap_value': 0.25
    }
    with pytest.raises(ValidationError):
        ModelOutput(**data)

def test_invalid_shap_type():
    """Test that non-numeric shap_value raises ValidationError."""
    data = {
        'smiles': 'CCO',
        'prediction': 1.5,
        'shap_value': 'invalid'
    }
    with pytest.raises(ValidationError):
        ModelOutput(**data)

def test_pandas_dataframe_validation():
    """
    Test validation against a pandas DataFrame row.
    """
    df = pd.DataFrame([{
        'smiles': 'CCO',
        'prediction': 1.5,
        'shap_value': 0.25
    }])

    for _, row_dict in df.iterrows():
        try:
            ModelOutput(**row_dict.to_dict())
        except ValidationError as e:
            pytest.fail(f"Validation failed for valid data: {e}")

    # Validate invalid row
    df_invalid = pd.DataFrame([{
        'smiles': 'CCO',
        'prediction': 'bad',
        'shap_value': 0.25
    }])

    for _, row_dict in df_invalid.iterrows():
        with pytest.raises(ValidationError):
            ModelOutput(**row_dict.to_dict())
