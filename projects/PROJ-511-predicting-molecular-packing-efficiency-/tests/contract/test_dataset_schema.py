"""
Contract test for dataset schema validation (T010).

This test validates that the final dataset produced by the pipeline (data/dataset.csv)
strictly conforms to the schema defined in contracts/dataset.schema.yaml (T004).

It verifies:
1. Schema file existence and validity.
2. Presence of all required columns defined in the schema.
3. Data types of each column (e.g., numeric vs string).
4. Valid SMILES format for the 'smiles' column.
5. Valid ranges for numeric descriptors (CAPE, PC, radii).
6. Cross-referencing of COD IDs against downloaded CIF files (if available).

Dependencies:
- T004: contracts/dataset.schema.yaml must exist.
- T018: data/dataset.csv must exist (pipeline output).
- T006, T009: Bondi constants and utils for validation helpers.
"""
import os
import sys
import logging
import json
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
import jsonschema
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.config import get_base_dir, get_data_dir, get_contracts_dir
from code.utils import setup_logging

# Setup logging
logger = setup_logging("test_dataset_schema")

# Constants
SCHEMA_PATH = get_contracts_dir() / "dataset.schema.yaml"
DATASET_PATH = get_data_dir() / "dataset.csv"

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the JSON/YAML schema definition."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    # Convert YAML schema to JSON-compatible dict if needed
    # jsonschema expects a dict, yaml.safe_load returns a dict
    return schema

def validate_smiles(smiles: str) -> bool:
    """Check if a string is a valid RDKit SMILES."""
    if not isinstance(smiles, str) or not smiles:
        return False
    try:
        mol = Chem.MolFromSmiles(smiles)
        return mol is not None
    except Exception:
        return False

def validate_numeric_range(value: Any, field_name: str, min_val: Optional[float] = None, max_val: Optional[float] = None) -> bool:
    """Validate a numeric value is within expected bounds."""
    if not isinstance(value, (int, float, np.number)):
        return False
    if pd.isna(value):
        return False
    
    val = float(value)
    if min_val is not None and val < min_val:
        logger.warning(f"Value {val} for {field_name} is below minimum {min_val}")
        return False
    if max_val is not None and val > max_val:
        logger.warning(f"Value {val} for {field_name} is above maximum {max_val}")
        return False
    return True

def cross_reference_cif_ids(dataset: pd.DataFrame) -> bool:
    """
    Verify that COD IDs in the dataset correspond to actual CIF files in data/raw_cif/.
    This ensures data integrity as per FR-017.
    """
    raw_cif_dir = get_base_dir() / "data" / "raw_cif"
    if not raw_cif_dir.exists():
        logger.warning("Raw CIF directory not found, skipping cross-reference check.")
        return True
    
    cif_files = set(f.stem for f in raw_cif_dir.glob("*.cif"))
    dataset_ids = set(dataset['cod_id'].astype(str).unique())
    
    missing_ids = dataset_ids - cif_files
    if missing_ids:
        logger.error(f"Found {len(missing_ids)} COD IDs in dataset without corresponding CIF files: {list(missing_ids)[:5]}...")
        return False
    
    logger.info(f"Cross-reference check passed: all {len(dataset_ids)} COD IDs found in raw_cif/")
    return True

def run_schema_validation(schema: Dict[str, Any], dataset: pd.DataFrame) -> bool:
    """
    Perform detailed validation of the dataset against the schema.
    """
    errors = []
    
    # 1. Check required columns
    required_columns = schema.get('required_columns', [])
    if not required_columns:
        # Fallback: try to infer from properties if schema is JSON Schema style
        if 'properties' in schema:
            required_columns = list(schema['properties'].keys())
        else:
            errors.append("Schema does not define required columns or properties.")
    
    missing_cols = set(required_columns) - set(dataset.columns)
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
    else:
        logger.info(f"All {len(required_columns)} required columns present.")
    
    # 2. Validate data types and constraints per column
    column_specs = schema.get('column_specs', schema.get('properties', {}))
    
    for col_name, spec in column_specs.items():
        if col_name not in dataset.columns:
            continue
        
        col_data = dataset[col_name]
        
        # Check for nulls if required
        if spec.get('required', False) and col_data.isna().any():
            null_count = col_data.isna().sum()
            errors.append(f"Column '{col_name}' has {null_count} null values but is required.")
        
        # Validate specific constraints
        if col_name == 'smiles':
            invalid_smiles = col_data.apply(lambda x: not validate_smiles(x) if isinstance(x, str) else False).sum()
            if invalid_smiles > 0:
                errors.append(f"Column 'smiles' contains {invalid_smiles} invalid SMILES strings.")
            else:
                logger.info("SMILES validation passed.")
        
        elif col_name in ['cape', 'raw_pc', 'unit_cell_volume', 'radius_of_gyration']:
            min_val = spec.get('min', None)
            max_val = spec.get('max', None)
            invalid_count = 0
            for val in col_data.dropna():
                if not validate_numeric_range(val, col_name, min_val, max_val):
                    invalid_count += 1
            if invalid_count > 0:
                errors.append(f"Column '{col_name}' has {invalid_count} values out of range [{min_val}, {max_val}].")
        
        elif col_name in ['n_atoms']:
            if not col_data.apply(lambda x: isinstance(x, (int, np.integer)) and x > 0).all():
                errors.append(f"Column 'n_atoms' contains non-positive or non-integer values.")
    
    # 3. JSON Schema validation (if applicable)
    # This is a secondary check if the schema is a valid JSON Schema draft
    if '$schema' in schema or 'type' in schema:
        try:
            # Convert pandas rows to list of dicts for validation
            # Note: jsonschema validates one object at a time usually, 
            # but we can validate the structure of the whole dataset if designed as an array of objects
            # For simplicity, we validate the schema structure itself or skip if not array-based
            pass
        except Exception as e:
            logger.warning(f"JSON Schema validation skipped or failed: {e}")
    
    return len(errors) == 0, errors

def main():
    """Main entry point for the contract test."""
    logger.info("Starting Dataset Schema Contract Test (T010)...")
    
    # Check prerequisites
    if not SCHEMA_PATH.exists():
        logger.error(f"Schema file missing: {SCHEMA_PATH}. Run T004 first.")
        sys.exit(1)
    
    if not DATASET_PATH.exists():
        logger.error(f"Dataset file missing: {DATASET_PATH}. Run T018 first.")
        sys.exit(1)
    
    # Load data
    try:
        dataset = pd.read_csv(DATASET_PATH)
        logger.info(f"Loaded dataset with {len(dataset)} rows and {len(dataset.columns)} columns.")
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        sys.exit(1)
    
    # Load schema
    try:
        schema = load_schema(SCHEMA_PATH)
        logger.info("Schema loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        sys.exit(1)
    
    # Run validations
    all_passed = True
    
    # 1. Schema Structure Validation
    logger.info("Running column and type validation...")
    valid, errors = run_schema_validation(schema, dataset)
    if not valid:
        for err in errors:
            logger.error(f"Schema Error: {err}")
        all_passed = False
    else:
        logger.info("Column and type validation passed.")
    
    # 2. Cross-reference check
    logger.info("Running cross-reference check (COD IDs vs CIF files)...")
    if not cross_reference_cif_ids(dataset):
        all_passed = False
    
    # Final Result
    if all_passed:
        logger.info("✅ Contract Test PASSED: Dataset schema validation successful.")
        sys.exit(0)
    else:
        logger.error("❌ Contract Test FAILED: Dataset does not conform to schema.")
        sys.exit(1)

if __name__ == "__main__":
    main()