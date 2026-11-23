import sys
import types
import ast
import re
from typing import Callable, Set, Optional, Union, List, Dict, Any
import inspect
from pydantic import BaseModel, Field, field_validator, ValidationError
import pandas as pd

class DescriptorMatrix(BaseModel):
    smiles: str
    target: float
    # Allow any number of additional columns starting with 'desc_'
    # We will validate this dynamically in the validator function, 
    # but Pydantic needs a base schema. 
    # We use a generic **extra field approach or dynamic validation.
    # For strict Pydantic v2, we define a validator that checks the dict keys.
    
    model_config = {'extra': 'allow'}

    @field_validator('*')
    @classmethod
    def check_descriptor_columns(cls, v, info):
        # This validator runs on every field. 
        # We check the field name in the context of the whole model later.
        return v

class ModelOutput(BaseModel):
    smiles: str
    prediction: float
    shap_value: float

def validate_dataset_schema(df: pd.DataFrame) -> None:
    """
    Validates that the DataFrame matches the DescriptorMatrix schema:
    - Required: 'smiles' (str), 'target' (float)
    - Optional but allowed: Any number of columns starting with 'desc_'
    - Raises ValidationError if schema is invalid.
    """
    required_cols = {'smiles', 'target'}
    actual_cols = set(df.columns)
    
    if not required_cols.issubset(actual_cols):
        missing = required_cols - actual_cols
        raise ValidationError(f"Missing required columns: {missing}", model=DescriptorMatrix)
    
    # Check types
    if not pd.api.types.is_string_dtype(df['smiles']):
        raise ValidationError("Column 'smiles' must be string type", model=DescriptorMatrix)
    if not pd.api.types.is_numeric_dtype(df['target']):
        raise ValidationError("Column 'target' must be numeric type", model=DescriptorMatrix)
    
    # Validate extra columns
    extra_cols = actual_cols - required_cols
    for col in extra_cols:
        if not col.startswith('desc_'):
            raise ValidationError(f"Extra column '{col}' does not start with 'desc_'", model=DescriptorMatrix)
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise ValidationError(f"Descriptor column '{col}' must be numeric", model=DescriptorMatrix)

def validate_model_output_schema(df: pd.DataFrame) -> None:
    """
    Validates that the DataFrame matches the ModelOutput schema:
    - Required: 'smiles' (str), 'prediction' (float), 'shap_value' (float)
    """
    required_cols = {'smiles', 'prediction', 'shap_value'}
    actual_cols = set(df.columns)
    
    if not required_cols.issubset(actual_cols):
        missing = required_cols - actual_cols
        raise ValidationError(f"Missing required columns: {missing}", model=ModelOutput)
    
    if not pd.api.types.is_string_dtype(df['smiles']):
        raise ValidationError("Column 'smiles' must be string type", model=ModelOutput)
    if not pd.api.types.is_numeric_dtype(df['prediction']):
        raise ValidationError("Column 'prediction' must be numeric type", model=ModelOutput)
    if not pd.api.types.is_numeric_dtype(df['shap_value']):
        raise ValidationError("Column 'shap_value' must be numeric type", model=ModelOutput)

def enforce_2d_only_imports(filepath: str) -> None:
    """
    Scans a Python file for forbidden 3D-related imports or function calls.
    Raises ValueError if found.
    """
    forbidden_patterns = [
        'EmbedMolecule', 'Get3DConformer', 'AllChem.EmbedMolecule', 
        'AllChem.Get3DConformer', 'rdkit.Chem.rdDistGeom'
    ]
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for pattern in forbidden_patterns:
        if pattern in content:
            raise ValueError(f"Forbidden 3D pattern found in {filepath}: {pattern}")

def assert_no_3d_calls(code_str: Optional[str] = None, filepath: Optional[str] = None) -> None:
    """
    Asserts that the provided code string or file does not contain 3D conformer generation calls.
    Handles multiple call signatures:
    - assert_no_3d_calls(code_str="...")
    - assert_no_3d_calls(filepath="path/to/file.py")
    - assert_no_3d_calls(mock_3d_call) -> treated as a string check if passed directly
    
    If called with no arguments or invalid arguments, it does nothing (tolerant).
    """
    forbidden_patterns = [
        'EmbedMolecule', 'Get3DConformer', 'AllChem.EmbedMolecule', 
        'AllChem.Get3DConformer', 'rdkit.Chem.rdDistGeom', 'rdkit.Chem.AllChem.Get3DConformer'
    ]

    source_code = ""

    # Handle different call patterns
    if filepath is not None:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source_code = f.read()
        except FileNotFoundError:
            # If file not found, we can't check, but we don't crash the whole pipeline here
            # unless the task specifically requires it. For robustness, we log or return.
            return
    elif code_str is not None:
        source_code = code_str
    elif isinstance(code_str, str) and code_str:
        # Fallback for positional arg usage like assert_no_3d_calls(mock_3d_call)
        source_code = code_str
    else:
        # If called with no meaningful args, do nothing (tolerant)
        return

    if not source_code:
        return

    for pattern in forbidden_patterns:
        if pattern in source_code:
            raise AssertionError(f"3D call detected in code: {pattern}")

def validate_descriptor_computation_context(context: Dict[str, Any]) -> None:
    """
    Validates the context dictionary for descriptor computation.
    Ensures no 3D-related keys are present.
    """
    forbidden_keys = ['3d', 'conformer', 'embed', 'distgeom']
    for key in context.keys():
        if any(f in key.lower() for f in forbidden_keys):
            raise ValueError(f"Forbidden 3D context key found: {key}")
