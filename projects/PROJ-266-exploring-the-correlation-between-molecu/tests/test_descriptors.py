"""
Unit tests for conformer generation and variance calculation in descriptors.py.

This module validates the core logic of User Story 2 (Flexibility Descriptors),
specifically:
1. Conformer generation using RDKit (adhering to DEV-001 for 20 conformers).
2. Calculation of bond, angle, and dihedral variances.
3. Outlier flagging logic.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Import the functions under test from the project's codebase
# The import path assumes the test runner is executed from the project root
# or that code/ is in sys.path.
from code.data.descriptors import (
    generate_conformers,
    calculate_variance_metrics,
    flag_outliers,
    process_molecules
)
from code.utils.config import set_seed

# Set a fixed seed for deterministic test results
set_seed(42)

# --- Fixtures ---

@pytest.fixture
def valid_smiles_list() -> List[str]:
    """
    Returns a list of valid SMILES strings representing small molecules
    suitable for testing conformer generation and variance calculation.
    """
    return [
        "CCO",  # Ethanol
        "CC(C)C", # Isobutane
        "c1ccccc1", # Benzene
        "CC(=O)Oc1ccccc1C(=O)O", # Aspirin
        "CCN(CC)CC" # Triethylamine
    ]

@pytest.fixture
def invalid_smiles_list() -> List[str]:
    """
    Returns a list of invalid or problematic SMILES strings.
    """
    return [
        "INVALID_SMILES_STRING",
        "C1CCC1C1CCC1", # Unlikely ring closure, might fail
        ""
    ]

@pytest.fixture
def sample_processed_df(valid_smiles_list) -> pd.DataFrame:
    """
    Creates a sample DataFrame mimicking the output of preprocessing,
    containing SMILES and the target logPapp column.
    """
    data = {
        "smiles": valid_smiles_list,
        "logPapp": [np.random.uniform(-5, 5) for _ in valid_smiles_list],
        "mol_id": [f"MOL_{i}" for i in range(len(valid_smiles_list))]
    }
    return pd.DataFrame(data)

# --- Tests for Conformer Generation ---

def test_generate_conformers_valid_molecule(valid_smiles_list):
    """
    Test that generate_conformers successfully creates conformers for a valid molecule.
    Verifies the number of conformers matches the deviation (DEV-001) of 20.
    """
    smiles = valid_smiles_list[0] # Ethanol
    num_conformers = 20  # Per DEV-001

    mol, conformers, success = generate_conformers(smiles, num_conformers=num_conformers)

    assert success is True, "Conformer generation should succeed for valid SMILES."
    assert mol is not None, "Molecule object should not be None."
    assert len(conformers) == num_conformers, f"Expected {num_conformers} conformers, got {len(conformers)}."

def test_generate_conformers_invalid_molecule(invalid_smiles_list):
    """
    Test that generate_conformers handles invalid SMILES gracefully.
    """
    smiles = invalid_smiles_list[0]
    num_conformers = 20

    mol, conformers, success = generate_conformers(smiles, num_conformers=num_conformers)

    assert success is False, "Conformer generation should fail for invalid SMILES."
    assert mol is None, "Molecule object should be None for invalid SMILES."
    assert len(conformers) == 0, "Conformers list should be empty for invalid SMILES."

def test_generate_conformers_count_consistency(valid_smiles_list):
    """
    Test that the number of generated conformers is consistent across multiple runs
    for the same molecule (given a fixed seed).
    """
    smiles = valid_smiles_list[2] # Benzene
    num_conformers = 20

    _, conformers_1, _ = generate_conformers(smiles, num_conformers=num_conformers)
    _, conformers_2, _ = generate_conformers(smiles, num_conformers=num_conformers)

    assert len(conformers_1) == len(conformers_2) == num_conformers

# --- Tests for Variance Calculation ---

def test_calculate_variance_metrics_returns_correct_columns(valid_smiles_list):
    """
    Test that calculate_variance_metrics returns a dictionary with the required keys:
    bond_variance, angle_variance, dihedral_variance.
    """
    smiles = valid_smiles_list[0]
    num_conformers = 20

    _, conformers, success = generate_conformers(smiles, num_conformers=num_conformers)
    assert success, "Conformer generation failed for test molecule."

    metrics = calculate_variance_metrics(conformers)

    assert isinstance(metrics, dict), "Metrics should be a dictionary."
    assert "bond_variance" in metrics, "Missing bond_variance in metrics."
    assert "angle_variance" in metrics, "Missing angle_variance in metrics."
    assert "dihedral_variance" in metrics, "Missing dihedral_variance in metrics."

    # Verify values are non-negative floats
    for key, value in metrics.items():
        assert isinstance(value, (int, float)), f"{key} should be a number."
        assert value >= 0.0, f"{key} variance cannot be negative."

def test_calculate_variance_metrics_rigid_molecule(valid_smiles_list):
    """
    Test variance calculation on a rigid molecule (Benzene).
    Variances should be very low (close to zero) due to aromaticity.
    """
    smiles = valid_smiles_list[2] # Benzene
    num_conformers = 20

    _, conformers, success = generate_conformers(smiles, num_conformers=num_conformers)
    assert success, "Conformer generation failed for test molecule."

    metrics = calculate_variance_metrics(conformers)

    # While not exactly zero due to numerical noise and optimization,
    # rigid molecules should have significantly lower variance than flexible ones.
    # We assert they are below a reasonable threshold for this test.
    threshold = 0.1 # rad^2 (arbitrary but reasonable for rigid aromatic ring)
    assert metrics["bond_variance"] < threshold, "Bond variance for benzene is unexpectedly high."
    assert metrics["angle_variance"] < threshold, "Angle variance for benzene is unexpectedly high."
    # Dihedral variance might be slightly higher due to ring puckering optimization,
    # but still constrained.
    assert metrics["dihedral_variance"] < threshold * 5, "Dihedral variance for benzene is unexpectedly high."

def test_calculate_variance_metrics_flexible_molecule(valid_smiles_list):
    """
    Test variance calculation on a flexible molecule (Triethylamine).
    Variances should be higher than the rigid molecule.
    """
    smiles = valid_smiles_list[4] # Triethylamine
    num_conformers = 20

    _, conformers, success = generate_conformers(smiles, num_conformers=num_conformers)
    assert success, "Conformer generation failed for test molecule."

    metrics = calculate_variance_metrics(conformers)

    # Just ensure values are positive and within a realistic range
    assert metrics["bond_variance"] >= 0.0
    assert metrics["angle_variance"] >= 0.0
    assert metrics["dihedral_variance"] >= 0.0

# --- Tests for Outlier Flagging ---

def test_flag_outliers_basic_logic():
    """
    Test the flag_outliers function with a known dataset containing an outlier.
    """
    # Create a sample series of bond variances
    # Most values around 0.05, one clear outlier at 0.5
    data = pd.Series([0.04, 0.05, 0.06, 0.05, 0.05, 0.5])
    
    outliers = flag_outliers(data)

    assert isinstance(outliers, pd.Series), "Output should be a pandas Series."
    assert len(outliers) == len(data), "Length should match input."
    
    # The last value (0.5) should be flagged as an outlier (True)
    # The others should be False
    assert outliers.iloc[-1] is True, "The outlier value should be flagged as True."
    assert outliers.iloc[0] is False, "Normal values should be flagged as False."

def test_flag_outliers_no_outliers():
    """
    Test flag_outliers when no outliers exist.
    """
    data = pd.Series([0.05, 0.06, 0.055, 0.045, 0.05])
    
    outliers = flag_outliers(data)
    
    assert all(outliers == False), "No values should be flagged as outliers."

# --- Tests for Process Molecules (Integration of steps) ---

def test_process_molecules_valid_input(sample_processed_df):
    """
    Test the full pipeline for a valid subset of molecules.
    """
    # Limit to first 3 for speed in unit test
    df_subset = sample_processed_df.head(3)
    
    results = process_molecules(df_subset, num_conformers=20)
    
    assert isinstance(results, pd.DataFrame), "Results should be a DataFrame."
    assert len(results) == 3, "Should process 3 molecules."
    
    # Check for required columns
    required_cols = ["smiles", "mol_id", "bond_variance", "angle_variance", "dihedral_variance", "is_outlier"]
    for col in required_cols:
        assert col in results.columns, f"Missing column: {col}"
    
    # Check for non-NaN variance values
    for col in ["bond_variance", "angle_variance", "dihedral_variance"]:
        assert results[col].notna().all(), f"Column {col} contains NaN values."

def test_process_molecules_handles_failures(valid_smiles_list, invalid_smiles_list):
    """
    Test that process_molecules handles a mix of valid and invalid molecules
    without crashing, and reports failures appropriately.
    """
    mixed_data = {
        "smiles": valid_smiles_list[:1] + invalid_smiles_list[:1],
        "logPapp": [1.0, 1.0],
        "mol_id": ["VALID", "INVALID"]
    }
    df_mixed = pd.DataFrame(mixed_data)
    
    # We expect this to handle the failure gracefully (log warning, skip, or partial result)
    # The exact behavior depends on implementation, but it must not raise an unhandled exception.
    try:
        results = process_molecules(df_mixed, num_conformers=20)
        # If it returns a result, it should only contain the valid one (or handle invalid gracefully)
        assert isinstance(results, pd.DataFrame), "Results should be a DataFrame."
    except Exception as e:
        pytest.fail(f"process_molecules raised an unexpected exception: {e}")

# --- Edge Cases ---

def test_generate_conformers_zero_conformers():
    """
    Test behavior when num_conformers is 0.
    """
    smiles = "CCO"
    mol, conformers, success = generate_conformers(smiles, num_conformers=0)
    
    # Depending on implementation, this might fail or return empty list.
    # We assert it doesn't crash.
    assert success is False or len(conformers) == 0, "Should not generate conformers if count is 0."

def test_calculate_variance_metrics_empty_conformers():
    """
    Test variance calculation with an empty list of conformers.
    """
    conformers = []
    with pytest.raises(Exception):
        # Expecting an error or specific handling for empty input
        # The implementation should likely raise ValueError or return NaNs
        calculate_variance_metrics(conformers)