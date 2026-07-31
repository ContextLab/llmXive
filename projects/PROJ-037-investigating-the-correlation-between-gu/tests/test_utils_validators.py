"""
Unit tests for data validation utilities.
"""
import pytest
import pandas as pd
import numpy as np

from code.utils.validators import validate_schema, validate_non_null, validate_merged_cohort

def test_validate_schema_valid():
    """Test schema validation with valid data."""
    df = pd.DataFrame({"id": [1, 2], "value": [1.0, 2.0]})
    schema = {"id": "int64", "value": "float64"}

    assert validate_schema(df, schema) is True

def test_validate_schema_missing_column():
    """Test schema validation with missing column."""
    df = pd.DataFrame({"id": [1, 2]})
    schema = {"id": "int64", "value": "float64"}

    assert validate_schema(df, schema) is False

def test_validate_non_null_valid():
    """Test non-null validation with valid data."""
    df = pd.DataFrame({"id": [1, 2], "value": [1.0, 2.0]})
    assert validate_non_null(df, ["id", "value"]) is True

def test_validate_non_null_null_values():
    """Test non-null validation with null values."""
    df = pd.DataFrame({"id": [1, None], "value": [1.0, 2.0]})
    assert validate_non_null(df, ["id"]) is False

def test_validate_merged_cohort_valid():
    """Test merged cohort validation with valid data."""
    df = pd.DataFrame({
        "participant_id": ["P1", "P2"],
        "shannon": [3.5, 4.1],
        "sleep_duration": [7.0, 8.0]
    })
    assert validate_merged_cohort(df) is True

def test_validate_merged_cohort_null_participant_id():
    """Test merged cohort validation with null participant_id."""
    df = pd.DataFrame({
        "participant_id": [None, "P2"],
        "shannon": [3.5, 4.1],
        "sleep_duration": [7.0, 8.0]
    })
    assert validate_merged_cohort(df) is False

def test_validate_merged_cohort_null_sleep_duration():
    """Test merged cohort validation with null sleep_duration."""
    df = pd.DataFrame({
        "participant_id": ["P1", "P2"],
        "shannon": [3.5, 4.1],
        "sleep_duration": [7.0, None]
    })
    assert validate_merged_cohort(df) is False