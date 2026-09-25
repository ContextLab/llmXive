"""
Contract test for analysis cohort schema validation.

Verifies that the analysis cohort produced by the pipeline
matches the expected schema defined in the specification.
"""
import pytest
import pandas as pd
from pathlib import Path
import json

# Project root
project_root = Path(__file__).parent.parent.parent.parent
cohort_path = project_root / "data" / "results" / "analysis_cohort.csv"

def get_expected_schema():
    """Return the expected schema for the analysis cohort."""
    return {
        'required_columns': [
            'social_support',
            'harassment_severity',
            'harassment_exposure',
            'depression',
            'anxiety',
            'ptsd',
            'age',
            'gender',
            'education',
            'income',
            'platform'
        ],
        'column_types': {
            'social_support': 'float64',
            'harassment_severity': 'float64',
            'harassment_exposure': 'int64',
            'depression': 'float64',
            'anxiety': 'float64',
            'ptsd': 'float64',
            'age': 'float64',
            'gender': 'object',
            'education': 'object',
            'income': 'float64',
            'platform': 'object'
        }
    }

@pytest.mark.skipif(not cohort_path.exists(), reason="Analysis cohort not yet generated")
def test_cohort_schema():
    """Test that the analysis cohort matches the expected schema."""
    if not cohort_path.exists():
        pytest.skip("Cohort file not found")
    
    df = pd.read_csv(cohort_path)
    schema = get_expected_schema()
    
    # Check required columns
    missing_cols = set(schema['required_columns']) - set(df.columns)
    assert len(missing_cols) == 0, f"Missing required columns: {missing_cols}"
    
    # Check column types (approximate)
    for col, expected_type in schema['column_types'].items():
        if col in df.columns:
            # For object types, we just check presence
            if expected_type == 'object':
                assert df[col].dtype == 'object' or df[col].dtype.name.startswith('str')
            else:
                # For numeric types, check if it's a numeric dtype
                assert pd.api.types.is_numeric_dtype(df[col])

@pytest.mark.skipif(not cohort_path.exists(), reason="Analysis cohort not yet generated")
def test_cohort_not_empty():
    """Test that the analysis cohort contains data."""
    if not cohort_path.exists():
        pytest.skip("Cohort file not found")
    
    df = pd.read_csv(cohort_path)
    assert len(df) > 0, "Analysis cohort is empty"
