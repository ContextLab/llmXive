import pytest
import pandas as pd
import tempfile
from pathlib import Path
import os

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.add_molecular_weight import calculate_molecular_weight, add_molecular_weight_column

class TestCalculateMolecularWeight:
    """Unit tests for molecular weight calculation."""

    def test_valid_smiles_ethane(self):
        """Test molecular weight calculation for ethane."""
        smiles = "CC"
        mw = calculate_molecular_weight(smiles)
        # Ethane (C2H6) MW = 2*12.01 + 6*1.008 ≈ 30.07
        assert mw is not None
        assert 29.0 < mw < 31.0

    def test_valid_smiles_benzene(self):
        """Test molecular weight calculation for benzene."""
        smiles = "c1ccccc1"
        mw = calculate_molecular_weight(smiles)
        # Benzene (C6H6) MW = 6*12.01 + 6*1.008 ≈ 78.11
        assert mw is not None
        assert 77.0 < mw < 79.0

    def test_invalid_smiles(self):
        """Test handling of invalid SMILES."""
        smiles = "invalid_smiles_string"
        mw = calculate_molecular_weight(smiles)
        assert mw is None

    def test_empty_smiles(self):
        """Test handling of empty SMILES."""
        smiles = ""
        mw = calculate_molecular_weight(smiles)
        assert mw is None

    def test_complex_molecule(self):
        """Test molecular weight for a more complex molecule (aspirin)."""
        smiles = "CC(=O)Oc1ccccc1C(=O)O"
        mw = calculate_molecular_weight(smiles)
        # Aspirin (C9H8O4) MW ≈ 180.16
        assert mw is not None
        assert 175.0 < mw < 185.0

class TestAddMolecularWeightColumn:
    """Integration tests for adding molecular weight column to parquet files."""

    def test_add_mw_to_dataframe(self):
        """Test adding molecular weight column to a valid parquet file."""
        # Create a temporary input file
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_path = tmpdir / "input.parquet"
            output_path = tmpdir / "output.parquet"

            # Create test data
            test_data = {
                'smiles': ['CC', 'c1ccccc1', 'CCO'],
                'node_features': [[1], [2], [1]],
                'edge_features': [[0], [1], [0]]
            }
            df = pd.DataFrame(test_data)
            df.to_parquet(input_path)

            # Run the function
            add_molecular_weight_column(input_path, output_path)

            # Verify output
            assert output_path.exists()
            result_df = pd.read_parquet(output_path)

            assert 'molecular_weight' in result_df.columns
            assert len(result_df) == 3
            assert result_df['molecular_weight'].iloc[0] is not None
            assert result_df['molecular_weight'].iloc[1] is not None
            assert result_df['molecular_weight'].iloc[2] is not None

    def test_missing_smiles_column(self):
        """Test that function raises error if SMILES column is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_path = tmpdir / "input.parquet"
            output_path = tmpdir / "output.parquet"

            # Create test data without smiles column
            test_data = {
                'other_col': [1, 2, 3]
            }
            df = pd.DataFrame(test_data)
            df.to_parquet(input_path)

            with pytest.raises(ValueError, match="must contain 'smiles' column"):
                add_molecular_weight_column(input_path, output_path)

    def test_file_not_found(self):
        """Test that function raises error if input file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_path = tmpdir / "nonexistent.parquet"
            output_path = tmpdir / "output.parquet"

            with pytest.raises(FileNotFoundError):
                add_molecular_weight_column(input_path, output_path)