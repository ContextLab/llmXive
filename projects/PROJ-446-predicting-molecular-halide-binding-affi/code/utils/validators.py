import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import yaml
import pandas as pd

from rdkit import Chem

def load_schema(schema_path: Optional[str] = None) -> Dict[str, Any]:
    """Load the dataset schema from YAML."""
    if schema_path is None:
        schema_path = Path(__file__).parent.parent.parent / "specs" / "dataset.schema.yaml"
    if not Path(schema_path).exists():
        # Fallback to a minimal schema if file not found
        return {
            "required_columns": ["host_id", "halide_identity", "affinity_value", "affinity_unit", "smiles"],
            "types": {
                "host_id": "string",
                "halide_identity": "string",
                "affinity_value": "float",
                "affinity_unit": "string",
                "smiles": "string"
            }
        }
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_smiles(smiles: str) -> bool:
    """Validate if a string is a valid SMILES."""
    if not smiles or pd.isna(smiles):
        return False
    try:
        mol = Chem.MolFromSmiles(str(smiles))
        return mol is not None
    except:
        return False

def validate_column_types(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """Check if column types match the schema."""
    errors = []
    types_map = {
        "string": str,
        "float": float,
        "int": int,
        "object": object
    }
    
    for col, type_str in schema.get("types", {}).items():
        if col not in df.columns:
            continue
        expected_type = types_map.get(type_str, object)
        if not all(isinstance(x, expected_type) or pd.isna(x) for x in df[col]):
            errors.append(f"Column {col} has invalid type. Expected {type_str}")
    return errors

def validate_required_columns(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """Check if all required columns are present."""
    required = schema.get("required_columns", [])
    missing = [col for col in required if col not in df.columns]
    return missing

def validate_constraints(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """Check specific constraints (e.g., non-null, ranges)."""
    errors = []
    constraints = schema.get("constraints", {})
    
    for col, rules in constraints.items():
        if col not in df.columns:
            continue
        if rules.get("not_null", False) and df[col].isna().any():
            errors.append(f"Column {col} contains null values")
        # Add more constraint checks as needed
    return errors

def validate_dataset(df: pd.DataFrame, schema: Optional[Dict[str, Any]] = None) -> Tuple[bool, List[str]]:
    """Validate a dataframe against a schema."""
    if schema is None:
        schema = load_schema()
    
    errors = []
    errors.extend(validate_required_columns(df, schema))
    errors.extend(validate_column_types(df, schema))
    errors.extend(validate_constraints(df, schema))
    
    return len(errors) == 0, errors

def ensure_schema_file_exists():
    """Ensure the schema file exists."""
    schema_path = Path(__file__).parent.parent.parent / "specs" / "dataset.schema.yaml"
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    if not schema_path.exists():
        with open(schema_path, 'w') as f:
            yaml.dump({
                "required_columns": ["host_id", "halide_identity", "affinity_value", "affinity_unit", "smiles"],
                "types": {
                    "host_id": "string",
                    "halide_identity": "string",
                    "affinity_value": "float",
                    "affinity_unit": "string",
                    "smiles": "string"
                },
                "constraints": {
                    "halide_identity": {"not_null": True},
                    "affinity_value": {"not_null": True}
                }
            }, f)

def validate_dataframe_for_host_filtering(df: pd.DataFrame) -> bool:
    """Check if dataframe has necessary columns for host filtering."""
    required = ["host_id", "halide_identity"]
    return all(col in df.columns for col in required)
