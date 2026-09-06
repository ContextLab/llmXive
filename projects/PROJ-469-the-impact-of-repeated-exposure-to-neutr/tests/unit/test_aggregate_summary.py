"""
Unit tests for T029: Aggregate Summary Generation.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Mock the config_manager to return temp paths
from unittest.mock import patch, MagicMock

from aggregate_summary import extract_model_summary, extract_diagnostics, load_csv_safely

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

def test_load_csv_safely_exists(temp_dir):
    """Test loading an existing CSV."""
    file_path = temp_dir / "test.csv"
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    df.to_csv(file_path, index=False)
    
    result = load_csv_safely(file_path)
    assert result is not None
    assert len(result) == 2

def test_load_csv_safely_missing(temp_dir):
    """Test loading a non-existent CSV returns None."""
    file_path = temp_dir / "nonexistent.csv"
    result = load_csv_safely(file_path)
    assert result is None

def test_extract_model_summary_primary(temp_dir):
    """Test extracting summary from primary model results."""
    # Create mock primary results
    mock_df = pd.DataFrame({
        "term": ["intercept", "news_exposure_z", "political_ideology", "interaction"],
        "coef": [0.1, 0.2, 0.3, 0.05],
        "std_err": [0.05, 0.05, 0.05, 0.02],
        "p-value": [0.001, 0.001, 0.001, 0.01]
    })
    primary_path = temp_dir / "primary_model_results.csv"
    mock_df.to_csv(primary_path, index=False)
    
    # Mock binary path as empty
    binary_path = temp_dir / "binary_model_results.csv"
    
    result = extract_model_summary(primary_path, binary_path)
    
    assert result is not None
    assert len(result) == 4
    assert result.iloc[0]["model_type"] == "primary"
    assert "coefficient" in result.columns

def test_extract_diagnostics(temp_dir):
    """Test extracting diagnostics from imputed data."""
    mock_imp = pd.DataFrame({
        "IAT_D_score": [0.1, 0.2, 0.3],
        "news_exposure_z": [0.1, 0.2, 0.3],
        "political_ideology": [0.1, 0.2, 0.3]
    })
    imp_path = temp_dir / "imputed_data.csv"
    mock_imp.to_csv(imp_path, index=False)
    
    result = extract_diagnostics(imp_path)
    
    assert result is not None
    assert not result.empty
    # Check for total_rows metric
    assert "metric" in result.columns
    assert "total_rows" in result["metric"].values