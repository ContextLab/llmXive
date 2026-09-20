"""
Contract tests for the analysis cohort schema (T010).
Verifies that the analysis_cohort.csv contains the expected columns and data types.
"""
import pytest
import pandas as pd
from pathlib import Path
import sys

code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

EXPECTED_COLUMNS = {
    'age': 'numeric',
    'gender': 'categorical',
    'education': 'categorical',
    'income': 'numeric',
    'social_support': 'numeric',
    'harassment_severity': 'numeric',
    'harassment_exposure': 'boolean',
    'depression': 'numeric',
    'anxiety': 'numeric',
    'ptsd': 'numeric' # Optional if PCL-5 is missing, but schema should handle it
}

def load_cohort():
    cohort_path = Path(__file__).parent.parent.parent / "data" / "results" / "analysis_cohort.csv"
    if not cohort_path.exists():
        pytest.skip("analysis_cohort.csv not found. Run the pipeline first.")
    return pd.read_csv(cohort_path)

def test_cohort_exists():
    """Test that the cohort file exists."""
    cohort_path = Path(__file__).parent.parent.parent / "data" / "results" / "analysis_cohort.csv"
    assert cohort_path.exists(), "analysis_cohort.csv does not exist"

def test_required_columns_present():
    """Test that all required columns are present in the cohort."""
    df = load_cohort()
    required_cols = ['harassment_severity', 'social_support', 'depression', 'anxiety']
    missing_cols = [col for col in required_cols if col not in df.columns]
    assert len(missing_cols) == 0, f"Missing required columns: {missing_cols}"

def test_column_types():
    """Test that numeric columns are numeric."""
    df = load_cohort()
    numeric_cols = ['age', 'social_support', 'harassment_severity', 'depression', 'anxiety']
    if 'ptsd' in df.columns:
        numeric_cols.append('ptsd')

    for col in numeric_cols:
        if col in df.columns:
            assert pd.api.types.is_numeric_dtype(df[col]), f"Column {col} is not numeric"

def test_no_nulls_in_critical_columns():
    """Test that critical columns have no null values after preprocessing."""
    df = load_cohort()
    critical_cols = ['harassment_severity', 'social_support', 'depression', 'anxiety']
    for col in critical_cols:
        if col in df.columns:
            assert df[col].isnull().sum() == 0, f"Column {col} contains null values"