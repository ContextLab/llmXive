import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import yaml
import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_smiles(smiles: str) -> bool:
    """Basic SMILES validation."""
    if not smiles or not isinstance(smiles, str):
        return False
    # Very basic check for balanced brackets and common characters
    if smiles.count('(') != smiles.count(')'):
        return False
    return True

def validate_column_types(df: pd.DataFrame, schema: Dict[str, Any]) -> bool:
    """Validate column types against schema definitions."""
    columns = schema.get('columns', {})
    for col_name, col_def in columns.items():
        if col_name in df.columns:
            expected_type = col_def.get('type')
            if expected_type == 'string' and not df[col_name].apply(lambda x: isinstance(x, str)).all():
                logger.warning(f"Column {col_name} should be string")
                return False
            elif expected_type == 'float' and not pd.api.types.is_float_dtype(df[col_name]):
                # Allow int to be cast to float
                if not pd.api.types.is_numeric_dtype(df[col_name]):
                    logger.warning(f"Column {col_name} should be numeric")
                    return False
    return True

def validate_required_columns(df: pd.DataFrame, schema: Dict[str, Any]) -> bool:
    """Ensure all required columns are present."""
    required = schema.get('required_columns', [])
    missing = [col for col in required if col not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return False
    return True

def validate_constraints(df: pd.DataFrame, schema: Dict[str, Any]) -> bool:
    """Validate specific constraints (e.g., value ranges)."""
    constraints = schema.get('constraints', {})
    for col_name, constraint in constraints.items():
        if col_name in df.columns:
            if 'min' in constraint and (df[col_name] < constraint['min']).any():
                logger.warning(f"Column {col_name} has values below min {constraint['min']}")
                return False
            if 'max' in constraint and (df[col_name] > constraint['max']).any():
                logger.warning(f"Column {col_name} has values above max {constraint['max']}")
                return False
    return True

def validate_dataset(df: pd.DataFrame, schema_path: Path) -> bool:
    """Main validation function."""
    try:
        schema = load_schema(schema_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        return False

    if not validate_required_columns(df, schema):
        return False
    
    if not validate_column_types(df, schema):
        return False
        
    if not validate_constraints(df, schema):
        return False
    
    logger.info("Dataset validation passed.")
    return True

def validate_dataframe_for_host_filtering(df: pd.DataFrame, min_halides: int = 3) -> bool:
    """Check if dataframe has enough halide diversity per host."""
    if df.empty:
        return False
    host_counts = df.groupby('host_id')['halide_identity'].nunique()
    return (host_counts >= min_halides).any()

def ensure_schema_file_exists(schema_path: Path) -> bool:
    """Create a default schema file if it doesn't exist."""
    if schema_path.exists():
        return True
    
    default_schema = {
        "required_columns": ["host_id", "smiles", "halide_identity", "solvent", "log_k"],
        "columns": {
            "host_id": {"type": "string"},
            "smiles": {"type": "string"},
            "halide_identity": {"type": "string"},
            "solvent": {"type": "string"},
            "log_k": {"type": "float"}
        },
        "constraints": {
            "log_k": {"min": -10, "max": 20}
        }
    }
    
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    with open(schema_path, 'w') as f:
        yaml.dump(default_schema, f)
    
    logger.info(f"Created default schema at {schema_path}")
    return True
