import pytest
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
from preprocess import generate_morgan_fingerprint, impute_descriptors_knn

def test_generate_morgan_fingerprint_valid():
    """Test fingerprint generation for valid SMILES."""
    smiles = "CCO"  # Ethanol
    fp = generate_morgan_fingerprint(smiles, radius=2, n_bits=2048)
    assert len(fp) == 2048
    assert fp.dtype == np.float32
    assert np.any(fp > 0)  # Should have some bits set

def test_generate_morgan_fingerprint_invalid():
    """Test fingerprint generation for invalid SMILES."""
    smiles = "invalid_smiles_string"
    fp = generate_morgan_fingerprint(smiles, radius=2, n_bits=2048)
    assert len(fp) == 2048
    assert np.all(fp == 0)  # Should be all zeros

def test_impute_descriptors_knn_insufficient_neighbors():
    """Test that rows with insufficient neighbors are flagged and excluded."""
    # Create a dataset with 4 rows, all with missing values in desc1 for the last one.
    # k=5. Total rows = 4.
    data_small = {
        'smiles': ['CCO', 'CCO', 'CCO', 'CCO'],
        'desc1': [1.0, 2.0, 3.0, np.nan],
        'desc2': [5.0, 6.0, 7.0, 8.0]
    }
    df_small = pd.DataFrame(data_small)
    
    # k=5, but only 4 rows.
    # The imputer should fail or leave NaN for the last row, triggering exclusion.
    imputed_df, exclusions = impute_descriptors_knn(df_small, k=5)
    
    # The row with NaN should be excluded if k neighbors are not found.
    # Since we have 4 rows and k=5, the last row cannot find 5 neighbors.
    assert len(exclusions) > 0, "Expected exclusions when k > number of rows"
    # Verify that the imputed dataframe does not contain the excluded row's NaN
    # or that the NaN count in the specific column is 0 if the row was removed.
    # If the row was removed, the length of the dataframe will be 3.
    assert len(imputed_df) < len(df_small), "Expected row exclusion"

def test_impute_descriptors_knn_success():
    """Test successful imputation when enough neighbors exist."""
    data = {
        'smiles': ['CCO'] * 10,
        'desc1': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, np.nan],
        'desc2': [10.0] * 10
    }
    df = pd.DataFrame(data)
    
    imputed_df, exclusions = impute_descriptors_knn(df, k=5)
    
    assert len(exclusions) == 0, "No exclusions expected with sufficient neighbors"
    assert imputed_df['desc1'].isnull().sum() == 0, "All NaNs should be imputed"
    assert len(imputed_df) == 10

def test_impute_descriptors_knn_edge_case_exact_neighbors():
    """Test imputation when exactly k neighbors are available."""
    # Create a dataset with exactly k+1 rows where one has a missing value.
    # k=3. Total rows = 4.
    data = {
        'smiles': ['CCO'] * 4,
        'desc1': [1.0, 2.0, 3.0, np.nan],
        'desc2': [5.0, 6.0, 7.0, 8.0]
    }
    df = pd.DataFrame(data)
    
    imputed_df, exclusions = impute_descriptors_knn(df, k=3)
    
    # Should succeed because we have exactly 3 neighbors for the missing row.
    assert len(exclusions) == 0, "No exclusions expected when exactly k neighbors exist"
    assert imputed_df['desc1'].isnull().sum() == 0, "All NaNs should be imputed"
    assert len(imputed_df) == 4

def test_impute_descriptors_knn_all_nan_descriptors():
    """Test behavior when a row has all descriptor values as NaN."""
    data = {
        'smiles': ['CCO', 'CCO', 'CCO'],
        'desc1': [1.0, 2.0, np.nan],
        'desc2': [np.nan, np.nan, np.nan] # Last row has all NaN descriptors
    }
    df = pd.DataFrame(data)
    
    imputed_df, exclusions = impute_descriptors_knn(df, k=2)
    
    # The last row has no valid features to compute distance, so it should be excluded.
    assert len(exclusions) > 0, "Expected exclusion for row with all NaN descriptors"
    # Verify the imputed dataframe doesn't have the problematic row
    assert len(imputed_df) < len(df)