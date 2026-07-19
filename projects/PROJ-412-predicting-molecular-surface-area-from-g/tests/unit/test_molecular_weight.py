import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(project_root))

from data.add_molecular_weight import calculate_molecular_weight, add_molecular_weight_column

class TestCalculateMolecularWeight:
    def test_valid_smiles_ethane(self):
        """Test MW calculation for ethane (C2H6)."""
        smiles = "CC"
        mw = calculate_molecular_weight(smiles)
        # Ethane MW is approx 30.07
        assert 30.0 < mw < 30.1

    def test_valid_smiles_water(self):
        """Test MW calculation for water (H2O)."""
        smiles = "O"
        mw = calculate_molecular_weight(smiles)
        # Water MW is approx 18.015
        assert 18.0 < mw < 18.1

    def test_invalid_smiles(self):
        """Test that invalid SMILES raises ValueError."""
        with pytest.raises(ValueError):
            calculate_molecular_weight("invalid_smiles_string")

    def test_empty_smiles(self):
        """Test that empty SMILES raises ValueError."""
        with pytest.raises(ValueError):
            calculate_molecular_weight("")

class TestAddMolecularWeightColumn:
    def test_add_mw_column(self):
        """Test adding MW column to a DataFrame."""
        # Create a temporary input file
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.parquet"
            output_path = Path(tmpdir) / "output.parquet"
            
            # Create test data
            data = {
                'smiles': ['CC', 'CCC', 'O'],
                'node_features': [[1], [2], [3]],
                'edge_features': [[0], [1], [2]],
                'surface_area': [10.0, 20.0, 5.0]
            }
            df = pd.DataFrame(data)
            df.to_parquet(input_path)
            
            # Run the function
            add_molecular_weight_column(input_path, output_path)
            
            # Verify output
            assert output_path.exists()
            result_df = pd.read_parquet(output_path)
            
            assert 'molecular_weight' in result_df.columns
            assert len(result_df) == 3
            assert not result_df['molecular_weight'].isna().any()
            
            # Check specific values (approximate)
            assert 30.0 < result_df['molecular_weight'].iloc[0] < 30.1  # Ethane
            assert 44.0 < result_df['molecular_weight'].iloc[1] < 44.1  # Propane
            assert 18.0 < result_df['molecular_weight'].iloc[2] < 18.1  # Water

    def test_mw_column_with_invalid_smiles(self):
        """Test handling of invalid SMILES in DataFrame."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.parquet"
            output_path = Path(tmpdir) / "output.parquet"
            
            # Create test data with one invalid SMILES
            data = {
                'smiles': ['CC', 'invalid', 'CCC'],
                'node_features': [[1], [2], [3]],
                'edge_features': [[0], [1], [2]],
                'surface_area': [10.0, 20.0, 5.0]
            }
            df = pd.DataFrame(data)
            df.to_parquet(input_path)
            
            # Run the function
            add_molecular_weight_column(input_path, output_path)
            
            # Verify output
            result_df = pd.read_parquet(output_path)
            
            assert 'molecular_weight' in result_df.columns
            # One value should be NaN
            assert result_df['molecular_weight'].isna().sum() == 1
            assert not result_df['molecular_weight'].iloc[0] != result_df['molecular_weight'].iloc[0] # Check first is valid
            assert result_df['molecular_weight'].iloc[2] > 40.0 # Check third is valid
