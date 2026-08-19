"""
Schema validation module for dataset and output validation.
Implements the validation rules defined in contracts/*.schema.yaml
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
import yaml

from config import ensure_directories

logger = logging.getLogger(__name__)

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema file."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_rsa_metrics(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate RSA metrics DataFrame against schema rules.
    
    Rules:
    - All required columns present
    - No null values
    - All numeric values positive
    - Species ID format valid
    """
    errors = []
    
    required_columns = ['species_id', 'depth', 'branching_density', 'surface_area']
    for col in required_columns:
        if col not in df.columns:
            errors.append(f"Missing required column: {col}")
    
    if errors:
        return False, errors
    
    # Check for null values
    null_counts = df[required_columns[1:]].isnull().sum()
    if null_counts.any():
        for col, count in null_counts.items():
            if count > 0:
                errors.append(f"Column '{col}' has {count} null values")
    
    # Check for positive values
    numeric_cols = ['depth', 'branching_density', 'surface_area']
    for col in numeric_cols:
        if (df[col] <= 0).any():
            neg_count = (df[col] <= 0).sum()
            errors.append(f"Column '{col}' has {neg_count} non-positive values")
    
    # Check species ID format
    import re
    valid_pattern = re.compile(r'^[a-zA-Z0-9_-]+$')
    invalid_ids = df[~df['species_id'].astype(str).str.match(valid_pattern)]
    if len(invalid_ids) > 0:
        errors.append(f"Found {len(invalid_ids)} invalid species_id formats")
    
    return len(errors) == 0, errors

def validate_physiological_traits(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate physiological traits DataFrame against schema rules.
    
    Rules:
    - All required columns present
    - No null values in required fields
    - All numeric values positive
    - Survival rate between 0 and 1 (if present)
    """
    errors = []
    
    required_columns = ['species_id', 'stomatal_conductance', 'photosynthesis']
    for col in required_columns:
        if col not in df.columns:
            errors.append(f"Missing required column: {col}")
    
    if errors:
        return False, errors
    
    # Check for null values in required columns
    null_counts = df[required_columns[1:]].isnull().sum()
    if null_counts.any():
        for col, count in null_counts.items():
            if count > 0:
                errors.append(f"Column '{col}' has {count} null values")
    
    # Check for positive values
    numeric_cols = ['stomatal_conductance', 'photosynthesis']
    for col in numeric_cols:
        if (df[col] <= 0).any():
            neg_count = (df[col] <= 0).sum()
            errors.append(f"Column '{col}' has {neg_count} non-positive values")
    
    # Check survival rate if present
    if 'survival_rate' in df.columns:
        invalid_sr = df[(df['survival_rate'] < 0) | (df['survival_rate'] > 1)]
        if len(invalid_sr) > 0:
            errors.append(f"Found {len(invalid_sr)} survival_rate values outside [0, 1]")
    
    return len(errors) == 0, errors

def validate_merged_dataset(rsa_df: pd.DataFrame, physio_df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate merged dataset for species overlap and sample size.
    
    Rules:
    - Species overlap exists
    - Sample size >= 55
    """
    errors = []
    
    rsa_species = set(rsa_df['species_id'].unique())
    physio_species = set(physio_df['species_id'].unique())
    
    overlap = rsa_species.intersection(physio_species)
    
    if len(overlap) == 0:
        errors.append("No species overlap between RSA and physiological datasets")
        return False, errors
    
    if len(overlap) < 55:
        errors.append(f"Insufficient species overlap: {len(overlap)} < 55 required")
    
    return len(errors) == 0, errors

def validate_model_results(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate model results DataFrame against schema rules.
    
    Rules:
    - All required columns present
    - R² between 0 and 1
    - P-values between 0 and 1
    - Coefficients are numeric
    """
    errors = []
    
    required_columns = ['model_type', 'predictor', 'coefficient', 'p_value', 'r_squared']
    for col in required_columns:
        if col not in df.columns:
            errors.append(f"Missing required column: {col}")
    
    if errors:
        return False, errors
    
    # Check R² range
    if (df['r_squared'] < 0).any() or (df['r_squared'] > 1).any():
        errors.append("R² values must be between 0 and 1")
    
    # Check p-value range
    if (df['p_value'] < 0).any() or (df['p_value'] > 1).any():
        errors.append("P-values must be between 0 and 1")
    
    # Check adjusted p-value if present
    if 'adjusted_p_value' in df.columns:
        if (df['adjusted_p_value'] < 0).any() or (df['adjusted_p_value'] > 1).any():
            errors.append("Adjusted p-values must be between 0 and 1")
    
    return len(errors) == 0, errors

def validate_vif_compliance(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate VIF compliance DataFrame against schema rules.
    
    Rules:
    - All required columns present
    - VIF score >= 1
    - Boolean fields are actually boolean
    """
    errors = []
    
    required_columns = ['predictor', 'vif_score', 'is_collinear', 'suppression_applied']
    for col in required_columns:
        if col not in df.columns:
            errors.append(f"Missing required column: {col}")
    
    if errors:
        return False, errors
    
    # Check VIF range
    if (df['vif_score'] < 1).any():
        errors.append("VIF scores must be >= 1")
    
    # Check boolean consistency
    if df['is_collinear'].dtype != bool:
        errors.append("is_collinear must be boolean")
    
    if df['suppression_applied'].dtype != bool:
        errors.append("suppression_applied must be boolean")
    
    # Check logical consistency: if VIF > 5, is_collinear should be True
    inconsistent = df[(df['vif_score'] > 5) & (~df['is_collinear'])]
    if len(inconsistent) > 0:
        errors.append(f"Found {len(inconsistent)} rows with VIF > 5 but is_collinear=False")
    
    return len(errors) == 0, errors

def validate_proxy_detection(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate proxy detection results against schema rules.
    
    Rules:
    - has_proxy is boolean
    - If has_proxy is True, proxy_variable must be non-empty string
    """
    errors = []
    
    required_columns = ['has_proxy']
    for col in required_columns:
        if col not in df.columns:
            errors.append(f"Missing required column: {col}")
    
    if errors:
        return False, errors
    
    if df['has_proxy'].dtype != bool:
        errors.append("has_proxy must be boolean")
    
    if 'proxy_variable' in df.columns:
        has_proxy_true = df[df['has_proxy'] == True]
        if len(has_proxy_true) > 0:
            empty_vars = has_proxy_true[has_proxy_true['proxy_variable'].astype(str).str.strip() == '']
            if len(empty_vars) > 0:
                errors.append("proxy_variable must be non-empty when has_proxy=True")
    
    return len(errors) == 0, errors

def main():
    """
    Main validation entry point.
    Validates all datasets and outputs according to schema rules.
    """
    ensure_directories()
    
    project_root = Path(__file__).parent.parent
    contracts_dir = project_root / 'contracts'
    
    # Load schemas (for documentation/logging)
    try:
        dataset_schema = load_schema(contracts_dir / 'dataset.schema.yaml')
        output_schema = load_schema(contracts_dir / 'output.schema.yaml')
        logger.info("Schemas loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load schemas: {e}")
        return 1
    
    # Example validation workflow (actual data paths would be passed as args)
    data_dir = project_root / 'data'
    derived_dir = data_dir / 'derived'
    
    # Validate RSA metrics if exists
    rsa_path = derived_dir / 'rsametrics.csv'
    if rsa_path.exists():
        try:
            rsa_df = pd.read_csv(rsa_path)
            valid, errors = validate_rsa_metrics(rsa_df)
            if valid:
                logger.info(f"RSA metrics validation passed: {rsa_path}")
            else:
                logger.error(f"RSA metrics validation failed: {errors}")
        except Exception as e:
            logger.error(f"Error validating RSA metrics: {e}")
    
    # Validate physiological traits if exists
    physio_path = derived_dir / 'physiological_traits.csv'
    if physio_path.exists():
        try:
            physio_df = pd.read_csv(physio_path)
            valid, errors = validate_physiological_traits(physio_df)
            if valid:
                logger.info(f"Physiological traits validation passed: {physio_path}")
            else:
                logger.error(f"Physiological traits validation failed: {errors}")
        except Exception as e:
            logger.error(f"Error validating physiological traits: {e}")
    
    # Validate model results if exists
    model_path = derived_dir / 'model_results.csv'
    if model_path.exists():
        try:
            model_df = pd.read_csv(model_path)
            valid, errors = validate_model_results(model_df)
            if valid:
                logger.info(f"Model results validation passed: {model_path}")
            else:
                logger.error(f"Model results validation failed: {errors}")
        except Exception as e:
            logger.error(f"Error validating model results: {e}")
    
    logger.info("Schema validation complete")
    return 0

if __name__ == '__main__':
    sys.exit(main())