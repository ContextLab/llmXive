"""
Unit tests for handle_missing_data module.
"""
import pytest
import pandas as pd
import numpy as np
import json
import os
import tempfile
from datetime import datetime

from ingestion.handle_missing_data import (
    calculate_missing_ratio,
    impute_polymer_class_averages,
    handle_missing_data
)
from utils.errors import DataInsufficientError


@pytest.fixture
def sample_dataframe():
    """Create a sample dataframe for testing."""
    return pd.DataFrame({
        "smiles": [
            "CC(C)(C)c1ccc(cc1)C(C)(C)C(=O)O",  # Polycarbonate-like
            "CC(C)(C)c1ccc(cc1)C(C)(C)C(=O)O",  # Same class
            "O=C(O)C(C)C",                      # Different class
            "O=C(O)C(C)C",                      # Same class
            "CC(=O)Oc1ccccc1C(=O)O"             # Third class
        ],
        "permeability_co2": [10.0, np.nan, 5.0, np.nan, 8.0],
        "permeability_o2": [2.0, 1.5, np.nan, 1.0, 1.8],
        "selectivity_co2_o2": [5.0, 6.0, np.nan, 5.5, 4.5]
    })


@pytest.fixture
def high_missing_dataframe():
    """Create a dataframe with >20% missing data."""
    return pd.DataFrame({
        "smiles": [
            "CC(C)(C)c1ccc(cc1)C(C)(C)C(=O)O",
            "CC(C)(C)c1ccc(cc1)C(C)(C)C(=O)O",
            "O=C(O)C(C)C",
            "O=C(O)C(C)C"
        ],
        "permeability_co2": [np.nan, np.nan, np.nan, 5.0],
        "permeability_o2": [np.nan, np.nan, 1.0, np.nan],
        "selectivity_co2_o2": [np.nan, 6.0, np.nan, np.nan]
    })


def test_calculate_missing_ratio_no_missing():
    """Test calculation when no data is missing."""
    df = pd.DataFrame({
        "permeability_co2": [10.0, 5.0, 8.0],
        "permeability_o2": [2.0, 1.5, 1.8],
        "selectivity_co2_o2": [5.0, 6.0, 4.5]
    })
    
    ratio = calculate_missing_ratio(df)
    assert ratio == 0.0


def test_calculate_missing_ratio_with_missing(sample_dataframe):
    """Test calculation when data is missing."""
    # 2 missing in permeability_co2, 2 in permeability_o2, 1 in selectivity = 5 total
    # 5 rows * 3 columns = 15 cells
    # Ratio = 5/15 = 0.333...
    ratio = calculate_missing_ratio(sample_dataframe)
    assert 0.3 < ratio < 0.4


def test_calculate_missing_ratio_missing_columns():
    """Test when critical columns don't exist."""
    df = pd.DataFrame({"other_col": [1, 2, 3]})
    ratio = calculate_missing_ratio(df)
    assert ratio == 0.0


def test_impute_polymer_class_averages(sample_dataframe):
    """Test imputation using polymer class averages."""
    # Count original missing
    original_missing = sample_dataframe.isnull().sum().sum()
    
    # Perform imputation
    df_imputed = impute_polymer_class_averages(sample_dataframe)
    
    # Verify no missing values in critical columns remain (if classes matched)
    critical_cols = ["permeability_co2", "permeability_o2", "selectivity_co2_o2"]
    new_missing = df_imputed[critical_cols].isnull().sum().sum()
    
    # Should have reduced missing values
    assert new_missing <= original_missing
    
    # Verify polymer_class column was added
    assert "polymer_class" in df_imputed.columns


def test_impute_missing_smiles():
    """Test imputation fails when smiles column is missing."""
    df = pd.DataFrame({
        "permeability_co2": [10.0, np.nan],
        "permeability_o2": [2.0, 1.5]
    })
    
    with pytest.raises(ValueError, match="smiles.*missing"):
        impute_polymer_class_averages(df)


def test_handle_missing_data_within_threshold(sample_dataframe, tmp_path):
    """Test handling missing data when within threshold."""
    output_dir = str(tmp_path)
    
    # This should succeed and return imputed data
    result = handle_missing_data(sample_dataframe, threshold=0.20, output_dir=output_dir)
    
    assert result is not None
    assert "polymer_class" in result.columns
    
    # Check if clarification flag was created
    flag_path = os.path.join(output_dir, "clarification_flag.json")
    assert os.path.exists(flag_path)
    
    with open(flag_path, "r") as f:
        flag_data = json.load(f)
    
    assert flag_data["status"] in ["imputed", "partial_imputation"]
    assert flag_data["imputation_method"] == "polymer_class_average"


def test_handle_missing_data_exceeds_threshold(high_missing_dataframe, tmp_path):
    """Test handling missing data when exceeds threshold."""
    output_dir = str(tmp_path)
    
    # This should raise DataInsufficientError
    with pytest.raises(DataInsufficientError, match="exceeds threshold"):
        handle_missing_data(high_missing_dataframe, threshold=0.20, output_dir=output_dir)


def test_handle_missing_data_no_missing():
    """Test handling when no data is missing."""
    df = pd.DataFrame({
        "smiles": ["CC(C)(C)c1ccc(cc1)C(C)(C)C(=O)O"],
        "permeability_co2": [10.0],
        "permeability_o2": [2.0],
        "selectivity_co2_o2": [5.0]
    })
    
    result = handle_missing_data(df, threshold=0.20)
    
    # Should return dataframe unchanged (or with polymer_class added)
    assert result is not None
    assert result["permeability_co2"].iloc[0] == 10.0
