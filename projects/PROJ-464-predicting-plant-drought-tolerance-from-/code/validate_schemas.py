"""
Schema validation module for llmXive Project PROJ-464.
Implements validation logic against contracts/dataset.schema.yaml and contracts/output.schema.yaml.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = PROJECT_ROOT / "contracts"
DATASET_SCHEMA_PATH = SCHEMA_DIR / "dataset.schema.yaml"
OUTPUT_SCHEMA_PATH = SCHEMA_DIR / "output.schema.yaml"

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema definition."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_column_types(df: pd.DataFrame, schema_def: Dict[str, Any]) -> List[str]:
    """Validate column types and constraints based on schema definition."""
    errors = []
    properties = schema_def.get('properties', {})
    
    for col, spec in properties.items():
        if col not in df.columns:
            if spec.get('required', False):
                errors.append(f"Missing required column: {col}")
            continue
        
        # Check for null values in numeric columns
        if spec.get('type') == 'number' or spec.get('type') == 'integer':
            if df[col].isnull().any():
                errors.append(f"Column '{col}' contains null values")
            
            # Check minimum constraints
            min_val = spec.get('minimum')
            if min_val is not None:
                if spec.get('exclusiveMinimum', False):
                    if (df[col] <= min_val).any():
                        errors.append(f"Column '{col}' contains values <= {min_val}")
                else:
                    if (df[col] < min_val).any():
                        errors.append(f"Column '{col}' contains values < {min_val}")
            
            # Check maximum constraints
            max_val = spec.get('maximum')
            if max_val is not None:
                if (df[col] > max_val).any():
                    errors.append(f"Column '{col}' contains values > {max_val}")
        
        # Check string patterns
        elif spec.get('type') == 'string':
            pattern = spec.get('pattern')
            if pattern:
                import re
                if df[col].apply(lambda x: bool(re.match(pattern, str(x)) if pd.notna(x) else False)).all() == False:
                    errors.append(f"Column '{col}' contains values not matching pattern: {pattern}")
    
    return errors

def validate_rsa_metrics(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validate RSA metrics dataframe against schema."""
    schema = load_schema(DATASET_SCHEMA_PATH)
    schema_def = schema['schemas']['rsa_metrics']
    
    errors = validate_column_types(df, schema_def)
    
    # Additional rule: positive_numerics
    numeric_cols = ['depth', 'branching_density', 'surface_area']
    for col in numeric_cols:
        if col in df.columns:
            if (df[col] <= 0).any():
                errors.append(f"Column '{col}' must be strictly positive")
    
    return len(errors) == 0, errors

def validate_physiological_traits(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validate physiological traits dataframe against schema."""
    schema = load_schema(DATASET_SCHEMA_PATH)
    schema_def = schema['schemas']['physiological_traits']
    
    errors = validate_column_types(df, schema_def)
    
    # Additional rule: positive_numerics
    numeric_cols = ['stomatal_conductance', 'photosynthesis_rate']
    for col in numeric_cols:
        if col in df.columns:
            if (df[col] <= 0).any():
                errors.append(f"Column '{col}' must be strictly positive")
    
    return len(errors) == 0, errors

def validate_merged_dataset(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validate merged dataset against schema."""
    schema = load_schema(DATASET_SCHEMA_PATH)
    schema_def = schema['schemas']['merged_dataset']
    
    errors = validate_column_types(df, schema_def)
    
    # Additional rule: sample_size_constraint
    if len(df) < 55:
        errors.append(f"Insufficient species after merge (N={len(df)} < 55). HALT required.")
    
    # Additional rule: positive_numerics
    numeric_cols = ['depth', 'branching_density', 'surface_area', 'stomatal_conductance', 'photosynthesis_rate']
    for col in numeric_cols:
        if col in df.columns:
            if (df[col] <= 0).any():
                errors.append(f"Column '{col}' must be strictly positive")
    
    return len(errors) == 0, errors

def validate_model_results(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validate model results dataframe against schema."""
    errors = []
    
    if 'r_squared' in df.columns:
        if ((df['r_squared'] < 0) | (df['r_squared'] > 1)).any():
            errors.append("R-squared values must be between 0 and 1")
    
    if 'p_values' in df.columns or any('p_value' in str(c) for c in df.columns):
        p_cols = [c for c in df.columns if 'p_value' in str(c)]
        for col in p_cols:
            if (df[col] < 0).any():
                errors.append(f"P-values in '{col}' must be non-negative")
    
    return len(errors) == 0, errors

def validate_vif_compliance(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate VIF compliance check data."""
    errors = []
    
    max_vif = data.get('max_vif', 0)
    suppression_applied = data.get('suppression_applied', False)
    suppressed_variables = data.get('suppressed_variables', [])
    
    # Rule: IF max_vif > 5 THEN suppression_applied == true AND len(suppressed_variables) > 0
    if max_vif > 5:
        if not suppression_applied:
            errors.append("VIF > 5 detected but suppression was not applied")
        if len(suppressed_variables) == 0:
            errors.append("VIF > 5 detected but no variables were suppressed")
    
    return len(errors) == 0, errors

def validate_proxy_detection(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate proxy detection status data."""
    errors = []
    
    has_proxy = data.get('has_proxy', False)
    classification_status = data.get('classification_status', 'SKIPPED')
    
    if has_proxy and classification_status != 'EXECUTED':
        errors.append("Proxy found but classification status is not EXECUTED")
    
    if not has_proxy and classification_status != 'SKIPPED':
        errors.append("No proxy found but classification status is not SKIPPED")
    
    return len(errors) == 0, errors

def main():
    """Run all schema validations."""
    logger.info("Starting schema validation...")
    
    # Example validation calls (these would be triggered by specific tasks)
    # 1. Validate RSA metrics if file exists
    rsa_path = PROJECT_ROOT / "data/derived/rsametrics.csv"
    if rsa_path.exists():
        df = pd.read_csv(rsa_path)
        valid, errors = validate_rsa_metrics(df)
        if valid:
            logger.info("RSA metrics validation: PASSED")
        else:
            logger.error(f"RSA metrics validation: FAILED - {errors}")
    
    # 2. Validate merged dataset if file exists
    merged_path = PROJECT_ROOT / "data/derived/merged_dataset.csv"
    if merged_path.exists():
        df = pd.read_csv(merged_path)
        valid, errors = validate_merged_dataset(df)
        if valid:
            logger.info("Merged dataset validation: PASSED")
        else:
            logger.error(f"Merged dataset validation: FAILED - {errors}")
    
    logger.info("Schema validation complete.")

if __name__ == "__main__":
    main()