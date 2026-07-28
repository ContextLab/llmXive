import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json

from code.data.add_molecular_weight import calculate_molecular_weight, add_molecular_weight_column

class TestCalculateMolecularWeight:
    def test_valid_smiles(self):
        """Test MW calculation for a valid SMILES string."""
        smiles = "CCO"  # Ethanol
        mw = calculate_molecular_weight(smiles)
        assert mw is not None
        assert isinstance(mw, float)
        # Ethanol MW is approximately 46.07 g/mol
        assert 45.0 < mw < 47.0

    def test_invalid_smiles(self):
        """Test MW calculation for invalid SMILES."""
        smiles = "INVALID_SMILES"
        mw = calculate_molecular_weight(smiles)
        assert mw is None

    def test_empty_smiles(self):
        """Test MW calculation for empty string."""
        mw = calculate_molecular_weight("")
        assert mw is None

    def test_complex_molecule(self):
        """Test MW calculation for a complex molecule."""
        smiles = "CC(=O)OC1=CC=CC=C1C(=O)O"  # Aspirin
        mw = calculate_molecular_weight(smiles)
        assert mw is not None
        # Aspirin MW is approximately 180.16 g/mol
        assert 179.0 < mw < 181.0

class TestAddMolecularWeightColumn:
    def test_add_mw_column(self):
        """Test adding molecular weight column to a dataframe."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.parquet"
            output_path = Path(tmpdir) / "output.parquet"
            
            # Create a test dataframe
            test_data = {
                'smiles': ['CCO', 'CC(=O)OC1=CC=CC=C1C(=O)O', 'C1=CC=CC=C1'],
                'node_features': [
                    {'charge': 0.0},
                    {'charge': 0.0},
                    {'charge': 0.0}
                ],
                'edge_features': [[], [], []]
            }
            df = pd.DataFrame(test_data)
            df.to_parquet(input_path)
            
            # Run the function
            stats = add_molecular_weight_column(input_path, output_path)
            
            # Verify output
            assert output_path.exists()
            output_df = pd.read_parquet(output_path)
            
            assert 'molecular_weight' in output_df.columns
            assert output_df['molecular_weight'].isna().sum() == 0
            assert stats['total_molecules'] == 3
            assert stats['mw_null_count'] == 0
            assert stats['success'] is True

    def test_missing_required_columns(self):
        """Test that missing required columns raise an error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.parquet"
            output_path = Path(tmpdir) / "output.parquet"
            
            # Create a dataframe without required columns
            test_data = {
                'smiles': ['CCO'],
                'other_col': ['value']
            }
            df = pd.DataFrame(test_data)
            df.to_parquet(input_path)
            
            with pytest.raises(ValueError, match="Missing required columns"):
                add_molecular_weight_column(input_path, output_path)

    def test_validation_log_creation(self):
        """Test that validation log is created with correct structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.parquet"
            output_path = Path(tmpdir) / "output.parquet"
            
            test_data = {
                'smiles': ['CCO'],
                'node_features': [{'charge': 0.0}],
                'edge_features': [[]]
            }
            df = pd.DataFrame(test_data)
            df.to_parquet(input_path)
            
            stats = add_molecular_weight_column(input_path, output_path)
            
            assert 'input_file' in stats
            assert 'output_file' in stats
            assert 'total_molecules' in stats
            assert 'mw_null_count' in stats
            assert 'charge_validation_passed' in stats
            assert 'success' in stats