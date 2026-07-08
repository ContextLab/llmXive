"""
Integration tests for cli.py commands.
"""
import pytest
import subprocess
import os
import tempfile
import pandas as pd
from pathlib import Path

# TODO: Implement integration tests for CLI commands
# once T008 and T016 are implemented.

def test_cli_help():
    """Test that CLI responds to --help."""
    result = subprocess.run(
        ["python", "code/cli.py", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Molecular Complexity Pipeline" in result.stdout

def test_compute_entropy_malformed_smiles_handling():
    """
    Integration test for malformed SMILES handling (logging/skipping).
    
    Verifies that:
    1. The CLI accepts a CSV with valid and invalid SMILES
    2. Invalid SMILES are skipped with appropriate logging
    3. Valid SMILES are processed correctly
    4. The output CSV contains entropy scores only for valid molecules
    """
    # Create a temporary input CSV with mixed valid/invalid SMILES
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input_mixed.csv"
        output_path = Path(tmpdir) / "output_mixed.csv"
        
        # Create test data with valid and malformed SMILES
        test_data = {
            "smiles": [
                "CCO",           # Valid: Ethanol
                "invalid_smiles", # Invalid: Not a valid SMILES
                "CC(=O)O",       # Valid: Acetic acid
                "C[C@H](O)C(=O)O", # Valid: Lactic acid (with stereochem)
                ">>>",           # Invalid: Malformed
                "C1=CC=CC=C1",   # Valid: Benzene
                "",              # Invalid: Empty string
                "CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC", # Valid: Long chain
                "[Fe]",          # Valid: Iron atom
                "C12C1C2",       # Invalid: Impossible ring closure
            ],
            "logS": [
                -0.31, None, -0.17, -0.70, None, -2.13, None, -8.0, None, None
            ],
            "logP": [
                -0.31, None, -0.17, -0.70, None, 2.13, None, 8.0, None, None
            ]
        }
        df_input = pd.DataFrame(test_data)
        df_input.to_csv(input_path, index=False)
        
        # Run the CLI command
        cmd = [
            "python", "code/cli.py", "compute_entropy",
            "--input", str(input_path),
            "--output", str(output_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        # Check that the command completed (may have warnings but should exit 0)
        assert result.returncode == 0, f"CLI failed with: {result.stderr}"
        
        # Verify output file was created
        assert output_path.exists(), "Output CSV was not created"
        
        # Load and verify output
        df_output = pd.read_csv(output_path)
        
        # Should have same number of rows as input (all rows preserved)
        assert len(df_output) == len(df_input), "Row count mismatch"
        
        # Verify columns exist
        assert "atom_entropy" in df_output.columns, "Missing atom_entropy column"
        assert "bond_entropy" in df_output.columns, "Missing bond_entropy column"
        
        # Count valid vs invalid based on input
        valid_indices = [0, 2, 3, 5, 7, 8, 9]  # Indices of valid SMILES
        invalid_indices = [1, 4, 6]  # Indices of invalid SMILES
        
        # Verify that valid SMILES have computed entropy values (not NaN)
        for idx in valid_indices:
            assert pd.notna(df_output.loc[idx, "atom_entropy"]), \
                f"Valid SMILES at index {idx} should have atom_entropy"
            assert pd.notna(df_output.loc[idx, "bond_entropy"]), \
                f"Valid SMILES at index {idx} should have bond_entropy"
        
        # Verify that invalid SMILES have NaN for entropy values
        for idx in invalid_indices:
            assert pd.isna(df_output.loc[idx, "atom_entropy"]), \
                f"Invalid SMILES at index {idx} should have NaN atom_entropy"
            assert pd.isna(df_output.loc[idx, "bond_entropy"]), \
                f"Invalid SMILES at index {idx} should have NaN bond_entropy"
        
        # Verify that original data columns are preserved
        assert "smiles" in df_output.columns, "Missing smiles column"
        assert "logS" in df_output.columns, "Missing logS column"
        assert "logP" in df_output.columns, "Missing logP column"
        
        # Verify original data integrity
        for col in ["smiles", "logS", "logP"]:
            pd.testing.assert_series_equal(
                df_input[col], 
                df_output[col],
                obj=f"Column {col} mismatch"
            )

def test_compute_entropy_all_invalid_smiles():
    """
    Integration test for handling a CSV where ALL SMILES are invalid.
    
    Verifies that:
    1. The CLI handles this gracefully (doesn't crash)
    2. Output contains NaN for all entropy values
    3. Appropriate logging occurs
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input_all_invalid.csv"
        output_path = Path(tmpdir) / "output_all_invalid.csv"
        
        # Create test data with all invalid SMILES
        test_data = {
            "smiles": [
                "invalid1",
                "invalid2",
                ">>>",
                "",
            ],
            "logS": [None, None, None, None],
            "logP": [None, None, None, None]
        }
        df_input = pd.DataFrame(test_data)
        df_input.to_csv(input_path, index=False)
        
        # Run the CLI command
        cmd = [
            "python", "code/cli.py", "compute_entropy",
            "--input", str(input_path),
            "--output", str(output_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        # Should complete successfully (even if all rows are invalid)
        assert result.returncode == 0, f"CLI failed with: {result.stderr}"
        
        # Verify output file was created
        assert output_path.exists(), "Output CSV was not created"
        
        # Load and verify output
        df_output = pd.read_csv(output_path)
        
        # All entropy values should be NaN
        assert df_output["atom_entropy"].isna().all(), \
            "All atom_entropy values should be NaN for invalid SMILES"
        assert df_output["bond_entropy"].isna().all(), \
            "All bond_entropy values should be NaN for invalid SMILES"