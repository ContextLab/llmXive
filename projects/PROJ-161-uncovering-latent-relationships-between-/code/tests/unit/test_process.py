"""
Unit tests for src.data.process module (Task T014).

Tests:
1. Canonicalization of valid and invalid SMILES.
2. Descriptor calculation for valid molecules.
3. Exclusion of invalid compounds.
4. Pipeline integration on a small mock dataset.
"""
import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from rdkit import Chem
from src.data.process import (
    canonicalize_smiles,
    calculate_descriptors,
    process_compounds,
    run_process_pipeline
)

class TestCanonicalizeSmiles:
    def test_valid_smiles(self):
        """Test canonicalization of a valid SMILES string."""
        smiles = "CCO"  # Ethanol
        result = canonicalize_smiles(smiles)
        assert result is not None
        assert result == "CCO"  # Ethanol is already canonical usually

    def test_complex_smiles(self):
        """Test canonicalization of a more complex SMILES."""
        # Aspirin
        smiles = "CC(=O)Oc1ccccc1C(=O)O"
        result = canonicalize_smiles(smiles)
        assert result is not None
        assert isinstance(result, str)
        # Verify it can be parsed back
        mol = Chem.MolFromSmiles(result)
        assert mol is not None

    def test_invalid_smiles(self):
        """Test handling of invalid SMILES."""
        invalid_smiles = "invalid_smiles_string"
        result = canonicalize_smiles(invalid_smiles)
        assert result is None

    def test_empty_string(self):
        """Test handling of empty string."""
        result = canonicalize_smiles("")
        assert result is None

    def test_none_input(self):
        """Test handling of None input."""
        result = canonicalize_smiles(None)
        assert result is None

class TestCalculateDescriptors:
    def test_basic_descriptors(self):
        """Test that basic descriptors are calculated for a valid molecule."""
        mol = Chem.MolFromSmiles("CCO")
        descriptors = calculate_descriptors(mol)
        
        assert "MolWt" in descriptors
        assert "LogP" in descriptors or "MolLogP" in descriptors # RDKit has both, check common ones
        
        # Check that values are numeric
        for name, val in descriptors.items():
            assert isinstance(val, (int, float, np.floating, np.integer))
            # Allow NaN but not strings or objects
            assert not isinstance(val, str)

    def test_all_desc_list(self):
        """Verify that all standard descriptors are present in output."""
        from rdkit.Chem import Descriptors
        expected_names = {name for name, _ in Descriptors.descList}
        
        mol = Chem.MolFromSmiles("CCO")
        descriptors = calculate_descriptors(mol)
        
        assert set(descriptors.keys()) == expected_names

class TestProcessCompounds:
    @pytest.fixture
    def mock_df(self):
        """Create a mock DataFrame with valid and invalid SMILES."""
        return pd.DataFrame({
            "inchikey": ["KEY1", "KEY2", "KEY3", "KEY4"],
            "smiles": ["CCO", "invalid", "CC(=O)O", "C1=CC=CC=C1"], # KEY2 is invalid
            "resistance_freq": [0.1, 0.5, 0.0, 0.9]
        })

    def test_excludes_invalid(self, mock_df):
        """Test that invalid SMILES are excluded."""
        processed_df, total, valid = process_compounds(mock_df)
        
        assert total == 4
        assert valid == 3
        assert len(processed_df) == 3
        
        # Check that the invalid row (KEY2) is not in the result
        assert "KEY2" not in processed_df["inchikey"].values

    def test_preserves_valid_data(self, mock_df):
        """Test that valid data is preserved and descriptors added."""
        processed_df, total, valid = process_compounds(mock_df)
        
        # Check for a known valid row
        row = processed_df[processed_df["inchikey"] == "KEY1"].iloc[0]
        assert row["smiles"] == "CCO" # Canonicalized
        assert "MolWt" in row
        assert row["resistance_freq"] == 0.1

    def test_empty_input(self):
        """Test handling of empty DataFrame."""
        df = pd.DataFrame(columns=["inchikey", "smiles"])
        processed_df, total, valid = process_compounds(df)
        assert total == 0
        assert valid == 0
        assert processed_df.empty

class TestRunProcessPipeline:
    def test_full_pipeline(self):
        """Test the full pipeline from file to file."""
        # Create temp input
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f_in:
            f_in.write("inchikey,smiles,resistance_freq\n")
            f_in.write("KEY1,CCO,0.1\n")
            f_in.write("KEY2,invalid,0.2\n")
            f_in.write("KEY3,CC(=O)O,0.3\n")
            input_path = f_in.name

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "processed.csv")
            
            run_process_pipeline(input_path, output_path)
            
            assert os.path.exists(output_path)
            
            df_out = pd.read_csv(output_path)
            
            # Should have 2 rows (KEY1 and KEY3)
            assert len(df_out) == 2
            assert "MolWt" in df_out.columns
            assert "KEY2" not in df_out["inchikey"].values

        # Cleanup
        os.unlink(input_path)