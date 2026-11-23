"""
Schema validation logic for project artifacts.
Loads JSON schemas from contracts/ and validates generated CSV/JSON artifacts.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import json
import yaml

logger = logging.getLogger(__name__)

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a JSON schema from a YAML file."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_column_types(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """Validate column types against schema properties."""
    errors = []
    props = schema.get('properties', {})
    required_cols = [k for k, v in props.items() if v.get('type') == 'object' and v.get('required', [])]
    
    # Check required columns exist
    for col in required_cols:
        if col not in df.columns:
            errors.append(f"Missing required column: {col}")

    # Check types for existing columns
    for col in df.columns:
        if col in props:
            col_schema = props[col]
            if col_schema.get('type') == 'object':
                # Nested object validation skipped for CSV flat structure, 
                # but we check if the column exists as expected.
                continue
            elif col_schema.get('properties'):
                # This implies a nested schema, but CSV is flat. 
                # We assume the CSV columns map to the leaf properties.
                leaf_props = col_schema.get('properties', {})
                for leaf_col, leaf_def in leaf_props.items():
                    if leaf_col in df.columns:
                        expected_type = leaf_def.get('properties', {}).get('type', {}).get('const')
                        if expected_type == 'number':
                            if not pd.api.types.is_numeric_dtype(df[leaf_col]):
                                errors.append(f"Column {leaf_col} should be numeric")
                        elif expected_type == 'string':
                            if not pd.api.types.is_string_dtype(df[leaf_col]) and not pd.api.types.is_object_dtype(df[leaf_col]):
                                errors.append(f"Column {leaf_col} should be string")
    return errors

def validate_rsa_metrics(df: pd.DataFrame, schema_path: Path) -> Tuple[bool, List[str]]:
    """Validate RSA metrics CSV against schema."""
    try:
        schema = load_schema(schema_path)
        errors = validate_column_types(df, schema)
        
        # Specific checks for RSA metrics
        if 'depth' in df.columns:
            if (df['depth'] <= 0).any():
                errors.append("depth must be > 0")
        if 'branching_density' in df.columns:
            if (df['branching_density'] <= 0).any():
                errors.append("branching_density must be > 0")
        if 'surface_area' in df.columns:
            if (df['surface_area'] <= 0).any():
                errors.append("surface_area must be > 0")
        
        return len(errors) == 0, errors
    except Exception as e:
        logger.error(f"Error validating RSA metrics: {e}")
        return False, [str(e)]

def validate_physiological_traits(df: pd.DataFrame, schema_path: Path) -> Tuple[bool, List[str]]:
    """Validate physiological traits CSV against schema."""
    try:
        schema = load_schema(schema_path)
        errors = validate_column_types(df, schema)
        return len(errors) == 0, errors
    except Exception as e:
        logger.error(f"Error validating physiological traits: {e}")
        return False, [str(e)]

def validate_merged_dataset(df: pd.DataFrame, schema_path: Path) -> Tuple[bool, List[str]]:
    """Validate merged dataset CSV against schema."""
    try:
        schema = load_schema(schema_path)
        errors = validate_column_types(df, schema)
        
        # Check PCA/PVR fields if they exist
        pvr_fields = ['pvr_lambda', 'pvr_sigma']
        for field in pvr_fields:
            if field in df.columns:
                if (df[field] < 0).any() and field == 'pvr_lambda':
                    errors.append(f"{field} must be >= 0")
                if (df[field] > 1).any() and field == 'pvr_lambda':
                    errors.append(f"{field} must be <= 1")
        
        return len(errors) == 0, errors
    except Exception as e:
        logger.error(f"Error validating merged dataset: {e}")
        return False, [str(e)]

def validate_model_results(df: pd.DataFrame, schema_path: Path) -> Tuple[bool, List[str]]:
    """Validate model results CSV against schema."""
    try:
        schema = load_schema(schema_path)
        errors = validate_column_types(df, schema)
        
        # Check p-value and R2 ranges
        if 'p_value' in df.columns:
            if (df['p_value'] < 0).any() or (df['p_value'] > 1).any():
                errors.append("p_value must be between 0 and 1")
        if 'r2' in df.columns:
            if (df['r2'] < 0).any() or (df['r2'] > 1).any():
                errors.append("r2 must be between 0 and 1")
        
        return len(errors) == 0, errors
    except Exception as e:
        logger.error(f"Error validating model results: {e}")
        return False, [str(e)]

def validate_vif_compliance(yaml_path: Path) -> Tuple[bool, List[str]]:
    """Validate VIF compliance YAML file."""
    errors = []
    try:
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        
        if not isinstance(data, dict):
            errors.append("VIF compliance file must be a dictionary")
            return False, errors
        
        # Check required fields
        required = ['vif_status', 'suppression_applied']
        for field in required:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        return len(errors) == 0, errors
    except Exception as e:
        logger.error(f"Error validating VIF compliance: {e}")
        return False, [str(e)]

def validate_proxy_detection(yaml_path: Path) -> Tuple[bool, List[str]]:
    """Validate proxy detection YAML file."""
    errors = []
    try:
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        
        if not isinstance(data, dict):
            errors.append("Proxy detection file must be a dictionary")
            return False, errors
        
        if 'has_proxy' not in data:
            errors.append("Missing required field: has_proxy")
        
        return len(errors) == 0, errors
    except Exception as e:
        logger.error(f"Error validating proxy detection: {e}")
        return False, [str(e)]

def main():
    """Main entry point for schema validation."""
    logging.basicConfig(level=logging.INFO)
    project_root = Path(__file__).parent.parent
    contracts_dir = project_root / 'contracts'
    data_dir = project_root / 'data' / 'derived'
    state_dir = project_root / 'state'

    # Define validation tasks
    validations = [
        ('rsametrics', data_dir / 'rsametrics.csv', contracts_dir / 'rsametrics.schema.yaml', validate_rsa_metrics),
        ('merged_data', data_dir / 'merged_data.csv', contracts_dir / 'merged_data.schema.yaml', validate_merged_dataset),
        ('model_results', data_dir / 'model_results.csv', contracts_dir / 'model_results.schema.yaml', validate_model_results),
    ]

    all_passed = True

    for name, file_path, schema_path, validator in validations:
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}. Skipping validation.")
            continue
        
        try:
            df = pd.read_csv(file_path)
            passed, errors = validator(df, schema_path)
            if passed:
                logger.info(f"Validation passed for {name}")
            else:
                logger.error(f"Validation failed for {name}: {errors}")
                all_passed = False
        except Exception as e:
            logger.error(f"Error processing {name}: {e}")
            all_passed = False

    # Validate YAML files
    yaml_validations = [
        ('vif_compliance', state_dir / 'vif_compliance_check.yaml', validate_vif_compliance),
        ('proxy_detection', state_dir / 'proxy_detection.yaml', validate_proxy_detection),
    ]

    for name, file_path, validator in yaml_validations:
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}. Skipping validation.")
            continue
        
        passed, errors = validator(file_path)
        if passed:
            logger.info(f"Validation passed for {name}")
        else:
            logger.error(f"Validation failed for {name}: {errors}")
            all_passed = False

    if all_passed:
        logger.info("All validations passed.")
        return 0
    else:
        logger.error("Some validations failed.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
