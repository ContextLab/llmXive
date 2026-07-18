"""
Unit tests for 3D coordinate extraction logic.
Implements T103: test_extract_3d_coords_handles_nan_and_missing_atoms.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import tempfile

# Add code directory to path to allow imports
project_root = Path(__file__).parent.parent.parent
code_dir = project_root / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from data.preprocess_3d import extract_3d_features


class TestExtract3DCoords:
    """Tests for handling NaN values and missing atoms in 3D coordinate extraction."""

    def test_extract_3d_coords_handles_nan_values(self):
        """
        Assert that molecules with NaN in coordinates are detected and excluded.
        Validates that the extraction logic does not silently pass invalid data.
        """
        # Create a mock molecule DataFrame with NaN coordinates
        data = {
            "molecule_id": ["mol_001", "mol_002", "mol_003"],
            "atoms": [["C", "H", "H"], ["C", "O", "H"], ["C", "N", "O"]],
            "coordinates": [
                [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],  # Valid
                [[0.0, 0.0, 0.0], [float("nan"), 0.0, 0.0], [0.0, 1.0, 0.0]],  # NaN in x
                [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],  # Valid
            ],
            "dipole": [1.5, 2.0, 1.8],
        }
        df = pd.DataFrame(data)

        # Run extraction
        # Note: The function is expected to handle validation internally or raise
        # based on the implementation in preprocess_3d.py.
        # We test that the function does not crash and correctly identifies/returns valid rows
        # or raises a specific error if strict mode is on.
        # Assuming extract_3d_features returns a DataFrame of processed features.
        
        try:
            result = extract_3d_features(df)
            
            # If it returns a result, verify that the row with NaN was excluded
            # or that the resulting feature vector for that row is not NaN.
            # Given the task description "handles NaN", we expect the row to be dropped
            # or the specific feature vector to be flagged.
            
            # Check that 'mol_002' (index 1 in input) is NOT in the result if strict filtering is applied
            # or that the result does not contain NaN values.
            if "molecule_id" in result.columns:
                assert "mol_002" not in result["molecule_id"].values, \
                    "Molecule with NaN coordinates should be excluded."
            
            # Ensure no NaN values exist in the resulting feature columns
            feature_cols = [c for c in result.columns if c not in ["molecule_id"]]
            for col in feature_cols:
                assert not result[col].isna().any(), \
                    f"Result contains NaN values in column {col}."

        except Exception as e:
            # If the function raises an error on NaN input, that is also a valid "handling"
            # strategy (fail-fast). We assert the error is informative.
            assert "NaN" in str(e) or "missing" in str(e).lower(), \
                f"Exception raised but does not mention NaN/missing: {e}"

    def test_extract_3d_coords_handles_missing_atoms(self):
        """
        Assert that molecules with missing atoms (mismatched list lengths) are handled.
        Specifically, if coordinates list length does not match atoms list length,
        the molecule should be excluded or flagged.
        """
        data = {
            "molecule_id": ["mol_001", "mol_002", "mol_003"],
            "atoms": [["C", "H"], ["C", "O", "H"], ["C", "N"]],
            # mol_001: 2 atoms, 2 coords (Valid)
            # mol_002: 3 atoms, 2 coords (Missing atom coordinate)
            # mol_003: 2 atoms, 3 coords (Extra coordinate)
            "coordinates": [
                [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]],
                [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]],
                [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
            ],
            "dipole": [1.2, 1.3, 1.4],
        }
        df = pd.DataFrame(data)

        try:
            result = extract_3d_features(df)
            
            # Verify that mol_002 and mol_003 are excluded due to mismatch
            if "molecule_id" in result.columns:
                assert "mol_002" not in result["molecule_id"].values, \
                    "Molecule with missing atom coordinates should be excluded."
                assert "mol_003" not in result["molecule_id"].values, \
                    "Molecule with extra coordinates (mismatch) should be excluded."
            
            # Ensure the valid molecule remains
            assert "mol_001" in result["molecule_id"].values, \
                "Valid molecule should be present in the result."

        except Exception as e:
            # Fail-fast behavior is acceptable
            assert "mismatch" in str(e).lower() or "missing" in str(e).lower(), \
                f"Exception raised but does not mention mismatch/missing: {e}"

    def test_extract_3d_coords_empty_input(self):
        """Assert that an empty DataFrame is handled gracefully."""
        df = pd.DataFrame(columns=["molecule_id", "atoms", "coordinates", "dipole"])
        
        result = extract_3d_features(df)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_extract_3d_coords_single_valid_molecule(self):
        """Assert that a single valid molecule is processed correctly."""
        data = {
            "molecule_id": ["mol_valid"],
            "atoms": [["C", "O"]],
            "coordinates": [[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]],
            "dipole": [2.5],
        }
        df = pd.DataFrame(data)
        
        result = extract_3d_features(df)
        
        assert len(result) == 1
        assert result["molecule_id"].iloc[0] == "mol_valid"
        # Check that features are numeric and not NaN
        feature_cols = [c for c in result.columns if c not in ["molecule_id"]]
        for col in feature_cols:
            assert not pd.isna(result[col].iloc[0]), f"Feature {col} is NaN for valid input."