"""
Contract test for molecule schema.
Validates that molecules with missing 3D coordinates are flagged and excluded.
"""

import pytest
from pathlib import Path
import sys
import os

# Add project root to path if not already present
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root / "code") not in sys.path:
    sys.path.insert(0, str(project_root / "code"))

from data.handle_missing_coords import handle_missing_coordinates
import pandas as pd
from datetime import datetime


def test_molecule_schema_validates_missing_coordinates(tmp_path):
    """
    Assert that molecules with missing 3D coordinates are flagged and excluded.
    
    This test creates a synthetic dataset with valid and invalid molecules,
    runs the missing coordinate handler, and verifies that:
    1. The output report contains excluded molecules with reason 'missing_3d'
    2. Valid molecules are not excluded
    3. The exclusion timestamp is recorded
    """
    
    # Create a test dataset with mixed valid/invalid coordinates
    # Valid molecule
    valid_molecule = {
        "molecule_id": "mol_001",
        "atoms": ["C", "H", "H", "H", "H"],
        "coordinates": [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [-0.5, -0.5, -0.5]
        ],
        "dipole": 0.0
    }
    
    # Molecule with missing coordinates (None values)
    missing_coords_molecule = {
        "molecule_id": "mol_002",
        "atoms": ["O", "H", "H"],
        "coordinates": None,  # Missing 3D coordinates
        "dipole": 1.85
    }
    
    # Molecule with NaN coordinates
    nan_coords_molecule = {
        "molecule_id": "mol_003",
        "atoms": ["N", "H", "H", "H"],
        "coordinates": [
            [0.0, 0.0, 0.0],
            [float('nan'), 0.0, 0.0],  # Invalid coordinate
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0]
        ],
        "dipole": 1.47
    }
    
    # Molecule with empty coordinates list
    empty_coords_molecule = {
        "molecule_id": "mol_004",
        "atoms": ["C", "O"],
        "coordinates": [],  # Empty coordinates
        "dipole": 2.3
    }
    
    # Create test DataFrame
    test_data = [valid_molecule, missing_coords_molecule, nan_coords_molecule, empty_coords_molecule]
    df = pd.DataFrame(test_data)
    
    # Define output paths
    output_csv = tmp_path / "excluded_molecules.csv"
    
    # Run the missing coordinate handler
    handle_missing_coordinates(
        molecules_df=df,
        output_csv=str(output_csv)
    )
    
    # Verify the output file exists
    assert output_csv.exists(), "Exclusion report CSV was not created"
    
    # Read the exclusion report
    excluded_df = pd.read_csv(output_csv)
    
    # Verify that molecules with missing/invalid coordinates were flagged
    assert len(excluded_df) > 0, "No molecules were flagged for exclusion"
    
    # Check that mol_002 (None coordinates) was excluded
    mol_002_excluded = excluded_df[excluded_df['molecule_id'] == 'mol_002']
    assert len(mol_002_excluded) == 1, "Molecule with None coordinates was not excluded"
    assert mol_002_excluded.iloc[0]['exclusion_reason'] == 'missing_3d', \
        f"Expected exclusion reason 'missing_3d', got '{mol_002_excluded.iloc[0]['exclusion_reason']}'"
    
    # Check that mol_003 (NaN coordinates) was excluded
    mol_003_excluded = excluded_df[excluded_df['molecule_id'] == 'mol_003']
    assert len(mol_003_excluded) == 1, "Molecule with NaN coordinates was not excluded"
    assert mol_003_excluded.iloc[0]['exclusion_reason'] == 'missing_3d', \
        f"Expected exclusion reason 'missing_3d', got '{mol_003_excluded.iloc[0]['exclusion_reason']}'"
    
    # Check that mol_004 (empty coordinates) was excluded
    mol_004_excluded = excluded_df[excluded_df['molecule_id'] == 'mol_004']
    assert len(mol_004_excluded) == 1, "Molecule with empty coordinates was not excluded"
    assert mol_004_excluded.iloc[0]['exclusion_reason'] == 'missing_3d', \
        f"Expected exclusion reason 'missing_3d', got '{mol_004_excluded.iloc[0]['exclusion_reason']}'"
    
    # Verify that valid molecule (mol_001) was NOT excluded
    mol_001_excluded = excluded_df[excluded_df['molecule_id'] == 'mol_001']
    assert len(mol_001_excluded) == 0, "Valid molecule was incorrectly excluded"
    
    # Verify exclusion_timestamp column exists and is populated
    assert 'exclusion_timestamp' in excluded_df.columns, "Missing 'exclusion_timestamp' column"
    assert all(pd.notna(excluded_df['exclusion_timestamp'])), "Some exclusion_timestamp values are missing"
    
    # Verify the format of exclusion_reason (should be enum: 'missing_3d' or 'invalid_structure')
    valid_reasons = ['missing_3d', 'invalid_structure']
    for reason in excluded_df['exclusion_reason']:
        assert reason in valid_reasons, f"Invalid exclusion reason: {reason}"
    
    print(f"✓ Test passed: {len(excluded_df)} molecules correctly excluded for missing coordinates")
    print(f"  - Excluded molecules: {list(excluded_df['molecule_id'])}")
    print(f"  - Exclusion reasons: {list(excluded_df['exclusion_reason'])}")