"""
Contract tests for the merged dataframe schema.

These tests verify that the output of the data merge process (T014)
adheres to the expected schema requirements before proceeding to 
preprocessing (T015+).

Expected Schema:
- participant_id: str (unique identifier)
- age: int (>= 60 filter applied later, but column must exist)
- cognitive_score: float (non-null)
- bmi: float (may be null initially, imputed later)
- education: int (may be null initially, imputed later)
- Genera columns: At least 5 columns starting with 'genus_'
"""
import pandas as pd
import pytest
from typing import List, Set
import os

# Constants derived from task requirements
MIN_GENUS_COUNT = 5
REQUIRED_COVARIATES = ['age', 'bmi', 'education']
REQUIRED_CORE = ['participant_id', 'cognitive_score']
MIN_OVERLAP_SAMPLES = 500

def _load_merged_data() -> pd.DataFrame:
    """
    Loads the merged dataset produced by code/01_data_ingestion.py.
    Assumes the file exists at data/processed/merged_raw_data.csv.
    """
    # Standard path for the output of T012/T013/T014
    file_path = "data/processed/merged_raw_data.csv"
    
    if not os.path.exists(file_path):
        pytest.fail(f"Data file not found at {file_path}. "
                    "Run code/01_data_ingestion.py first.")
    
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        pytest.fail(f"Failed to read CSV: {e}")
        
    return df

def _get_genus_columns(df: pd.DataFrame) -> List[str]:
    """Identify columns representing microbial genera."""
    return [col for col in df.columns if col.startswith('genus_')]

class TestMergedDataSchema:
    """Contract tests for the merged dataframe structure."""

    def test_schema_exists(self):
        """Test: The merged dataframe file exists and is loadable."""
        df = _load_merged_data()
        assert df is not None
        assert not df.empty

    def test_minimum_sample_overlap(self):
        """Test: The merge resulted in at least 500 samples."""
        df = _load_merged_data()
        assert len(df) >= MIN_OVERLAP_SAMPLES, \
            f"Sample count {len(df)} is below required minimum {MIN_OVERLAP_SAMPLES}"

    def test_required_core_columns_present(self):
        """Test: All core ID and target columns exist."""
        df = _load_merged_data()
        missing = set(REQUIRED_CORE) - set(df.columns)
        assert not missing, f"Missing core columns: {missing}"

    def test_required_covariate_columns_present(self):
        """Test: All required covariate columns exist (even if null)."""
        df = _load_merged_data()
        missing = set(REQUIRED_COVARIATES) - set(df.columns)
        assert not missing, f"Missing covariate columns: {missing}"

    def test_minimum_genera_count(self):
        """Test: At least 5 microbial genera columns are present."""
        df = _load_merged_data()
        genus_cols = _get_genus_columns(df)
        count = len(genus_cols)
        assert count >= MIN_GENUS_COUNT, \
            f"Found {count} genera columns, required at least {MIN_GENUS_COUNT}"

    def test_cognitive_score_not_empty(self):
        """Test: The cognitive score column has no null values."""
        df = _load_merged_data()
        null_count = df['cognitive_score'].isnull().sum()
        assert null_count == 0, \
            f"cognitive_score contains {null_count} null values"

    def test_participant_id_uniqueness(self):
        """Test: participant_id is unique (no duplicate rows per participant)."""
        df = _load_merged_data()
        duplicates = df['participant_id'].duplicated().sum()
        assert duplicates == 0, \
            f"Found {duplicates} duplicate participant IDs"

    def test_data_types(self):
        """Test: Basic data types are correct."""
        df = _load_merged_data()
        
        # Check ID is string/object
        assert df['participant_id'].dtype == 'object', \
            "participant_id must be string type"
        
        # Check age is numeric
        assert pd.api.types.is_numeric_dtype(df['age']), \
            "age must be numeric"
        
        # Check cognitive_score is numeric
        assert pd.api.types.is_numeric_dtype(df['cognitive_score']), \
            "cognitive_score must be numeric"

class TestMergedDataContentValues:
    """Tests for specific value constraints in the merged data."""

    def test_age_range_reasonable(self):
        """Test: Age values are within a biologically plausible range."""
        df = _load_merged_data()
        ages = df['age']
        assert ages.min() >= 0, "Age cannot be negative"
        assert ages.max() <= 120, "Age cannot exceed 120"
        
        # Note: The >= 60 filter is applied in T015, so we just check plausibility here.

    def test_genera_values_non_negative(self):
        """Test: Microbial abundance columns contain non-negative values."""
        df = _load_merged_data()
        genus_cols = _get_genus_columns(df)
        
        for col in genus_cols:
            if df[col].min() < 0:
                pytest.fail(f"Column {col} contains negative values: {df[col].min()}")

    def test_cognitive_score_range(self):
        """Test: Cognitive scores are within expected bounds (0-100 or similar)."""
        df = _load_merged_data()
        scores = df['cognitive_score']
        
        # HRS cognitive scores are typically 0-27 or similar indices.
        # We assert a very wide bound to avoid false negatives on specific scales,
        # but ensure they are not NaN (checked in schema) and reasonable.
        assert scores.max() <= 1000, "Cognitive score seems implausibly high (>1000)"
        assert scores.min() >= 0, "Cognitive score cannot be negative"