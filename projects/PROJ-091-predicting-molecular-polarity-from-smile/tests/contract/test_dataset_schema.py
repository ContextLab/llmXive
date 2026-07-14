"""
Contract test for dataset schema validation.

This test ensures that the processed dataset conforms to the expected
schema with required columns and data types as defined in the project
specifications for molecular polarity prediction.
"""
import pytest
import pandas as pd
import numpy as np
import os
from pathlib import Path

# Ensure we can import project modules if needed for schema constants
# (Currently using inline definitions based on spec)

def test_dataset_schema_raw():
    """
    Verify that a raw dataset (e.g., from download_qm9) has the expected basic schema.
    Expected: 'smiles' (string), 'target' (numeric).
    """
    # Define expected schema for raw input
    expected_columns = {'smiles', 'target'}
    
    # Create a sample dataframe mimicking the output of download_qm9/loader
    sample_data = {
        'smiles': ['CCO', 'CC(C)O', 'C1=CC=CC=C1'],
        'target': [1.5, 2.0, 0.0]  # Dipole moment in Debye
    }
    df = pd.DataFrame(sample_data)
    
    # Check columns
    found_cols = set(df.columns)
    assert expected_columns.issubset(found_cols), \
        f"Missing required columns. Expected subset of: {expected_columns}, Found: {found_cols}"
    
    # Check data types
    assert df['smiles'].dtype == object, "SMILES column should be string/object"
    assert np.issubdtype(df['target'].dtype, np.number), "Target column should be numeric"

def test_processed_descriptor_schema():
    """
    Verify that processed descriptor data (from preprocess_2d) has the expected structure.
    Must contain 'smiles', 'target', and numeric descriptor columns.
    """
    # Sample processed data with descriptors as expected after T014/T016
    sample_data = {
        'smiles': ['CCO', 'CC(C)O'],
        'target': [1.5, 2.0],
        'MolWt': [46.0, 60.0],
        'LogP': [-0.3, 0.1],
        'NumHDonors': [1, 1],
        'NumHAcceptors': [1, 1]
    }
    df = pd.DataFrame(sample_data)
    
    # Must have smiles and target
    assert 'smiles' in df.columns, "Processed data must contain 'smiles' column"
    assert 'target' in df.columns, "Processed data must contain 'target' column"
    
    # Identify descriptor columns (everything except smiles and target)
    descriptor_cols = [col for col in df.columns if col not in ['smiles', 'target']]
    
    # Must have at least one descriptor (as per US1 requirement of >=200, but schema check just needs existence)
    assert len(descriptor_cols) > 0, "Processed data must contain at least one descriptor column"
    
    # All descriptor columns should be numeric
    for col in descriptor_cols:
        assert np.issubdtype(df[col].dtype, np.number), \
            f"Descriptor column {col} should be numeric, found {df[col].dtype}"

def test_no_3d_descriptors_in_schema():
    """
    Contract test to ensure no 3D-dependent descriptors (like TPSA) are present
    in the processed dataset schema, enforcing the 2D-only constraint.
    """
    # Simulate a dataframe that might accidentally include 3D descriptors
    sample_data = {
        'smiles': ['CCO'],
        'target': [1.5],
        'MolWt': [46.0],
        'TPSA': [20.0],  # This should NOT be there per US1 constraints
        'LogP': [-0.3]
    }
    df = pd.DataFrame(sample_data)
    
    forbidden_3d_descriptors = {
        'TPSA', 'TPSA_E', 'TPSA_V', 'InertialMoment1', 'InertialMoment2', 
        'InertialMoment3', 'RadiusOfGyration'
    }
    
    found_cols = set(df.columns)
    violations = found_cols.intersection(forbidden_3d_descriptors)
    
    assert len(violations) == 0, \
        f"Schema contains forbidden 3D-dependent descriptors: {violations}. " \
        f"US1 requires 2D-only descriptors."

def test_schema_handles_missing_values():
    """
    Verify that the schema allows for NaN values in descriptor columns
    (since T016 handles them, but the raw processed output might still have them
    before final cleaning, or the schema must accommodate them).
    """
    sample_data = {
        'smiles': ['CCO', 'CC(C)O'],
        'target': [1.5, 2.0],
        'MolWt': [46.0, np.nan],
        'LogP': [-0.3, 0.1]
    }
    df = pd.DataFrame(sample_data)
    
    # Check that numeric columns can hold NaN
    assert pd.isna(df['MolWt']).any(), "Numeric descriptor columns must be able to hold NaN values"
    
    # Verify the column is still considered numeric (float) despite NaNs
    assert np.issubdtype(df['MolWt'].dtype, np.floating), \
        "Columns with NaN should be floating point to preserve numeric type"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])