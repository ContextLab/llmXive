"""
Contract test for metadata schema validation.

This module implements the validate_metadata_schema function to ensure
that metadata retrieved from the NASA Exoplanet Archive conforms to the
expected schema required for User Story 1 (Data Acquisition and Pre-processing).

Dependencies:
- T011b (code/download.py) must define the expected schema structure.
"""

import pandas as pd
from typing import List, Dict, Any, Optional
import logging

# Configure logging for the test module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Required columns based on T011b requirements and User Story 1 goals
REQUIRED_COLUMNS = [
    'planet_name',
    'host_star_name',
    'equilibrium_temperature',  # K
    'host_metallicity',         # [Fe/H]
    'spectral_resolution',      # R
    'signal_to_noise_ratio',    # SNR
    'planet_category',          # 'Hot Jupiter' or 'Super Earth'
    'spectrum_file_path',
    'upper_limit_flag'          # Boolean indicating censored data
]

# Column type expectations
COLUMN_TYPES = {
    'planet_name': str,
    'host_star_name': str,
    'equilibrium_temperature': (int, float),
    'host_metallicity': (int, float),
    'spectral_resolution': (int, float),
    'signal_to_noise_ratio': (int, float),
    'planet_category': str,
    'spectrum_file_path': str,
    'upper_limit_flag': bool
}

# Valid values for categorical columns
VALID_CATEGORIES = {'Hot Jupiter', 'Super Earth'}

def validate_metadata_schema(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validates that a DataFrame conforms to the expected metadata schema.
    
    This function checks:
    1. All required columns are present
    2. Column data types match expectations
    3. Categorical columns contain valid values
    4. No critical columns have null values (except upper_limit_flag which can be False)
    
    Args:
        df: pandas DataFrame containing exoplanet metadata
        
    Returns:
        Dict with validation results:
        - 'valid': bool indicating if schema is valid
        - 'errors': list of error messages
        - 'warnings': list of warning messages
        - 'missing_columns': list of missing required columns
        - 'type_errors': dict of columns with type mismatches
        - 'null_counts': dict of null counts per required column
    """
    result = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'missing_columns': [],
        'type_errors': {},
        'null_counts': {}
    }
    
    if df is None or df.empty:
        result['valid'] = False
        result['errors'].append("DataFrame is None or empty")
        return result
    
    # Check for required columns
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        result['valid'] = False
        result['missing_columns'] = missing
        result['errors'].append(f"Missing required columns: {missing}")
    
    # Check data types for columns that exist
    for col, expected_type in COLUMN_TYPES.items():
        if col in df.columns:
            # Check if any non-null values have wrong type
            non_null = df[col].dropna()
            if len(non_null) > 0:
                if not all(isinstance(val, expected_type) for val in non_null):
                    result['valid'] = False
                    result['type_errors'][col] = f"Expected {expected_type}, got mixed types"
                    result['errors'].append(f"Type mismatch in column '{col}'")
        
    # Check for null values in critical columns
    critical_columns = ['equilibrium_temperature', 'host_metallicity', 
                      'spectral_resolution', 'signal_to_noise_ratio',
                      'planet_category']
    
    for col in critical_columns:
        if col in df.columns:
            null_count = df[col].isnull().sum()
            result['null_counts'][col] = null_count
            if null_count > 0:
                result['warnings'].append(
                    f"Column '{col}' has {null_count} null values"
                )
    
    # Validate planet_category values
    if 'planet_category' in df.columns:
        invalid_categories = set(df['planet_category'].dropna().unique()) - VALID_CATEGORIES
        if invalid_categories:
            result['valid'] = False
            result['errors'].append(
                f"Invalid planet categories found: {invalid_categories}"
            )
    
    # Validate upper_limit_flag is boolean
    if 'upper_limit_flag' in df.columns:
        non_bool = df['upper_limit_flag'].dropna()
        if len(non_bool) > 0 and not all(isinstance(val, bool) for val in non_bool):
            result['valid'] = False
            result['errors'].append("upper_limit_flag must be boolean")
    
    return result


def test_validate_metadata_schema_basic():
    """Test basic schema validation with valid data."""
    valid_data = pd.DataFrame({
        'planet_name': ['WASP-12b', 'GJ 1214b'],
        'host_star_name': ['WASP-12', 'GJ 1214'],
        'equilibrium_temperature': [2500.0, 500.0],
        'host_metallicity': [0.1, -0.2],
        'spectral_resolution': [100.0, 50.0],
        'signal_to_noise_ratio': [15.0, 8.0],
        'planet_category': ['Hot Jupiter', 'Super Earth'],
        'spectrum_file_path': ['/data/raw/wasp12.fits', '/data/raw/gj1214.fits'],
        'upper_limit_flag': [False, False]
    })
    
    result = validate_metadata_schema(valid_data)
    assert result['valid'] is True
    assert len(result['errors']) == 0
    logger.info("✓ Basic valid schema test passed")

def test_validate_metadata_schema_missing_columns():
    """Test validation with missing required columns."""
    incomplete_data = pd.DataFrame({
        'planet_name': ['WASP-12b'],
        'host_star_name': ['WASP-12']
    })
    
    result = validate_metadata_schema(incomplete_data)
    assert result['valid'] is False
    assert len(result['missing_columns']) > 0
    assert 'equilibrium_temperature' in result['missing_columns']
    logger.info("✓ Missing columns test passed")

def test_validate_metadata_schema_invalid_categories():
    """Test validation with invalid planet categories."""
    invalid_data = pd.DataFrame({
        'planet_name': ['Test Planet'],
        'host_star_name': ['Test Star'],
        'equilibrium_temperature': [1000.0],
        'host_metallicity': [0.0],
        'spectral_resolution': [100.0],
        'signal_to_noise_ratio': [10.0],
        'planet_category': ['Unknown Type'],  # Invalid
        'spectrum_file_path': ['/data/raw/test.fits'],
        'upper_limit_flag': [False]
    })
    
    result = validate_metadata_schema(invalid_data)
    assert result['valid'] is False
    assert any('Invalid planet categories' in err for err in result['errors'])
    logger.info("✓ Invalid categories test passed")

def test_validate_metadata_schema_null_values():
    """Test validation with null values in critical columns."""
    null_data = pd.DataFrame({
        'planet_name': ['WASP-12b'],
        'host_star_name': ['WASP-12'],
        'equilibrium_temperature': [None],  # Null critical value
        'host_metallicity': [0.1],
        'spectral_resolution': [100.0],
        'signal_to_noise_ratio': [15.0],
        'planet_category': ['Hot Jupiter'],
        'spectrum_file_path': ['/data/raw/wasp12.fits'],
        'upper_limit_flag': [False]
    })
    
    result = validate_metadata_schema(null_data)
    assert result['valid'] is True  # Schema is valid, but warnings should exist
    assert 'equilibrium_temperature' in result['null_counts']
    assert result['null_counts']['equilibrium_temperature'] == 1
    assert any('null values' in w for w in result['warnings'])
    logger.info("✓ Null values test passed")

def test_validate_metadata_schema_empty_dataframe():
    """Test validation with empty DataFrame."""
    empty_data = pd.DataFrame()
    
    result = validate_metadata_schema(empty_data)
    assert result['valid'] is False
    assert any('empty' in err for err in result['errors'])
    logger.info("✓ Empty DataFrame test passed")

def test_validate_metadata_schema_type_mismatch():
    """Test validation with type mismatches."""
    type_mismatch_data = pd.DataFrame({
        'planet_name': ['WASP-12b'],
        'host_star_name': ['WASP-12'],
        'equilibrium_temperature': ['2500.0'],  # String instead of number
        'host_metallicity': [0.1],
        'spectral_resolution': [100.0],
        'signal_to_noise_ratio': [15.0],
        'planet_category': ['Hot Jupiter'],
        'spectrum_file_path': ['/data/raw/wasp12.fits'],
        'upper_limit_flag': [False]
    })
    
    result = validate_metadata_schema(type_mismatch_data)
    assert result['valid'] is False
    assert 'equilibrium_temperature' in result['type_errors']
    logger.info("✓ Type mismatch test passed")

if __name__ == "__main__":
    logger.info("Running metadata schema contract tests...")
    test_validate_metadata_schema_basic()
    test_validate_metadata_schema_missing_columns()
    test_validate_metadata_schema_invalid_categories()
    test_validate_metadata_schema_null_values()
    test_validate_metadata_schema_empty_dataframe()
    test_validate_metadata_schema_type_mismatch()
    logger.info("All contract tests passed!")