import os
import json
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
import sys

# Add code directory to path for imports
code_dir = Path(__file__).resolve().parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from uq.verify_predictions import verify_schema, verify_data_integrity

@pytest.fixture
def valid_dataframe():
    """Create a valid DataFrame matching the expected schema."""
    data = {
        "sample_id": [1, 2, 3, 4, 5],
        "method": ["DeepEnsemble", "MCDropout", "SparseGP", "DeepEnsemble", "MCDropout"],
        "prediction": [-1.5, -2.0, -1.8, -1.6, -2.1],
        "variance": [0.05, 0.06, 0.04, 0.055, 0.058],
        "lower_50": [-1.7, -2.2, -2.0, -1.8, -2.3],
        "upper_50": [-1.3, -1.8, -1.6, -1.4, -1.9],
        "lower_90": [-2.0, -2.4, -2.2, -1.9, -2.5],
        "upper_90": [-1.0, -1.6, -1.4, -1.3, -1.7],
        "aleatoric": [0.03, 0.04, np.nan, 0.035, 0.042],
        "epistemic": [0.02, 0.02, np.nan, 0.02, 0.016],
        "total": [0.05, 0.06, 0.04, 0.055, 0.058],
        "uncertainty_type": ["mixed", "mixed", "total", "mixed", "mixed"]
    }
    return pd.DataFrame(data)

def test_verify_schema_valid(valid_dataframe):
    """Test that a valid DataFrame passes schema verification."""
    assert verify_schema(valid_dataframe, "test.csv") is True

def test_verify_schema_missing_columns():
    """Test that a DataFrame with missing columns fails schema verification."""
    data = {
        "sample_id": [1, 2],
        "method": ["DeepEnsemble", "MCDropout"],
        "prediction": [-1.5, -2.0]
    }
    df = pd.DataFrame(data)
    assert verify_schema(df, "test.csv") is False

def test_verify_schema_wrong_order():
    """Test that a DataFrame with wrong column order fails schema verification."""
    from uq.verify_predictions import REQUIRED_COLUMNS
    # Create a DataFrame with columns in wrong order
    data = {}
    for col in reversed(REQUIRED_COLUMNS):
        if col == "sample_id":
            data[col] = [1, 2]
        elif col == "method":
            data[col] = ["DeepEnsemble", "MCDropout"]
        else:
            data[col] = [0.0, 0.0]
    df = pd.DataFrame(data)
    assert verify_schema(df, "test.csv") is False

def test_verify_data_integrity_valid(valid_dataframe):
    """Test that valid data passes integrity checks."""
    assert verify_data_integrity(valid_dataframe, "test.csv") is True

def test_verify_data_integrity_negative_variance():
    """Test that negative variance fails integrity check."""
    df = pd.DataFrame({
        "sample_id": [1],
        "method": ["DeepEnsemble"],
        "prediction": [-1.5],
        "variance": [-0.1],
        "lower_50": [-1.7],
        "upper_50": [-1.3],
        "lower_90": [-2.0],
        "upper_90": [-1.0],
        "aleatoric": [0.0],
        "epistemic": [0.0],
        "total": [0.0],
        "uncertainty_type": ["mixed"]
    })
    assert verify_data_integrity(df, "test.csv") is False

def test_verify_data_integrity_invalid_bounds():
    """Test that invalid bounds (lower > upper) fails integrity check."""
    df = pd.DataFrame({
        "sample_id": [1],
        "method": ["DeepEnsemble"],
        "prediction": [-1.5],
        "variance": [0.05],
        "lower_50": [-1.3],  # Invalid: greater than prediction
        "upper_50": [-1.7],  # Invalid: less than prediction
        "lower_90": [-2.0],
        "upper_90": [-1.0],
        "aleatoric": [0.0],
        "epistemic": [0.0],
        "total": [0.0],
        "uncertainty_type": ["mixed"]
    })
    assert verify_data_integrity(df, "test.csv") is False

def test_verify_data_integrity_duplicate_sample_id():
    """Test that duplicate sample_id fails integrity check."""
    df = pd.DataFrame({
        "sample_id": [1, 1],
        "method": ["DeepEnsemble", "MCDropout"],
        "prediction": [-1.5, -2.0],
        "variance": [0.05, 0.06],
        "lower_50": [-1.7, -2.2],
        "upper_50": [-1.3, -1.8],
        "lower_90": [-2.0, -2.4],
        "upper_90": [-1.0, -1.6],
        "aleatoric": [0.0, 0.0],
        "epistemic": [0.0, 0.0],
        "total": [0.0, 0.0],
        "uncertainty_type": ["mixed", "mixed"]
    })
    assert verify_data_integrity(df, "test.csv") is False

def test_verify_data_integrity_invalid_method():
    """Test that invalid method name fails integrity check."""
    df = pd.DataFrame({
        "sample_id": [1],
        "method": ["InvalidMethod"],
        "prediction": [-1.5],
        "variance": [0.05],
        "lower_50": [-1.7],
        "upper_50": [-1.3],
        "lower_90": [-2.0],
        "upper_90": [-1.0],
        "aleatoric": [0.0],
        "epistemic": [0.0],
        "total": [0.0],
        "uncertainty_type": ["mixed"]
    })
    assert verify_data_integrity(df, "test.csv") is False