"""
Schema validation utilities for the corrosion potential prediction pipeline.

This module provides functions to validate data against schema contracts,
enforce non-null constraints, and verify data quality metrics.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Type, Union

import pandas as pd
import yaml

from utils.logging import get_logger
from utils.exceptions import DataInsufficientError, SchemaMismatchError

# Get logger for this module
logger = get_logger(__name__)

# Critical fields that must not be null based on data-model.md and contracts
CRITICAL_FIELDS = [
    'alloy_id',
    'specific_alloy_designation',
    'potential_mV',
    'ph',
    'temperature'
]

# Minimum record count requirement from FR-014
MIN_RECORD_COUNT = 500

# Minimum alloy diversity requirement from FR-004/LOSO requirement
MIN_ALLOY_COUNT = 10


def load_schema_contract(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a YAML schema contract from disk.
    
    Args:
        schema_path: Path to the schema YAML file
        
    Returns:
        Dictionary containing the schema definition
        
    Raises:
        FileNotFoundError: If schema file doesn't exist
        yaml.YAMLError: If schema file is not valid YAML
    """
    schema_path = Path(schema_path)
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema contract not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def validate_schema_structure(df: pd.DataFrame, schema: Dict[str, Any]) -> bool:
    """
    Validate that DataFrame columns match the expected schema structure.
    
    Args:
        df: DataFrame to validate
        schema: Schema definition dictionary
        
    Returns:
        True if schema structure matches, False otherwise
        
    Raises:
        SchemaMismatchError: If required columns are missing
    """
    required_columns = set(schema.get('required_fields', []))
    actual_columns = set(df.columns)
    
    missing_columns = required_columns - actual_columns
    if missing_columns:
        error_msg = f"Schema mismatch: Missing required columns: {missing_columns}"
        logger.error(error_msg)
        raise SchemaMismatchError(error_msg)
    
    logger.info(f"Schema structure validation passed. Found {len(actual_columns)} columns.")
    return True


def validate_non_nulls(df: pd.DataFrame, fields: Optional[List[str]] = None) -> Dict[str, int]:
    """
    Validate non-null constraints on specified fields.
    
    Args:
        df: DataFrame to validate
        fields: List of field names to check. Defaults to CRITICAL_FIELDS.
        
    Returns:
        Dictionary mapping field names to null counts
        
    Raises:
        SchemaMismatchError: If any critical field has null values
    """
    if fields is None:
        fields = CRITICAL_FIELDS
    
    null_counts = {}
    critical_nulls = []
    
    for field in fields:
        if field in df.columns:
            null_count = int(df[field].isna().sum())
            null_counts[field] = null_count
            if null_count > 0:
                critical_nulls.append(field)
                logger.warning(f"Field '{field}' has {null_count} null values.")
        else:
            logger.warning(f"Field '{field}' not found in DataFrame.")
            null_counts[field] = -1  # Indicate missing field
    
    if critical_nulls:
        error_msg = (
            f"Schema validation failed: Critical fields have null values: {critical_nulls}. "
            f"Null counts: { {k: null_counts[k] for k in critical_nulls} }"
        )
        logger.error(error_msg)
        raise SchemaMismatchError(error_msg)
    
    logger.info("Non-null validation passed for all critical fields.")
    return null_counts


def validate_record_count(df: pd.DataFrame, min_count: int = MIN_RECORD_COUNT) -> int:
    """
    Validate that the dataset meets the minimum record count requirement.
    
    Args:
        df: DataFrame to validate
        min_count: Minimum required record count (default: MIN_RECORD_COUNT)
        
    Returns:
        The actual record count
        
    Raises:
        SchemaMismatchError: If record count is below minimum
    """
    record_count = len(df)
    
    if record_count < min_count:
        error_msg = (
            f"Data insufficient: Record count ({record_count}) is below minimum "
            f"requirement ({min_count}). Pipeline halted as per FR-014."
        )
        logger.error(error_msg)
        # Raise SchemaMismatchError as mandated by FR-014
        raise SchemaMismatchError(error_msg)
    
    logger.info(f"Record count validation passed: {record_count} records >= {min_count} minimum.")
    return record_count


def validate_alloy_diversity(df: pd.DataFrame, 
                             alloy_column: str = 'specific_alloy_designation',
                             min_alloys: int = MIN_ALLOY_COUNT) -> int:
    """
    Validate that the dataset has sufficient alloy diversity for LOSO splitting.
    
    Args:
        df: DataFrame to validate
        alloy_column: Column name containing alloy designations
        min_alloys: Minimum required unique alloy designations
        
    Returns:
        The number of unique alloy designations
        
    Raises:
        DataInsufficientError: If alloy diversity is insufficient
    """
    if alloy_column not in df.columns:
        error_msg = f"Alloy column '{alloy_column}' not found in DataFrame."
        logger.error(error_msg)
        raise DataInsufficientError(error_msg)
    
    unique_alloys = df[alloy_column].nunique()
    
    if unique_alloys < min_alloys:
        error_msg = (
            f"Data insufficient: Found {unique_alloys} unique alloy designations, "
            f"but minimum required is {min_alloys} for Leave-One-Specific-Alloy-Out splitting."
        )
        logger.error(error_msg)
        raise DataInsufficientError(error_msg)
    
    logger.info(f"Alloy diversity validation passed: {unique_alloys} unique alloys >= {min_alloys} minimum.")
    return unique_alloys


def filter_null_records(df: pd.DataFrame, 
                        fields: Optional[List[str]] = None) -> Tuple[pd.DataFrame, int]:
    """
    Filter out records with null values in specified fields.
    
    Args:
        df: DataFrame to filter
        fields: List of field names to check for nulls
        
    Returns:
        Tuple of (filtered DataFrame, count of removed records)
        
    Note:
        This function does NOT raise an error. It simply removes null records
        and returns the cleaned dataset. Use validate_non_nulls() if you want
        to raise errors on nulls.
    """
    if fields is None:
        fields = CRITICAL_FIELDS
    
    # Only filter on fields that exist in the DataFrame
    existing_fields = [f for f in fields if f in df.columns]
    
    if not existing_fields:
        logger.warning("No fields to filter on. Returning original DataFrame.")
        return df, 0
    
    initial_count = len(df)
    
    # Drop rows where any of the specified fields are null
    filtered_df = df.dropna(subset=existing_fields)
    
    removed_count = initial_count - len(filtered_df)
    
    if removed_count > 0:
        logger.info(f"Removed {removed_count} records with null values in {existing_fields}.")
    else:
        logger.info("No records removed. All specified fields have no nulls.")
    
    return filtered_df, removed_count


def run_full_validation(df: pd.DataFrame, 
                        schema_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Run a full validation suite on the dataset.
    
    This function performs:
    1. Schema structure validation (if schema_path provided)
    2. Non-null validation on critical fields
    3. Record count validation
    4. Alloy diversity validation
    
    Args:
        df: DataFrame to validate
        schema_path: Optional path to schema contract YAML
        
    Returns:
        Dictionary containing validation results and statistics
        
    Raises:
        SchemaMismatchError: If schema validation fails
        DataInsufficientError: If data quality requirements are not met
    """
    results = {
        'status': 'pending',
        'record_count': None,
        'unique_alloys': None,
        'null_counts': {},
        'schema_valid': False,
        'errors': []
    }
    
    try:
        # 1. Schema structure validation
        if schema_path:
            try:
                schema = load_schema_contract(schema_path)
                validate_schema_structure(df, schema)
                results['schema_valid'] = True
            except FileNotFoundError as e:
                logger.warning(f"Schema file not found, skipping structure validation: {e}")
                results['errors'].append(f"Schema file not found: {e}")
            except Exception as e:
                results['errors'].append(f"Schema validation error: {e}")
                raise
        
        # 2. Non-null validation
        try:
            null_counts = validate_non_nulls(df)
            results['null_counts'] = null_counts
        except SchemaMismatchError as e:
            results['errors'].append(f"Non-null validation failed: {e}")
            raise
        
        # 3. Record count validation
        try:
            record_count = validate_record_count(df)
            results['record_count'] = record_count
        except SchemaMismatchError as e:
            results['errors'].append(f"Record count validation failed: {e}")
            raise
        
        # 4. Alloy diversity validation
        try:
            unique_alloys = validate_alloy_diversity(df)
            results['unique_alloys'] = unique_alloys
        except DataInsufficientError as e:
            results['errors'].append(f"Alloy diversity validation failed: {e}")
            raise
        
        results['status'] = 'passed'
        logger.info("Full validation suite completed successfully.")
        
    except Exception as e:
        results['status'] = 'failed'
        logger.error(f"Validation failed: {e}")
        raise
    
    return results


def write_validation_log(validation_results: Dict[str, Any], 
                         log_path: Union[str, Path]) -> None:
    """
    Write validation results to a log file.
    
    Args:
        validation_results: Dictionary containing validation results
        log_path: Path to the output log file
    """
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(validation_results, f, indent=2, default=str)
    
    logger.info(f"Validation log written to: {log_path}")


def check_schema_validation_prerequisite() -> bool:
    """
    Check if the schema validation prerequisite (T004) has been completed.
    
    This function verifies that:
    1. The schema validation log exists
    2. The log indicates successful validation
    
    Returns:
        True if prerequisite is satisfied, False otherwise
    """
    log_path = Path('data/logs/schema_validation.log')
    
    if not log_path.exists():
        logger.warning(f"Prerequisite check failed: {log_path} does not exist.")
        return False
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        # Check for success indicator
        if 'status' in log_content and 'PASS' in log_content:
            logger.info("Schema validation prerequisite (T004) verified successfully.")
            return True
        else:
            logger.warning("Schema validation log exists but does not indicate success.")
            return False
            
    except Exception as e:
        logger.error(f"Error reading schema validation log: {e}")
        return False