"""
Schema Validation Utility for PROJ-206.

This script provides functions to validate dataframes against the YAML
schemas defined in specs/001-statistical-poll-aggregation/contracts/.
It ensures that data produced by harmonization and modeling steps
adheres to the expected structure and constraints.
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml
import pandas as pd
import numpy as np

# Add project root to path to import utils if needed, though this script
# is self-contained for validation logic.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "specs" / "001-statistical-poll-aggregation" / "contracts"

def load_schema(schema_name: str) -> Dict[str, Any]:
    """Load a schema file from the contracts directory."""
    schema_path = CONTRACTS_DIR / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_dataframe(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """
    Validate a pandas DataFrame against a given schema.
    
    Returns a list of error messages. If the list is empty, validation passed.
    """
    errors = []
    
    # 1. Check required columns
    required_cols = schema.get('column_types', {}).keys()
    actual_cols = set(df.columns)
    missing_cols = set(required_cols) - actual_cols
    
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
    
    # 2. Check data types
    type_map = {
        'integer': (int, np.integer),
        'number': (float, np.floating, int, np.integer),
        'string': (str, object),
        'boolean': (bool, np.bool_)
    }
    
    column_types = schema.get('column_types', {})
    for col_name, expected_type in column_types.items():
        if col_name not in df.columns:
            continue
        
        expected_types = type_map.get(expected_type, (object,))
        # Check if dtype is compatible
        if not any(isinstance(df[col_name].dtype.type, type) for type in expected_types if isinstance(type, type)):
            # More lenient check: try to cast or check underlying type
            # For now, we check if the values are roughly of the right kind
            sample_val = df[col_name].iloc[0] if len(df) > 0 else None
            if sample_val is not None:
                if expected_type == 'integer' and not isinstance(sample_val, (int, np.integer)):
                    errors.append(f"Column '{col_name}' expected integer, got {type(sample_val)}")
                elif expected_type == 'number' and not isinstance(sample_val, (int, float, np.number)):
                    errors.append(f"Column '{col_name}' expected number, got {type(sample_val)}")
                elif expected_type == 'date' and not isinstance(sample_val, str):
                    # Date is string in CSV, so we expect string
                    pass 
                elif expected_type == 'string' and not isinstance(sample_val, str):
                    errors.append(f"Column '{col_name}' expected string, got {type(sample_val)}")

    # 3. Check constraints
    constraints = schema.get('constraints', {})
    
    if constraints.get('unique_pollster_date', False):
        # Specific to dataset schema
        if 'pollster' in df.columns and 'date' in df.columns:
            if df.duplicated(subset=['pollster', 'date']).any():
                errors.append("Constraint violation: Duplicate (pollster, date) pairs found")
    
    if constraints.get('vote_share_range', False):
        range_vals = constraints['vote_share_range']
        if 'vote_share' in df.columns:
            min_val, max_val = range_vals
            if (df['vote_share'] < min_val).any() or (df['vote_share'] > max_val).any():
                errors.append(f"Constraint violation: vote_share outside range [{min_val}, {max_val}]")
    
    if constraints.get('sample_size_positive', False):
        if 'sample_size' in df.columns:
            if (df['sample_size'] <= 0).any():
                errors.append("Constraint violation: sample_size must be positive")
    
    if constraints.get('rmse_non_negative', False):
        if 'historical_rmse' in df.columns:
            if (df['historical_rmse'] < 0).any():
                errors.append("Constraint violation: historical_rmse must be non-negative")

    if constraints.get('forecast_range', False):
        range_vals = constraints['forecast_range']
        forecast_cols = [c for c in df.columns if 'forecast' in c or 'median' in c or 'ci_' in c]
        for col in forecast_cols:
            if col in df.columns:
                min_val, max_val = range_vals
                if (df[col] < min_val).any() or (df[col] > max_val).any():
                    errors.append(f"Constraint violation: {col} outside range [{min_val}, {max_val}]")

    if constraints.get('ci_ordering', False):
        if all(c in df.columns for c in ['bayesian_ci_lower', 'bayesian_median', 'bayesian_ci_upper']):
            if ((df['bayesian_ci_lower'] > df['bayesian_median']) | 
                (df['bayesian_median'] > df['bayesian_ci_upper'])).any():
                errors.append("Constraint violation: CI ordering incorrect (lower <= median <= upper)")

    if constraints.get('unique_date_candidate_model', False):
        if all(c in df.columns for c in ['date', 'candidate', 'model_type']):
            if df.duplicated(subset=['date', 'candidate', 'model_type']).any():
                errors.append("Constraint violation: Duplicate (date, candidate, model_type) pairs found")

    return errors

def main():
    """Run validation on example files if they exist."""
    print("Schema Validation Utility")
    print(f"Contracts directory: {CONTRACTS_DIR}")
    
    # Check if contracts exist
    if not CONTRACTS_DIR.exists():
        print(f"Error: Contracts directory not found at {CONTRACTS_DIR}")
        sys.exit(1)
    
    # Load and print schema info
    try:
        dataset_schema = load_schema('dataset.schema.yaml')
        forecast_schema = load_schema('forecast.schema.yaml')
        print("✓ Schemas loaded successfully.")
        print(f"  - Dataset columns: {list(dataset_schema.get('column_types', {}).keys())}")
        print(f"  - Forecast columns: {list(forecast_schema.get('column_types', {}).keys())}")
    except FileNotFoundError as e:
        print(f"Error loading schemas: {e}")
        sys.exit(1)

    # If processed data exists, validate it
    data_dir = PROJECT_ROOT / "data" / "processed"
    if data_dir.exists():
        cleaned_file = data_dir / "poll_data_cleaned.csv"
        if cleaned_file.exists():
            print(f"\nValidating {cleaned_file}...")
            df = pd.read_csv(cleaned_file)
            errors = validate_dataframe(df, dataset_schema)
            if errors:
                print(f"  ✗ Validation FAILED ({len(errors)} errors):")
                for err in errors:
                    print(f"    - {err}")
            else:
                print("  ✓ Validation PASSED")
        
        forecast_file = data_dir / "frequentist_forecasts.csv"
        if forecast_file.exists():
            print(f"\nValidating {forecast_file}...")
            df = pd.read_csv(forecast_file)
            errors = validate_dataframe(df, forecast_schema)
            if errors:
                print(f"  ✗ Validation FAILED ({len(errors)} errors):")
                for err in errors:
                    print(f"    - {err}")
            else:
                print("  ✓ Validation PASSED")
    else:
        print("\nNo processed data directory found. Skipping data validation.")

if __name__ == "__main__":
    main()