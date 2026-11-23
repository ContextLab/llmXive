import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import yaml
import pandas as pd

from code.utils.logger import get_logger
from code.utils.config import get_data_path

logger = get_logger(__name__)

def load_schema(schema_path: Optional[str] = None) -> Dict[str, Any]:
    """Load the dataset schema from YAML."""
    if schema_path is None:
        schema_path = Path(get_data_path()) / "schema.yaml"
    
    if not os.path.exists(schema_path):
        logger.warning(f"Schema file not found at {schema_path}. Returning empty schema.")
        return {}
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_smiles(smiles: str) -> bool:
    """Basic validation of SMILES string."""
    if not smiles or not isinstance(smiles, str):
        return False
    # Simple regex for SMILES (not exhaustive but catches common errors)
    pattern = r'^[CNOcSsFClBrIPnHn\d\(\)\[\]=#@$%^&*]+$'
    return bool(re.match(pattern, smiles))

def validate_column_types(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """Check that columns have expected types based on schema."""
    errors = []
    expected_types = schema.get('columns', {})
    
    for col, spec in expected_types.items():
        if col not in df.columns:
            continue # Handled by required check
        
        expected_type = spec.get('type')
        if expected_type == 'string' and not df[col].apply(lambda x: isinstance(x, str) or pd.isna(x)).all():
            errors.append(f"Column {col} should be string")
        elif expected_type == 'number' and not df[col].apply(lambda x: isinstance(x, (int, float)) or pd.isna(x)).all():
            errors.append(f"Column {col} should be number")
    
    return errors

def validate_required_columns(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """Check that all required columns are present."""
    errors = []
    required = schema.get('required_columns', [])
    missing = [col for col in required if col not in df.columns]
    if missing:
        errors.append(f"Missing required columns: {missing}")
    return errors

def validate_constraints(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """Check value constraints (e.g., range, unique)."""
    errors = []
    constraints = schema.get('constraints', {})
    
    for col, constraint in constraints.items():
        if col not in df.columns:
            continue
        
        if 'min' in constraint:
            min_val = constraint['min']
            if df[col].min() < min_val:
                errors.append(f"Column {col} has values below {min_val}")
        
        if 'unique' in constraint and constraint['unique']:
            if df[col].duplicated().any():
                errors.append(f"Column {col} should be unique")
    
    return errors

def validate_dataset(df: pd.DataFrame, schema_path: str) -> Tuple[bool, List[str]]:
    """
    Validate a DataFrame against a schema.
    Returns (is_valid, list_of_errors).
    """
    schema = load_schema(schema_path)
    if not schema:
        return True, [] # No schema, no validation
    
    errors = []
    errors.extend(validate_required_columns(df, schema))
    errors.extend(validate_column_types(df, schema))
    errors.extend(validate_constraints(df, schema))
    
    return len(errors) == 0, errors

def validate_dataframe_for_host_filtering(df: pd.DataFrame) -> Tuple[bool, str]:
    """Specific validation for the host filtering step."""
    if 'host_id' not in df.columns:
        return False, "Missing host_id column"
    if 'halide' not in df.columns:
        return False, "Missing halide column"
    return True, "OK"

def ensure_schema_file_exists():
    """Create a default schema file if it doesn't exist."""
    schema_path = Path(get_data_path()) / "schema.yaml"
    if not schema_path.exists():
        schema_path.parent.mkdir(parents=True, exist_ok=True)
        default_schema = {
            "required_columns": ["host_id", "halide", "logK_std", "smiles"],
            "columns": {
                "host_id": {"type": "string"},
                "halide": {"type": "string"},
                "logK_std": {"type": "number"},
                "smiles": {"type": "string"}
            },
            "constraints": {
                "host_id": {"unique": False}
            }
        }
        with open(schema_path, 'w') as f:
            yaml.dump(default_schema, f)
        logger.info(f"Created default schema at {schema_path}")