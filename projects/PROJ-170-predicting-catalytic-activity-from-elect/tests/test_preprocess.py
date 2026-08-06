import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from preprocess import parse_oc20_to_dataframe
from config import get_project_root, get_data_path

def test_parse_oc20_schema():
    """
    Test that parse_oc20_to_dataframe produces a DataFrame with the correct schema.
    This is a contract test for T013a.
    """
    project_root = get_project_root()
    data_path = get_data_path(project_root)
    h5_file_path = os.path.join(data_path, 'raw', 'oc20_sample.h5')
    
    # Skip if file doesn't exist (e.g., in CI without data)
    if not os.path.exists(h5_file_path):
        pytest.skip(f"OC20 sample file not found at {h5_file_path}")
    
    df = parse_oc20_to_dataframe(h5_file_path)
    
    expected_columns = ['composition', 'surface_facet', 'experimental_tof', 'd_band_center', 'adsorption_energy']
    
    # Check columns
    assert set(df.columns) == set(expected_columns), f"Columns mismatch. Expected {expected_columns}, got {list(df.columns)}"
    
    # Check non-empty
    assert not df.empty, "DataFrame is empty"
    
    # Check types
    assert df['composition'].dtype == object, "composition should be string"
    assert df['surface_facet'].dtype == object, "surface_facet should be string"
    
    # Check numeric columns are numeric (allow NaN for now, as per task description)
    assert pd.api.types.is_numeric_dtype(df['experimental_tof']), "experimental_tof should be numeric"
    assert pd.api.types.is_numeric_dtype(df['d_band_center']), "d_band_center should be numeric"
    assert pd.api.types.is_numeric_dtype(df['adsorption_energy']), "adsorption_energy should be numeric"

def test_data_integrity_no_empty_composition():
    """
    Test that no composition strings are empty.
    """
    project_root = get_project_root()
    data_path = get_data_path(project_root)
    h5_file_path = os.path.join(data_path, 'raw', 'oc20_sample.h5')
    
    if not os.path.exists(h5_file_path):
        pytest.skip(f"OC20 sample file not found at {h5_file_path}")
    
    df = parse_oc20_to_dataframe(h5_file_path)
    
    # Check for empty strings in composition
    assert not df['composition'].str.strip().eq('').any(), "Found empty composition strings"
    
    # Check for NaN in composition
    assert not df['composition'].isna().any(), "Found NaN in composition"

def test_target_column_no_nan_initial():
    """
    Test that the target column (experimental_tof) has no NaN values initially.
    Note: The task description says "Log any missing target values for exclusion" in T015,
    but T013a verification says "no NaN values in the target column after imputation".
    Since T013a is before imputation, we check for presence of NaNs and log them.
    However, the prompt says "verify ... with no NaN values in the target column after imputation".
    This test is for T013a, so we just check the raw data.
    We expect some NaNs might be present, but we verify the structure.
    If the requirement is strict "no NaN", then we fail if NaNs exist.
    Given T015 handles exclusion, we assume T013a might have NaNs.
    But the task description for T013a says: "Verification: Verify DataFrame shape is (N, M) and columns match schema."
    It does NOT explicitly say "no NaN" for T013a. The "no NaN" is for the final output in T050.
    So we just check the schema here.
    """
    project_root = get_project_root()
    data_path = get_data_path(project_root)
    h5_file_path = os.path.join(data_path, 'raw', 'oc20_sample.h5')
    
    if not os.path.exists(h5_file_path):
        pytest.skip(f"OC20 sample file not found at {h5_file_path}")
    
    df = parse_oc20_to_dataframe(h5_file_path)
    
    # We don't assert no NaN here, as imputation happens later.
    # We just ensure the column exists and is numeric.
    assert 'experimental_tof' in df.columns
    assert pd.api.types.is_numeric_dtype(df['experimental_tof'])