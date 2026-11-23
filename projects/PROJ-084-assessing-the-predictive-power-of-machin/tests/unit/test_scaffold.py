"""
Unit tests for the scaffold generation module.
"""
import pytest
import pandas as pd
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold

from preprocessing.scaffold import get_murcko_scaffold, generate_scaffold_groups


class TestMurckoScaffoldGeneration:
    """Tests for the get_murcko_scaffold function."""

    def test_simple_benzene_scaffold(self):
        """Test that a benzene molecule returns the correct scaffold."""
        smiles = "c1ccccc1"
        scaffold = get_murcko_scaffold(smiles)
        # Benzene scaffold is just benzene
        assert scaffold is not None
        assert "c1ccccc1" in scaffold or "C1=CC=CC=C1" in scaffold

    def test_reaction_scaffold(self):
        """Test scaffold generation for a simple reaction."""
        # Reactant: Toluene, Product: Benzyl bromide (simplified)
        # Reaction: Cc1ccccc1>>Brc1ccccc1
        smiles = "Cc1ccccc1>>Brc1ccccc1"
        scaffold = get_murcko_scaffold(smiles)
        assert scaffold is not None
        # The scaffold should be the benzene ring
        assert "c1ccccc1" in scaffold or "C1=CC=CC=C1" in scaffold

    def test_complex_molecule_scaffold(self):
        """Test scaffold generation for a molecule with side chains."""
        # Aspirin-like structure
        smiles = "CC(=O)Oc1ccccc1C(=O)O"
        scaffold = get_murcko_scaffold(smiles)
        assert scaffold is not None
        # Should contain the benzene ring
        assert "c1ccccc1" in scaffold or "C1=CC=CC=C1" in scaffold

    def test_invalid_smiles_returns_none(self):
        """Test that invalid SMILES returns None."""
        assert get_murcko_scaffold("invalid_smiles") is None
        assert get_murcko_scaffold("") is None
        assert get_murcko_scaffold(None) is None

    def test_reaction_without_rings(self):
        """Test reaction where no rings are present (no scaffold)."""
        # Methane + Chlorine -> Chloromethane + HCl
        smiles = "C.Cl>>CCl.CC" # Simplified, no rings
        scaffold = get_murcko_scaffold(smiles)
        # Murcko scaffold for acyclic molecules is usually empty or None
        # depending on RDKit version, but typically returns None for purely acyclic
        # or a very simple chain. We just check it doesn't crash.
        # Note: RDKit MurckoScaffold often returns None for purely acyclic if no rings.
        # Let's verify behavior: if it returns a string, it's fine, if None, also fine.
        # The function returns None if no valid scaffold found.
        # For acyclic, it might return the chain or None.
        # We assert it doesn't raise an exception.
        pass

    def test_consistent_key_generation(self):
        """Test that the same reaction always generates the same key."""
        smiles = "Cc1ccccc1>>Brc1ccccc1"
        key1 = get_murcko_scaffold(smiles)
        key2 = get_murcko_scaffold(smiles)
        assert key1 == key2


class TestGenerateScaffoldGroups:
    """Tests for the generate_scaffold_groups function."""

    def test_generate_scaffold_groups_on_dataframe(self, tmp_path):
        """Test generating scaffold groups on a small in-memory DataFrame."""
        # Create a test DataFrame
        data = {
            "reaction_smiles": [
                "c1ccccc1>>c1ccccc1", # Benzene
                "Cc1ccccc1>>Brc1ccccc1", # Toluene to Bromobenzene
                "CCO>>CCO" # Ethanol (acyclic)
            ],
            "yield": [0.8, 0.9, 0.7]
        }
        df = pd.DataFrame(data)
        
        input_path = tmp_path / "test_cleaned.parquet"
        output_path = tmp_path / "test_scaffold.parquet"
        
        df.to_parquet(input_path)
        
        # Run the function
        result_df = generate_scaffold_groups(str(input_path), str(output_path))
        
        # Assertions
        assert "scaffold_key" in result_df.columns
        assert len(result_df) == 3
        assert result_df["scaffold_key"].notna().sum() >= 2 # At least the ring ones
        
        # Check that the output file was created
        assert output_path.exists()

    def test_missing_reaction_smiles_column(self, tmp_path):
        """Test that an error is raised if reaction_smiles is missing."""
        data = {"other_column": [1, 2, 3]}
        df = pd.DataFrame(data)
        
        input_path = tmp_path / "test_missing.parquet"
        output_path = tmp_path / "test_output.parquet"
        
        df.to_parquet(input_path)
        
        with pytest.raises(ValueError, match="does not contain 'reaction_smiles' column"):
            generate_scaffold_groups(str(input_path), str(output_path))